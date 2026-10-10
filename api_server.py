"""
Flask API Server for CGPA Monitor.

Serves SQLite data to the Next.js frontend.
Endpoints:
  GET /api/leaderboard        - Leaderboard with optional filters
  GET /api/student/<reg_no>   - Detailed student view
  GET /api/search?q=          - Search by name or registration number
  GET /api/stats              - Overall statistics
  GET /api/branches           - List of all branches
"""

import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_connection, DB_PATH
from calculations import (
    calculate_cgpa, calculate_updated_sgpa, get_student_semesters,
    get_semester_subjects, get_all_attempts_for_subject, get_leaderboard
)

app = Flask(__name__)
CORS(app)  # Allow Next.js frontend to call this API

# ---------------------------------------------------------------------------
# In-memory leaderboard cache.
#
# get_leaderboard() is expensive: it re-runs CGPA/SGPA math for every one of
# the 435 students on every request. The underlying SQLite data is static
# (scraped once per semester), so we cache the computed leaderboard and only
# rebuild when the database file's modification time changes.
# ---------------------------------------------------------------------------
_leaderboard_cache = {}  # key -> {"data": [...], "total": int, "ts": float}


def _db_mtime():
    try:
        return os.path.getmtime(DB_PATH)
    except OSError:
        return 0.0


def _get_cached_leaderboard(branch_filter, course_filter, semester_filter):
    key = (branch_filter, course_filter, semester_filter)
    cached = _leaderboard_cache.get(key)
    if cached and cached["ts"] == _db_mtime():
        return cached["data"], cached["total"]
    return None, None


def _set_cached_leaderboard(branch_filter, course_filter, semester_filter, data, total):
    _leaderboard_cache[(branch_filter, course_filter, semester_filter)] = {
        "data": data,
        "total": total,
        "ts": _db_mtime(),
    }


@app.route("/api/stats")
def stats():
    """Overall statistics."""
    conn = get_connection()
    
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    students_with_results = conn.execute(
        "SELECT COUNT(DISTINCT registration_number) FROM results"
    ).fetchone()[0]
    total_semesters = conn.execute(
        "SELECT COUNT(DISTINCT semester_number) FROM results"
    ).fetchone()[0]
    
    # Branch distribution
    branches = conn.execute("""
        SELECT branch, COUNT(*) as count 
        FROM students 
        GROUP BY branch 
        ORDER BY count DESC
    """).fetchall()
    
    # Scrape sessions info
    scrapes = conn.execute("""
        SELECT exam_session, semester_number, successful, no_result, failed, 
               started_at, completed_at, status
        FROM scrape_sessions 
        ORDER BY started_at DESC
    """).fetchall()
    
    conn.close()
    
    return jsonify({
        "total_students": total_students,
        "students_with_results": students_with_results,
        "total_semesters_scraped": total_semesters,
        "branches": [{"name": b[0], "count": b[1]} for b in branches],
        "scrape_sessions": [
            {
                "session": s[0], "semester": s[1],
                "successful": s[2], "no_result": s[3], "failed": s[4],
                "started_at": s[5], "completed_at": s[6], "status": s[7]
            } for s in scrapes
        ]
    })


@app.route("/api/branches")
def branches():
    """List all available branches."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT DISTINCT branch, COUNT(*) as count 
        FROM students 
        GROUP BY branch 
        ORDER BY branch
    """).fetchall()
    conn.close()
    
    return jsonify([{"name": r[0], "count": r[1]} for r in rows])


@app.route("/api/leaderboard")
def leaderboard():
    """
    Get the leaderboard.
    Query params:
      - branch: filter by branch (substring match)
      - course: "btech" or "biotech"
      - semester: specific semester number (shows SGPA instead of CGPA)
      - page: page number (default 1)
      - per_page: results per page (default 50)
    """
    branch_filter = request.args.get("branch")
    course_filter = request.args.get("course")
    semester_filter = request.args.get("semester", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # Use cached leaderboard when possible (data is static between scrapes)
    lb, total = _get_cached_leaderboard(branch_filter, course_filter, semester_filter)
    if lb is None:
        conn = get_connection()
        t0 = time.time()
        lb = get_leaderboard(conn, branch_filter, course_filter, semester_filter)
        conn.close()
        total = len(lb)
        _set_cached_leaderboard(branch_filter, course_filter, semester_filter, lb, total)
        print(f"[leaderboard] computed fresh in {time.time()-t0:.2f}s ({total} rows)")

    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    page_data = lb[start:end]

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "data": page_data
    })


