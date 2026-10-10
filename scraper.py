"""
BPUT Result Scraper for CGPA Monitor.

Politely scrapes results from results.bput.ac.in:
- 1 request at a time
- 1-2.5 second delay between requests
- Retries with exponential backoff
- Saves raw responses for re-parsing
- Stores structured data in SQLite
"""

import requests
import json
import time
import random
import sqlite3
import os
import sys
from datetime import datetime
from database import (
    get_connection, init_db, load_students_from_json,
    compute_grade_points, is_pass, compute_sgpa, GRADE_POINTS
)

BASE_URL = "https://results.bput.ac.in"
DOB = "2000-01-01"  # Any DOB works

# Session mapping: semester number -> BPUT session string
SESSION_MAP = {
    1: "Odd-(2024-25)",
    2: "Even-(2024-25)",
    3: "Odd-(2025-26)",
    4: "Even-(2025-26)",
}

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://results.bput.ac.in/",
    "Origin": "https://results.bput.ac.in",
    "Accept": "application/json, text/plain, */*",
}

MAX_RETRIES = 3
BASE_DELAY = 1.0   # Minimum delay between requests (seconds)
MAX_DELAY = 2.5    # Maximum delay between requests (seconds)


def polite_delay():
    """Sleep for a random duration between BASE_DELAY and MAX_DELAY seconds."""
    delay = random.uniform(BASE_DELAY, MAX_DELAY)
    time.sleep(delay)


