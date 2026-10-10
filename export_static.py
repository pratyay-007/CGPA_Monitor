"""
Static Export Script for CGPA Monitor.

Reads cgpa_monitor.db using the same calculation logic as api_server.py/calculations.py
and writes static JSON files for the Next.js frontend.

Outputs:
  - web/public/data/leaderboard.json: meta + one entry per student
  - web/public/data/students/<registration_number>.json: full student detail
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# -----------------------------------------------------------------------------
# HIDDEN_REGS: Students in this list are excluded from ALL output files.
# Add registration numbers here for removal requests.
# -----------------------------------------------------------------------------
HIDDEN_REGS = [
    # Example: "2401289001",
]

# -----------------------------------------------------------------------------
# Grade points and pass logic (mirroring calculations.py / database.py)
# -----------------------------------------------------------------------------
GRADE_POINTS = {
    "O": 10, "E": 9, "A": 8, "B": 7, "C": 6,
    "D": 5, "F": 2, "M": 0, "S": 0
}

PASS_GRADES_THEORY = {"O", "E", "A", "B", "C", "D"}
PASS_GRADES_PRACTICAL = {"O", "E", "A", "B", "C"}


def compute_grade_points(grade):
    """Convert a grade letter to grade points. Handles suffixes like F(Ex), F(Int)."""
    g = grade.upper().strip()
    if "(" in g:
        g = g.split("(")[0].strip()
    return GRADE_POINTS.get(g, 0)


def is_pass(grade, subject_type):
    """Check if a grade is passing for the given subject type."""
    grade = grade.upper().strip()
    if "(" in grade:
        grade = grade.split("(")[0].strip()
    if subject_type and subject_type.upper().strip() in ("P", "S", "V"):
        return grade in PASS_GRADES_PRACTICAL
    return grade in PASS_GRADES_THEORY


def session_sort_key(session_str):
    """
    Return a tuple (year_start, parity) for chronological ordering.
    'Odd-(2024-25)'  -> (2024, 0)   # Odd comes first in an academic year
    'Even-(2024-25)' -> (2024, 1)
    'Odd-(2025-26)'  -> (2025, 0)
    Unknown format   -> (9999, 9)   # sort to end
    """
    import re
    m = re.search(r'(\d{4})-\d{2}', session_str)
    year = int(m.group(1)) if m else 9999
    parity = 0 if session_str.lower().startswith("odd") else 1
    return (year, parity)


# -----------------------------------------------------------------------------
# Database connection
# -----------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgpa_monitor.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def build_not_in_clause(hidden_regs):
    """Build the NOT IN (...) part of a SQL WHERE clause for the hidden regs."""
    if not hidden_regs:
        return None, ()
    params = ["?" for _ in hidden_regs]
    return f"NOT IN ({', '.join(params)})", tuple(hidden_regs)


def load_student_data_efficiently(conn):
    """
    Load all student data efficiently in bulk.
    Returns dict: reg_no -> student_data_dict
    """
    # Get all students (excluding hidden) who have results
    where_clause, params = build_not_in_clause(HIDDEN_REGS)
    if where_clause:
        students_query = f"""
            SELECT DISTINCT r.registration_number, s.name, s.branch, s.college_name, s.student_photo
            FROM results r
            JOIN students s ON s.registration_number = r.registration_number
            WHERE r.registration_number {where_clause}
        """
        students_rows = conn.execute(students_query, params).fetchall()
    else:
        students_rows = conn.execute("""
            SELECT DISTINCT r.registration_number, s.name, s.branch, s.college_name, s.student_photo
            FROM results r
            JOIN students s ON s.registration_number = r.registration_number
        """).fetchall()

    if not students_rows:
        return {}

    # Load all semesters data
    reg_numbers = [r[0] for r in students_rows]
    placeholders = ','.join('?' for _ in reg_numbers)

    semesters_data = conn.execute(f"""
        SELECT registration_number, semester_number, MIN(exam_session) as exam_session,
               semester_label, sgpa_bput, sgpa_calculated
        FROM results
        WHERE registration_number IN ({placeholders})
        GROUP BY registration_number, semester_number
        ORDER BY registration_number, semester_number
    """, reg_numbers).fetchall()

    # Load all subject attempts for these students
    subjects_data = conn.execute(f"""
        SELECT registration_number, semester_number, exam_session, subject_code, subject_name,
               subject_type, credits, grade, recheck, is_pass
        FROM subject_attempts
        WHERE registration_number IN ({placeholders})
        ORDER BY registration_number, semester_number, subject_code
    """, reg_numbers).fetchall()

    # Build lookup structures
    students_dict = {}
    for row in students_rows:
        reg_no = row[0]
        students_dict[reg_no] = {
            "info": {
                "registration_number": reg_no,
                "name": row[1],
                "branch": row[2],
                "college": row[3] or "Trident Academy of Technology, Bhubaneswar",
                "photo": row[4]
            },
            "semesters": {},
            "subjects": {},
            "semester_numbers": set()
        }

    # Index semesters data
    for row in semesters_data:
        reg_no, sem_num, exam_session, sem_label, sgpa_bput, sgpa_calc = row
        if reg_no in students_dict:
            students_dict[reg_no]["semesters"][sem_num] = {
                "exam_session": exam_session,
                "label": sem_label,
                "sgpa_bput": sgpa_bput,
                "sgpa_calculated": sgpa_calc
            }
            students_dict[reg_no]["semester_numbers"].add(sem_num)

    # Index subjects data: {sem_num: {exam_session: [attempts]}}
    for row in subjects_data:
        reg_no, sem_num, exam_session, subj_code, subj_name, subj_type, credits, grade, recheck, is_pass_val = row
        if reg_no in students_dict:
            if sem_num not in students_dict[reg_no]["subjects"]:
                students_dict[reg_no]["subjects"][sem_num] = {}
            if exam_session not in students_dict[reg_no]["subjects"][sem_num]:
                students_dict[reg_no]["subjects"][sem_num][exam_session] = []

            students_dict[reg_no]["subjects"][sem_num][exam_session].append({
                "subject_code": subj_code,
                "subject_name": subj_name,
                "subject_type": subj_type,
                "credits": float(credits) if credits else 0,
                "grade": grade,
                "recheck": recheck if recheck else 0,
                "is_pass": bool(is_pass_val)
            })

    return students_dict


def calculate_cgpa_for_student(student_data):
    """Calculate CGPA and per-semester SGPA from pre-loaded student data."""
    sem_data = student_data["semesters"]
    subjects = student_data["subjects"]  # {sem_num: {exam_session: [attempts]}}

    # -------------------------------------------------------------------
    # Pre-compute best grade per subject across ALL attempts for this student.
    # Tie-break: when grade points are equal, prefer the ORIGINAL (earliest)
    # session so is_backpaper is only True when a later attempt truly improved.
    # -------------------------------------------------------------------
    # Map: subject_code -> {"gp": float, "grade": str, "session": str}
    best_grade_map = {}

    for sem_num in subjects:
        for exam_session, attempts in subjects[sem_num].items():
            for attempt in attempts:
                code = attempt["subject_code"]
                gp = compute_grade_points(attempt["grade"])
                current = best_grade_map.get(code)
                if current is None:
                    best_grade_map[code] = {
                        "gp": gp,
                        "grade": attempt["grade"],
                        "session": exam_session
                    }
                else:
                    cur_key = session_sort_key(current["session"])
                    new_key = session_sort_key(exam_session)
                    if gp > current["gp"]:
                        # Strictly better — take this one
                        best_grade_map[code] = {
                            "gp": gp,
                            "grade": attempt["grade"],
                            "session": exam_session
                        }
                    elif gp == current["gp"] and new_key < cur_key:
                        # Same grade points but earlier session — prefer original
                        best_grade_map[code] = {
                            "gp": gp,
                            "grade": attempt["grade"],
                            "session": exam_session
                        }
                    # If same gp and later session: keep existing (original preferred)

    # -------------------------------------------------------------------
    # Build per-semester details using best-grade data
    # -------------------------------------------------------------------
    all_semesters_sorted = sorted(sem_data.keys())
    semester_details = []

    overall_total_ci = 0
    overall_total_credits = 0
    original_total_ci = 0
    original_total_credits = 0

    # Also build back_papers data indexed by subject_code
    # back_paper_data: code -> {subject_name, original_semester, attempts:[]}
    back_paper_data = {}

    # First pass: collect all attempts per subject across all sessions/semesters
    # to populate the back_papers section
    for sem_num in all_semesters_sorted:
        sem_info = sem_data[sem_num]
        original_session = sem_info["exam_session"]
        all_sessions_for_sem = subjects.get(sem_num, {})

        # Collect all known subject codes for this semester's original session
        orig_subjects_list = all_sessions_for_sem.get(original_session, [])

        for subj in orig_subjects_list:
            code = subj["subject_code"]
            # Gather all attempts for this subject across any session in any sem
            all_attempts_for_code = []
            for sn in subjects:
                for sess, attempts in subjects[sn].items():
                    for att in attempts:
                        if att["subject_code"] == code:
                            all_attempts_for_code.append((sess, att))

            if len(all_attempts_for_code) > 1:
                # Sort by session chronologically
                all_attempts_for_code.sort(key=lambda x: session_sort_key(x[0]))
                back_paper_data[code] = {
                    "subject_code": code,
                    "subject_name": subj["subject_name"],
                    "original_semester": sem_num,
                    "attempts": [
                        {
                            "session": sess,
                            "grade": att["grade"],
                            "grade_points": compute_grade_points(att["grade"]),
                            "is_pass": att["is_pass"]
                        }
                        for sess, att in all_attempts_for_code
                    ]
                }

    # Second pass: build per-semester calculation details
    for sem_num in all_semesters_sorted:
        sem_info = sem_data[sem_num]
        original_session = sem_info["exam_session"]

        # Get subject entries for the original session of this semester
        semester_subjects = subjects.get(sem_num, {}).get(original_session, [])

        details = []
        sem_total_ci = 0
        sem_total_credits = 0
        orig_sem_total_ci = 0
        orig_sem_total_credits = 0

        for subj in semester_subjects:
            code = subj["subject_code"]
            name = subj["subject_name"]
            stype = subj["subject_type"]
            credits = subj["credits"]
            orig_grade = subj["grade"]
            orig_gp = compute_grade_points(orig_grade)

            best = best_grade_map.get(code, {"gp": orig_gp, "grade": orig_grade, "session": original_session})
            best_gp = best["gp"]
            best_grade_letter = best["grade"]
            best_session = best["session"]

            # is_backpaper = True only when a later session truly improved the grade
            is_backpaper = best_session != original_session

            ci = credits * best_gp
            orig_ci = credits * orig_gp

            sem_total_ci += ci
            sem_total_credits += credits
            orig_sem_total_ci += orig_ci
            orig_sem_total_credits += credits

            details.append({
                "subject_code": code,
                "subject_name": name,
                "subject_type": stype,
                "credits": credits,
                "best_grade": best_grade_letter,       # <-- correct best grade letter
                "best_grade_points": best_gp,
                "credit_index": ci,
                "from_session": best_session,
                "is_backpaper": is_backpaper
            })

        sgpa = round(sem_total_ci / sem_total_credits, 2) if sem_total_credits > 0 else 0
        orig_sgpa = round(orig_sem_total_ci / orig_sem_total_credits, 2) if orig_sem_total_credits > 0 else 0

        semester_details.append({
            "semester": sem_num,
            "sgpa": sgpa,
            "original_sgpa": orig_sgpa,
            "credits": sem_total_credits,
            "credit_index": sem_total_ci,
            "subjects": details,
            "sgpa_bput": sem_info["sgpa_bput"],
            "sgpa_calculated": sem_info["sgpa_calculated"]
        })

        overall_total_ci += sem_total_ci
        overall_total_credits += sem_total_credits
        original_total_ci += orig_sem_total_ci
        original_total_credits += orig_sem_total_credits

    overall_cgpa = round(overall_total_ci / overall_total_credits, 2) if overall_total_credits > 0 else 0
    original_cgpa = round(original_total_ci / original_total_credits, 2) if original_total_credits > 0 else 0

    # Only include subjects in back_papers that actually have > 1 attempt
    back_papers = list(back_paper_data.values())

    return {
        "overall_cgpa": overall_cgpa,
        "original_cgpa": original_cgpa,
        "semester_details": semester_details,
        "all_semesters": all_semesters_sorted,
        "back_papers": back_papers
    }


def compute_ranks(student_results):
    """Compute overall and class ranks from student results."""
    sorted_students = sorted(student_results, key=lambda x: x[1]["overall_cgpa"], reverse=True)

    overall_rank_map = {}
    for rank, (reg_no, _) in enumerate(sorted_students, start=1):
        overall_rank_map[reg_no] = rank

    by_branch = {}
    for reg_no, result in student_results:
        branch = result["info"]["branch"]
        if branch not in by_branch:
            by_branch[branch] = []
        by_branch[branch].append((reg_no, result))

    class_rank_map = {}
    class_total_map = {}
    for branch, students in by_branch.items():
        sorted_by_cgpa = sorted(students, key=lambda x: x[1]["overall_cgpa"], reverse=True)
        class_total_map[branch] = len(sorted_by_cgpa)
        for rank, (reg_no, _) in enumerate(sorted_by_cgpa, start=1):
            if reg_no not in class_rank_map:
                class_rank_map[reg_no] = {}
            class_rank_map[reg_no][branch] = rank

    return overall_rank_map, class_rank_map, class_total_map


def main():
    print("Starting static export...")
    conn = get_connection()

    # Get available semesters (auto-detect, no hardcoding)
    all_sems_rows = conn.execute("""
        SELECT DISTINCT semester_number FROM results ORDER BY semester_number
    """).fetchall()
    available_semesters = [r[0] for r in all_sems_rows]
    print(f"Available semesters: {available_semesters}")

    # Get latest fetch date from scrape_sessions
    latest_fetch_row = conn.execute("""
        SELECT completed_at FROM scrape_sessions
        WHERE status = 'completed' AND completed_at IS NOT NULL
        ORDER BY completed_at DESC LIMIT 1
    """).fetchone()
    if latest_fetch_row and latest_fetch_row[0]:
        latest_fetch = latest_fetch_row[0]
    else:
        latest_fetch_row = conn.execute("""
            SELECT fetched_at FROM results ORDER BY fetched_at DESC LIMIT 1
        """).fetchone()
        if latest_fetch_row and latest_fetch_row[0]:
            latest_fetch = latest_fetch_row[0]
        else:
            latest_fetch = datetime.now().isoformat()

    print(f"Latest fetch date: {latest_fetch}")

    # Load all student data efficiently
    print("Loading student data...")
    students_dict = load_student_data_efficiently(conn)
    print(f"Loaded data for {len(students_dict)} students")

    # Calculate CGPA/SGPA for each student
    print("Calculating CGPA/SGPA...")
    student_results = {}  # reg_no -> result_dict
    for reg_no, data in students_dict.items():
        result = calculate_cgpa_for_student(data)
        result["info"] = data["info"]  # Add the student info back
        student_results[reg_no] = result

    # Compute ranks
    print("Computing ranks...")
    overall_rank_map, class_rank_map, class_total_map = compute_ranks([
        (reg_no, result) for reg_no, result in student_results.items()
    ])

    # Build leaderboard entries
    print("Building leaderboard...")
    leaderboard_entries = []
    branch_counts = {}

    for reg_no, result in student_results.items():
        info = result["info"]
        branch = info["branch"]
        course = "biotech" if "BIO" in branch.upper() or "BIOTECH" in branch.upper() else "btech"

        branch_counts[branch] = branch_counts.get(branch, 0) + 1

        entry = {
            "registration_number": reg_no,
            "name": info["name"],
            "branch": branch,
            "course": course,
            "cgpa": result["overall_cgpa"],
            "original_cgpa": result["original_cgpa"],
            "rank": overall_rank_map.get(reg_no, 0),
        }

        # Add SGPA for each available semester
        for sem in available_semesters:
            sem_detail = next((sd for sd in result["semester_details"] if sd["semester"] == sem), None)
            if sem_detail:
                entry[f"sgpa_sem{sem}"] = sem_detail["sgpa"]
            else:
                entry[f"sgpa_sem{sem}"] = None

        leaderboard_entries.append(entry)

    # Sort by CGPA descending, then by name for tie-breaking (mirrors api_server.py)
    leaderboard_entries.sort(key=lambda x: (-x["cgpa"], x["name"]))

    # Re-assign rank after sort (ties share rank)
    prev_cgpa = None
    prev_rank = 0
    for i, entry in enumerate(leaderboard_entries):
        if entry["cgpa"] != prev_cgpa:
            prev_rank = i + 1
            prev_cgpa = entry["cgpa"]
        entry["rank"] = prev_rank

    # Build branches list (sorted by count desc)
    branches_list = sorted(
        [{"name": b, "count": c} for b, c in branch_counts.items()],
        key=lambda x: -x["count"]
    )

    # Create meta object
    meta = {
        "semesters": available_semesters,
        "branches": branches_list,
        "data_fetched": latest_fetch,
        "total_students": len(leaderboard_entries),
        "generated_at": datetime.now().isoformat()
    }

    # Write leaderboard.json
    output_dir = Path("web/public/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    leaderboard_data = {
        "meta": meta,
        "students": leaderboard_entries
    }

    leaderboard_path = output_dir / "leaderboard.json"
    with open(leaderboard_path, "w", encoding="utf-8") as f:
        json.dump(leaderboard_data, f, ensure_ascii=False, indent=2)

    print(f"Written leaderboard.json ({leaderboard_path.stat().st_size / 1024:.1f} KB)")

    # Write individual student files
    print("Writing student detail files...")
    students_dir = output_dir / "students"
    students_dir.mkdir(parents=True, exist_ok=True)

    for reg_no, result in student_results.items():
        info = result["info"]
        branch = info["branch"]

        overall_rank = overall_rank_map.get(reg_no)
        class_rank = class_rank_map.get(reg_no, {}).get(branch)
        class_total = class_total_map.get(branch)

        detail = {
            "registration_number": reg_no,
            "name": info["name"],
            "branch": branch,
            "college": info["college"],
            "photo_url": f"https://results.bput.ac.in/{info['photo']}" if info['photo'] else "",
            "cgpa": result["overall_cgpa"],
            "original_cgpa": result["original_cgpa"],
            "total_credits": sum(sd["credits"] for sd in result["semester_details"]),
            "overall_rank": overall_rank,
            "total_students": len(student_results),
            "class_rank": class_rank,
            "class_total": class_total,
            "semesters": result["semester_details"],
            "back_papers": result["back_papers"],
            "source": "BPUT (Biju Patnaik University of Technology)",
            "disclaimer": "Results are provisional and sourced from BPUT. This is an unofficial aggregation.",
            "fetched_on": latest_fetch
        }

        student_path = students_dir / f"{reg_no}.json"
        with open(student_path, "w", encoding="utf-8") as f:
            json.dump(detail, f, ensure_ascii=False, indent=2)

    print(f"Written {len(student_results)} student detail files to {students_dir}")

    conn.close()
    print("Export complete!")


if __name__ == "__main__":
    main()