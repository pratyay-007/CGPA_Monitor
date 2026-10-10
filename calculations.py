"""
CGPA/SGPA Calculation Engine with Back-Paper Merge Logic.

Handles:
- SGPA calculation per semester
- CGPA calculation across all semesters
- Back paper handling: when a student passes a back paper,
  the updated grade is used in the ORIGINAL semester's SGPA calculation
- Two views: "Official SGPA (BPUT)" vs "Updated SGPA (after back papers)"
"""

import sqlite3
import os
from database import get_connection, compute_grade_points, GRADE_POINTS


def get_student_semesters(conn, reg_no):
    """Get all semesters a student has results for."""
    # Group by semester_number and take the earliest exam_session (which is the original attempt)
    rows = conn.execute("""
        SELECT semester_number, MIN(exam_session) as exam_session, 
               semester_label, sgpa_bput, sgpa_calculated
        FROM results 
        WHERE registration_number = ?
        GROUP BY semester_number
        ORDER BY semester_number
    """, (reg_no,)).fetchall()
    return rows


def get_semester_subjects(conn, reg_no, semester_number, exam_session):
    """Get all subjects for a student in a specific semester and session."""
    rows = conn.execute("""
        SELECT subject_code, subject_name, subject_type, credits, grade, 
               grade_points, credit_index, recheck, is_pass
        FROM subject_attempts 
        WHERE registration_number = ? AND semester_number = ? AND exam_session = ?
        ORDER BY subject_code
    """, (reg_no, semester_number, exam_session)).fetchall()
    return rows


def get_all_attempts_for_subject(conn, reg_no, subject_code):
    """Get all attempts (including back papers) for a specific subject."""
    rows = conn.execute("""
        SELECT exam_session, semester_number, grade, grade_points, credits, 
               credit_index, is_pass, recheck
        FROM subject_attempts 
        WHERE registration_number = ? AND subject_code = ?
        ORDER BY exam_session
    """, (reg_no, subject_code)).fetchall()
    return rows


def get_best_grade_for_subject(conn, reg_no, subject_code):
    """
    Get the best passing grade for a subject across all attempts.
    If no passing grade, return the most recent attempt.
    """
    # First try to find the best passing grade
    best_pass = conn.execute("""
        SELECT grade, grade_points, credits, exam_session
        FROM subject_attempts 
        WHERE registration_number = ? AND subject_code = ? AND is_pass = 1
        ORDER BY grade_points DESC
        LIMIT 1
    """, (reg_no, subject_code)).fetchone()
    
    if best_pass:
        return dict(best_pass)
    
    # If no passing grade, return the most recent attempt
    latest = conn.execute("""
        SELECT grade, grade_points, credits, exam_session
        FROM subject_attempts 
        WHERE registration_number = ? AND subject_code = ?
        ORDER BY exam_session DESC
        LIMIT 1
    """, (reg_no, subject_code)).fetchone()
    
    return dict(latest) if latest else None


def calculate_updated_sgpa(conn, reg_no, semester_number):
    """
    Calculate the "Updated SGPA" for a semester, using the best grade
    across all attempts (including back papers from later sessions).
    
    Returns: (updated_sgpa, details_list)
    """
    # Get the original exam session for this semester
    result = conn.execute("""
        SELECT exam_session FROM results 
        WHERE registration_number = ? AND semester_number = ?
        LIMIT 1
    """, (reg_no, semester_number)).fetchone()
    
    if not result:
        return None, []
    
    original_session = result[0]
    
    # Get all subjects from the original semester, EXCLUDING back papers
    # (subjects that also appear in an earlier semester for this student)
    original_subjects = conn.execute("""
        SELECT DISTINCT subject_code, subject_name, subject_type, credits
        FROM subject_attempts 
        WHERE registration_number = ? AND semester_number = ? AND exam_session = ?
        AND subject_code NOT IN (
            SELECT subject_code FROM subject_attempts
            WHERE registration_number = ? AND semester_number < ?
        )
    """, (reg_no, semester_number, original_session, reg_no, semester_number)).fetchall()
    
    details = []
    total_credits = 0
    total_ci = 0
    
    for subj in original_subjects:
        code = subj[0]
        name = subj[1]
        stype = subj[2]
        credits = float(subj[3])
        
        # Get best grade across all attempts
        best = get_best_grade_for_subject(conn, reg_no, code)
        
        if best:
            gp = float(best["grade_points"])
            ci = credits * gp
            total_credits += credits
            total_ci += ci
            
            details.append({
                "subject_code": code,
                "subject_name": name,
                "subject_type": stype,
                "credits": credits,
                "best_grade": best["grade"],
                "best_grade_points": gp,
                "credit_index": ci,
                "from_session": best["exam_session"],
                "is_backpaper": best["exam_session"] != original_session
            })
        else:
            total_credits += credits
            details.append({
                "subject_code": code,
                "subject_name": name,
                "subject_type": stype,
                "credits": credits,
                "best_grade": "?",
                "best_grade_points": 0,
                "credit_index": 0,
                "from_session": "",
                "is_backpaper": False
            })
    
    updated_sgpa = round(total_ci / total_credits, 2) if total_credits > 0 else 0
    return updated_sgpa, details