def make_request(url, retries=MAX_RETRIES):
    """Make a POST request with retry logic and exponential backoff."""
    for attempt in range(retries):
        try:
            resp = requests.post(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 400:
                # Client error - no result found, don't retry
                return resp
            elif resp.status_code == 404:
                return resp
            elif resp.status_code >= 500:
                # Server error - retry with backoff
                wait = (2 ** attempt) * 2 + random.uniform(0, 1)
                print(f"    Server error {resp.status_code}, retrying in {wait:.1f}s...")
                time.sleep(wait)
            else:
                print(f"    Unexpected status {resp.status_code}")
                return resp
        except requests.exceptions.Timeout:
            wait = (2 ** attempt) * 2 + random.uniform(0, 1)
            print(f"    Timeout, retrying in {wait:.1f}s...")
            time.sleep(wait)
        except requests.exceptions.ConnectionError as e:
            wait = (2 ** attempt) * 3 + random.uniform(0, 2)
            print(f"    Connection error, retrying in {wait:.1f}s...")
            time.sleep(wait)
        except Exception as e:
            print(f"    Unexpected error: {e}")
            return None
    
    print(f"    Failed after {retries} retries")
    return None


def save_raw_response(conn, reg_no, session, semester, endpoint, response_text, status_code):
    """Save raw API response to the database."""
    conn.execute("""
        INSERT INTO raw_responses (registration_number, exam_session, semester_number, 
                                   endpoint, response_json, http_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (reg_no, session, semester, endpoint, response_text, status_code))


def scrape_student_details(reg_no, conn):
    """Fetch and store student details (name, branch, college, photo)."""
    url = f"{BASE_URL}/student-detsils-results?rollNo={reg_no}"
    resp = make_request(url)
    
    if resp and resp.status_code == 200:
        try:
            data = resp.json()
            save_raw_response(conn, reg_no, "", 0, "student-detsils-results", resp.text, resp.status_code)
            
            if data:
                conn.execute("""
                    UPDATE students 
                    SET college_name = ?, student_photo = ?, updated_at = datetime('now')
                    WHERE registration_number = ?
                """, (data.get("collegeName", ""), data.get("studentPhoto", ""), reg_no))
                return data
        except Exception as e:
            print(f"    Error parsing student details: {e}")
    
    return None


def scrape_results_list(reg_no, session, conn, semester):
    """Fetch the list of published results for a student in a session."""
    url = f"{BASE_URL}/student-results-list?rollNo={reg_no}&dob={DOB}&session={session}"
    resp = make_request(url)
    
    if resp and resp.status_code == 200:
        try:
            data = resp.json()
            save_raw_response(conn, reg_no, session, semester, "student-results-list", resp.text, resp.status_code)
            return data
        except Exception as e:
            print(f"    Error parsing results list: {e}")
            save_raw_response(conn, reg_no, session, semester, "student-results-list", resp.text, resp.status_code)
    elif resp:
        save_raw_response(conn, reg_no, session, semester, "student-results-list", resp.text, resp.status_code)
    
    return None


def scrape_subjects(reg_no, sem_id, session, conn, semester):
    """Fetch subject grades and SGPA for a specific semester."""
    url = f"{BASE_URL}/student-results-subjects-list?semid={sem_id}&rollNo={reg_no}&session={session}"
    resp = make_request(url)
    
    if resp and resp.status_code == 200:
        try:
            data = resp.json()
            save_raw_response(conn, reg_no, session, semester, "student-results-subjects-list", resp.text, resp.status_code)
            return data
        except Exception as e:
            print(f"    Error parsing subjects: {e}")
            save_raw_response(conn, reg_no, session, semester, "student-results-subjects-list", resp.text, resp.status_code)
    elif resp:
        save_raw_response(conn, reg_no, session, semester, "student-results-subjects-list", resp.text, resp.status_code)
    
    return None


def parse_semester_number_from_label(label):
    """Extract the actual semester number from BPUT's semester label like '1st', '2nd', '3rd', '4th', etc."""
    if not label:
        return None
    label = str(label).strip().lower()
    # Handle formats like "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"
    for i in range(1, 9):
        suffixes = {1: "st", 2: "nd", 3: "rd"}
        suffix = suffixes.get(i, "th")
        if label.startswith(f"{i}{suffix}") or label.startswith(f"{i} ") or label == str(i):
            return i
    # Try to find any digit
    import re
    match = re.search(r'(\d+)', label)
    if match:
        return int(match.group(1))
    return None


def process_student_semester(reg_no, semester, session, conn):
    """
    Process one student for one session:
    1. Get results list (may contain multiple entries: regular + back papers)
    2. For EACH result entry, get subject grades
    3. Determine actual semester from BPUT's label
    4. Store subjects under the CORRECT semester number
    5. Store result summary for the primary semester
    
    Returns: 'success', 'no_result', or 'failed'
    """
    # Step 1: Get results list
    results = scrape_results_list(reg_no, session, conn, semester)
    polite_delay()
    
    if not results or (isinstance(results, list) and len(results) == 0):
        return "no_result"
    
    if isinstance(results, str):
        return "no_result"
    
    if not isinstance(results, list):
        return "no_result"
    
    any_success = False
    
    # Process ALL result entries (regular semester + back papers)
    for result_entry in results:
        sem_id = result_entry.get("semId")
        semester_label = result_entry.get("semester")
        branch_name = result_entry.get("branchName")
        
        if not sem_id:
            continue
        
        # Determine the ACTUAL semester number from BPUT's label
        actual_semester = parse_semester_number_from_label(semester_label)
        if actual_semester is None:
            actual_semester = semester  # Fallback to the session's semester
        
        # Step 2: Get subjects and grades for this result entry
        subjects_data = scrape_subjects(reg_no, sem_id, session, conn, actual_semester)
        polite_delay()
        
        if not subjects_data or not isinstance(subjects_data, dict):
            continue
        
        grades = subjects_data.get("grades", [])
        sgpa_details = subjects_data.get("sgpadetails", {})
        
        if not grades:
            continue
        
        # Extract BPUT's SGPA
        bput_sgpa = sgpa_details.get("sgpa", "")
        bput_credits = sgpa_details.get("cretits", "")
        
        # Step 3: Store subject attempts with the CORRECT semester number
        for g in grades:
            grade = g.get("grade", "")
            subject_type = g.get("subjectTP", "")
            credits = g.get("subjectCredits", 0)
            gp = compute_grade_points(grade) if grade and grade != "P" else 0
            passed = is_pass(grade, subject_type) if grade and grade != "P" else False
            credit_idx = credits * gp if grade != "P" else 0
            
            conn.execute("""
                INSERT INTO subject_attempts 
                (registration_number, exam_session, semester_number, subject_code, 
                 subject_name, subject_type, credits, grade, recheck, is_pass, 
                 grade_points, credit_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reg_no, session, actual_semester,
                g.get("subjectCODE", ""),
                g.get("subjectName", ""),
                subject_type,
                credits,
                grade,
                g.get("recheck", 0),
                1 if passed else 0,
                gp,
                credit_idx
            ))
        
        # Step 4: Calculate our own SGPA for this result entry
        valid_subjects = [
            {"credits": g["subjectCredits"], "grade": g["grade"]}
            for g in grades if g.get("grade") and g["grade"] != "P"
        ]
        calc_sgpa, calc_credits, calc_ci = compute_sgpa(valid_subjects)
        
        # Step 5: Store result summary (only for the primary semester, not back papers)
        # For back paper results, we still store them so we have a record
        conn.execute("""
            INSERT OR REPLACE INTO results 
            (registration_number, exam_session, semester_number, semester_label,
             branch_name, sgpa_bput, total_credits_bput, sgpa_calculated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reg_no, session, actual_semester, semester_label,
            branch_name, str(bput_sgpa), str(bput_credits), calc_sgpa
        ))
        
        # Step 6: Validate SGPA
        is_backpaper = (actual_semester != semester)
        bp_marker = " [BACK PAPER]" if is_backpaper else ""
        try:
            bput_sgpa_float = float(bput_sgpa) if bput_sgpa else 0
            diff = abs(calc_sgpa - bput_sgpa_float)
            if diff > 0.02:
                print(f"    ⚠ Sem {actual_semester} SGPA mismatch! BPUT={bput_sgpa}, Calc={calc_sgpa:.2f}{bp_marker}")
            else:
                print(f"    ✓ Sem {actual_semester} SGPA: BPUT={bput_sgpa}, Calc={calc_sgpa:.2f}{bp_marker}")
        except (ValueError, TypeError):
            print(f"    ? Sem {actual_semester} SGPA: BPUT={bput_sgpa}, Calc={calc_sgpa:.2f}{bp_marker}")
        
        any_success = True
    
    return "success" if any_success else "no_result"


def scrape_semester(semester_number, resume_from=None):
    """
    Scrape all students for a given semester.
    
    Args:
        semester_number: 1-4
        resume_from: If set, skip students until this registration number is found
    """
    session = SESSION_MAP.get(semester_number)
    if not session:
        print(f"Unknown semester number: {semester_number}")
        return
    
    print(f"\n{'='*60}")
    print(f"SCRAPING SEMESTER {semester_number} ({session})")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Initialize database
    init_db()
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.json")
    load_students_from_json(json_path)
    
    conn = get_connection()
    
    # Get all students
    students = conn.execute(
        "SELECT registration_number, name FROM students ORDER BY registration_number"
    ).fetchall()
    
    total = len(students)
    print(f"Total students to scrape: {total}\n")
    
    # Create scrape session record
    conn.execute("""
        INSERT INTO scrape_sessions (exam_session, semester_number, started_at, total_students, status)
        VALUES (?, ?, datetime('now'), ?, 'running')
    """, (session, semester_number, total))
    scrape_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    
    # Check which students already have results for this semester
    existing = set()
    rows = conn.execute(
        "SELECT registration_number FROM results WHERE exam_session = ? AND semester_number = ?",
        (session, semester_number)
    ).fetchall()
    for r in rows:
        existing.add(r[0])
    
    if existing:
        print(f"Skipping {len(existing)} students already scraped\n")
    
    successful = 0
    failed = 0
    no_result = 0
    skipping = resume_from is not None
    
    # First, scrape student details (once per student, not per semester)
    for i, student in enumerate(students):
        reg_no = student[0]
        name = student[1]
        
        if skipping:
            if reg_no == resume_from:
                skipping = False
            else:
                continue
        
        if reg_no in existing:
            continue
        
        progress = f"[{i+1}/{total}]"
        print(f"{progress} {reg_no} - {name}")
        
        try:
            # Fetch student details if we don't have them yet
            has_details = conn.execute(
                "SELECT college_name FROM students WHERE registration_number = ? AND college_name IS NOT NULL",
                (reg_no,)
            ).fetchone()
            
            if not has_details:
                scrape_student_details(reg_no, conn)
                polite_delay()
            
            # Process semester
            result = process_student_semester(reg_no, semester_number, session, conn)
            
            if result == "success":
                successful += 1
            elif result == "no_result":
                no_result += 1
                print(f"    - No result found")
            else:
                failed += 1
                print(f"    ✗ Failed")
            
            # Commit after each student
            conn.commit()
            
            # Progress update every 25 students
            if (i + 1) % 25 == 0:
                elapsed = datetime.now().strftime('%H:%M:%S')
                print(f"\n--- Progress: {successful} success, {no_result} no result, {failed} failed ({elapsed}) ---\n")
            
        except KeyboardInterrupt:
            print(f"\n\nInterrupted! Saving progress...")
            conn.commit()
            break
        except Exception as e:
            print(f"    ✗ Error: {e}")
            failed += 1
            conn.commit()
    
    # Update scrape session
    conn.execute("""
        UPDATE scrape_sessions 
        SET completed_at = datetime('now'), successful = ?, failed = ?, no_result = ?, status = 'completed'
        WHERE id = ?
    """, (successful, failed, no_result, scrape_id))
    conn.commit()
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"Successful: {successful}")
    print(f"No result: {no_result}")
    print(f"Failed: {failed}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    conn.close()


def scrape_all_semesters():
    """Scrape all available semesters in order."""
    for sem in [1, 2, 3, 4]:
        try:
            scrape_semester(sem)
        except Exception as e:
            print(f"Error scraping semester {sem}: {e}")
            continue


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sem = int(sys.argv[1])
        resume = sys.argv[2] if len(sys.argv) > 2 else None
        scrape_semester(sem, resume_from=resume)
    else:
        # Default: scrape semester 1
        scrape_semester(1)