@app.route("/api/student/<reg_no>")
def student_detail(reg_no):
    """Get detailed student information with all semesters."""
    conn = get_connection()
    
    # Student info
    student = conn.execute(
        "SELECT name, branch, college_name, student_photo FROM students WHERE registration_number = ?",
        (reg_no,)
    ).fetchone()
    
    if not student:
        conn.close()
        return jsonify({"error": "Student not found"}), 404
    
    # Calculate CGPA with best grades
    cgpa, total_credits, total_ci, semesters = calculate_cgpa(conn, reg_no, use_best_grades=True)
    
    # Also get original CGPA
    original_cgpa, _, _, _ = calculate_cgpa(conn, reg_no, use_best_grades=False)
    
    # Get BPUT SGPAs for each semester (from original attempts)
    bput_sgpas = {}
    results = conn.execute(
        "SELECT semester_number, sgpa_bput, MIN(exam_session) FROM results WHERE registration_number = ? GROUP BY semester_number",
        (reg_no,)
    ).fetchall()
    for r in results:
        bput_sgpas[r[0]] = r[1]
    
    # Enrich semester data with BPUT SGPA
    for sem in semesters:
        sem["sgpa_bput"] = bput_sgpas.get(sem["semester"], "")
    
    # Get all back paper attempts
    back_papers = []
    for sem in semesters:
        for subj in sem.get("subjects", []):
            if subj.get("is_backpaper"):
                all_attempts = get_all_attempts_for_subject(conn, reg_no, subj["subject_code"])
                back_papers.append({
                    "subject_code": subj["subject_code"],
                    "subject_name": subj["subject_name"],
                    "original_semester": sem["semester"],
                    "attempts": [
                        {
                            "session": a[0],
                            "grade": a[2],
                            "grade_points": a[3],
                            "is_pass": bool(a[6])
                        } for a in all_attempts
                    ]
                })
    
    # Compute overall rank (rank among all students) and class rank.
    # Reuse the cached leaderboard so we don't recompute CGPA for all 435
    # students on every student-detail request.
    all_students, _ = _get_cached_leaderboard(None, None, None)
    if all_students is None:
        all_students = get_leaderboard(conn)
        _set_cached_leaderboard(None, None, None, all_students, len(all_students))
    total_students = len(all_students)
    overall_rank = None
    for entry in all_students:
        if entry["registration_number"] == reg_no:
            overall_rank = entry["rank"]
            break

    class_rank = None
    class_students, _ = _get_cached_leaderboard(student[1], None, None)
    if class_students is None:
        class_students = get_leaderboard(conn, branch_filter=student[1])
        _set_cached_leaderboard(student[1], None, None, class_students, len(class_students))
    class_total = len(class_students)
    for entry in class_students:
        if entry["registration_number"] == reg_no:
            class_rank = entry["rank"]
            break

    conn.close()

    photo_url = ""
    if student[3]:
        photo_url = f"https://results.bput.ac.in/{student[3]}"

    return jsonify({
        "registration_number": reg_no,
        "name": student[0],
        "branch": student[1],
        "college": student[2] or "Trident Academy of Technology, Bhubaneswar",
        "photo_url": photo_url,
        "cgpa": cgpa,
        "original_cgpa": original_cgpa,
        "total_credits": total_credits,
        "overall_rank": overall_rank,
        "total_students": total_students,
        "class_rank": class_rank,
        "class_total": class_total,
        "semesters": semesters,
        "back_papers": back_papers,
        "source": "BPUT (Biju Patnaik University of Technology)",
        "disclaimer": "Results are provisional and sourced from BPUT. This is an unofficial aggregation."
    })


@app.route("/api/search")
def search():
    """
    Search students by name or registration number.
    Query params:
      - q: search query
      - limit: max results (default 20)
    """
    query = request.args.get("q", "").strip()
    limit = request.args.get("limit", 20, type=int)
    
    if not query or len(query) < 2:
        return jsonify([])
    
    conn = get_connection()
    
    # Search by name or registration number
    results = conn.execute("""
        SELECT s.registration_number, s.name, s.branch
        FROM students s
        WHERE s.name LIKE ? OR s.registration_number LIKE ?
        ORDER BY s.name
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", limit)).fetchall()
    
    # Enrich with CGPA if available
    search_results = []
    for r in results:
        reg_no = r[0]
        has_results = conn.execute(
            "SELECT COUNT(*) FROM results WHERE registration_number = ?",
            (reg_no,)
        ).fetchone()[0]
        
        cgpa = None
        if has_results > 0:
            cgpa_val, _, _, _ = calculate_cgpa(conn, reg_no, use_best_grades=True)
            cgpa = cgpa_val
        
        search_results.append({
            "registration_number": reg_no,
            "name": r[1],
            "branch": r[2],
            "cgpa": cgpa,
            "has_results": has_results > 0
        })
    
    conn.close()
    return jsonify(search_results)


@app.route("/api/compare")
def compare():
    """
    Compare multiple students.
    Query params:
      - reg_nos: comma-separated registration numbers
    """
    reg_nos = request.args.get("reg_nos", "").split(",")
    reg_nos = [r.strip() for r in reg_nos if r.strip()]
    
    if not reg_nos:
        return jsonify({"error": "No registration numbers provided"}), 400
    
    conn = get_connection()
    comparison = []
    
    for reg_no in reg_nos[:10]:  # Max 10 students
        student = conn.execute(
            "SELECT name, branch FROM students WHERE registration_number = ?",
            (reg_no,)
        ).fetchone()
        
        if not student:
            continue
        
        cgpa, total_credits, _, semesters = calculate_cgpa(conn, reg_no, use_best_grades=True)
        
        comparison.append({
            "registration_number": reg_no,
            "name": student[0],
            "branch": student[1],
            "cgpa": cgpa,
            "total_credits": total_credits,
            "semester_sgpas": {s["semester"]: s["sgpa"] for s in semesters}
        })
    
    conn.close()
    return jsonify(comparison)


if __name__ == "__main__":
    print("Starting CGPA Monitor API Server...")
    print("API docs:")
    print("  GET /api/stats          - Overall statistics")
    print("  GET /api/branches       - List branches")
    print("  GET /api/leaderboard    - Leaderboard (params: branch, course, semester, page)")
    print("  GET /api/student/<reg>  - Student detail")
    print("  GET /api/search?q=      - Search students")
    print("  GET /api/compare        - Compare students (params: reg_nos)")
    app.run(host="0.0.0.0", port=5000, debug=True)