def calculate_cgpa(conn, reg_no, use_best_grades=True):
    """
    Calculate CGPA across all semesters.
    
    Args:
        use_best_grades: If True, use updated grades (after back papers).
                         If False, use original grades only.
    
    Returns: (cgpa, total_credits, total_ci, semester_details)
    """
    semesters = get_student_semesters(conn, reg_no)
    
    if not semesters:
        return 0, 0, 0, []
    
    total_credits = 0
    total_ci = 0
    semester_details = []
    
    for sem in semesters:
        sem_num = sem[0]
        
        if use_best_grades:
            sgpa, details = calculate_updated_sgpa(conn, reg_no, sem_num)
            sem_credits = sum(d["credits"] for d in details)
            sem_ci = sum(d["credit_index"] for d in details)
        else:
            # Use original grades
            subjects = get_semester_subjects(conn, reg_no, sem_num, sem[1])
            sem_credits = 0
            sem_ci = 0
            details = []
            for s in subjects:
                c = float(s[3])
                gp = float(s[5]) if s[5] else 0
                sem_credits += c
                sem_ci += c * gp
                details.append({
                    "subject_code": s[0],
                    "subject_name": s[1],
                    "credits": c,
                    "grade": s[4],
                    "grade_points": gp
                })
            sgpa = round(sem_ci / sem_credits, 2) if sem_credits > 0 else 0
        
        total_credits += sem_credits
        total_ci += sem_ci
        
        semester_details.append({
            "semester": sem_num,
            "sgpa": sgpa,
            "credits": sem_credits,
            "credit_index": sem_ci,
            "subjects": details
        })
    
    cgpa = round(total_ci / total_credits, 2) if total_credits > 0 else 0
    return cgpa, total_credits, total_ci, semester_details


def get_leaderboard(conn, branch_filter=None, course_filter=None, semester_filter=None):
    """
    Generate a leaderboard of students ranked by CGPA (or SGPA for a specific semester).
    
    Args:
        branch_filter: Filter by branch name (e.g., "COMPUTER SCIENCE")
        course_filter: Filter by course (e.g., "B.Tech" vs "Biotech")
        semester_filter: If set, rank by SGPA for that semester instead of CGPA
    """
    # Get all students with results
    query = "SELECT DISTINCT registration_number FROM results"
    params = []
    
    students_data = conn.execute(query).fetchall()
    
    leaderboard = []
    
    for row in students_data:
        reg_no = row[0]
        
        # Get student info
        student = conn.execute(
            "SELECT name, branch FROM students WHERE registration_number = ?",
            (reg_no,)
        ).fetchone()
        
        if not student:
            continue
        
        name = student[0]
        branch = student[1]
        
        # Apply filters
        if branch_filter and branch_filter.upper() not in branch.upper():
            continue
        if course_filter:
            if course_filter.upper() == "BIOTECH" and "BIO" not in branch.upper():
                continue
            elif course_filter.upper() == "BTECH" and "BIO" in branch.upper():
                continue
        
        if semester_filter:
            # Use updated SGPA for the specific semester
            sgpa, _ = calculate_updated_sgpa(conn, reg_no, semester_filter)
            if sgpa is None:
                continue
            leaderboard.append({
                "registration_number": reg_no,
                "name": name,
                "branch": branch,
                "sgpa": sgpa,
                "sort_value": sgpa
            })
        else:
            # Calculate CGPA
            cgpa, credits, ci, _ = calculate_cgpa(conn, reg_no, use_best_grades=True)
            if cgpa == 0:
                continue
            leaderboard.append({
                "registration_number": reg_no,
                "name": name,
                "branch": branch,
                "cgpa": cgpa,
                "sort_value": cgpa
            })
    
    # Sort by CGPA/SGPA descending
    leaderboard.sort(key=lambda x: x["sort_value"], reverse=True)
    
    # Add rank
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    
    return leaderboard


def print_student_report(reg_no):
    """Print a detailed report for a student."""
    conn = get_connection()
    
    student = conn.execute(
        "SELECT name, branch, college_name FROM students WHERE registration_number = ?",
        (reg_no,)
    ).fetchone()
    
    if not student:
        print(f"Student {reg_no} not found")
        return
    
    print(f"\n{'='*60}")
    print(f"Student: {student[0]}")
    print(f"Reg No:  {reg_no}")
    print(f"Branch:  {student[1]}")
    print(f"College: {student[2] or 'N/A'}")
    print(f"{'='*60}")
    
    cgpa, total_credits, total_ci, semesters = calculate_cgpa(conn, reg_no, use_best_grades=True)
    
    for sem in semesters:
        print(f"\n  Semester {sem['semester']} (SGPA: {sem['sgpa']})")
        print(f"  {'-'*50}")
        for subj in sem['subjects']:
            bp_marker = " [BACK PAPER CLEARED]" if subj.get("is_backpaper") else ""
            print(f"    {subj['subject_code']}  {subj.get('subject_name', subj.get('subject_code')):<40s}  "
                  f"{subj.get('best_grade', subj.get('grade')):<3s}  "
                  f"({subj['credits']} cr){bp_marker}")
    
    print(f"\n  {'-'*50}")
    print(f"  CGPA: {cgpa} ({total_credits} total credits)")
    
    # Also show original SGPA comparison
    original_cgpa, _, _, _ = calculate_cgpa(conn, reg_no, use_best_grades=False)
    if original_cgpa != cgpa:
        print(f"  Original CGPA (without back paper improvement): {original_cgpa}")
    
    conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print_student_report(sys.argv[1])
    else:
        # Demo: show report for sample students
        for reg in ["2401289308", "2401289285"]:
            print_student_report(reg)
