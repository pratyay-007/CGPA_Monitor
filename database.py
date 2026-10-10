"""
Database schema and helpers for CGPA Monitor.
Tables:
  - students: registration_number, name, branch
  - scrape_sessions: metadata about each scrape run
  - raw_responses: raw JSON responses from BPUT (for re-parsing)
  - results: semester-level data (SGPA, credits) per student per session
  - subject_attempts: individual subject grades for every attempt
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgpa_monitor.db")


def get_connection():
    """Get a database connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            registration_number TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            branch TEXT NOT NULL,
            college_name TEXT,
            student_photo TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scrape_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_session TEXT NOT NULL,       -- e.g., "Odd-(2024-25)"
            semester_number INTEGER NOT NULL,  -- e.g., 1
            started_at TEXT NOT NULL,
            completed_at TEXT,
            total_students INTEGER DEFAULT 0,
            successful INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            no_result INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running'      -- running, completed, failed
        );

        CREATE TABLE IF NOT EXISTS raw_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_number TEXT NOT NULL,
            exam_session TEXT NOT NULL,
            semester_number INTEGER NOT NULL,
            endpoint TEXT NOT NULL,            -- which API endpoint
            response_json TEXT NOT NULL,       -- raw JSON response
            http_status INTEGER,
            fetched_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (registration_number) REFERENCES students(registration_number)
        );

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_number TEXT NOT NULL,
            exam_session TEXT NOT NULL,        -- e.g., "Odd-(2024-25)"
            semester_number INTEGER NOT NULL,
            semester_label TEXT,               -- e.g., "1st"
            branch_name TEXT,
            sgpa_bput TEXT,                    -- SGPA reported by BPUT
            total_credits_bput TEXT,           -- credits reported by BPUT
            sgpa_calculated REAL,              -- our calculated SGPA
            fetched_at TEXT DEFAULT (datetime('now')),
            UNIQUE(registration_number, exam_session, semester_number),
            FOREIGN KEY (registration_number) REFERENCES students(registration_number)
        );

        CREATE TABLE IF NOT EXISTS subject_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_number TEXT NOT NULL,
            exam_session TEXT NOT NULL,        -- session when this attempt was taken
            semester_number INTEGER NOT NULL,  -- which semester this subject belongs to
            subject_code TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            subject_type TEXT,                 -- T (Theory), P (Practical), etc.
            credits REAL NOT NULL,
            grade TEXT NOT NULL,
            recheck INTEGER DEFAULT 0,
            is_pass INTEGER,                   -- 1 if passed, 0 if failed
            grade_points REAL,                 -- computed grade points
            credit_index REAL,                 -- credits * grade_points
            fetched_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (registration_number) REFERENCES students(registration_number)
        );

        CREATE INDEX IF NOT EXISTS idx_results_reg ON results(registration_number);
        CREATE INDEX IF NOT EXISTS idx_results_session ON results(exam_session);
        CREATE INDEX IF NOT EXISTS idx_attempts_reg ON subject_attempts(registration_number);
        CREATE INDEX IF NOT EXISTS idx_attempts_session ON subject_attempts(exam_session);
        CREATE INDEX IF NOT EXISTS idx_attempts_subject ON subject_attempts(subject_code);
        CREATE INDEX IF NOT EXISTS idx_raw_reg ON raw_responses(registration_number);
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")


def load_students_from_json(json_path):
    """Load students from students.json into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    with open(json_path, "r", encoding="utf-8") as f:
        students = json.load(f)

    inserted = 0
    for s in students:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO students (registration_number, name, branch)
                VALUES (?, ?, ?)
            """, (s["registration_number"], s["name"], s["branch"]))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error inserting {s['registration_number']}: {e}")

    conn.commit()
    conn.close()
    print(f"Loaded {inserted} new students (total in JSON: {len(students)})")
    return inserted


# Grade point mapping
GRADE_POINTS = {
    "O": 10, "E": 9, "A": 8, "B": 7, "C": 6,
    "D": 5, "F": 2, "M": 0, "S": 0
}

# Pass grades: D and above for theory, C and above for practical/sessional/project/viva
PASS_GRADES_THEORY = {"O", "E", "A", "B", "C", "D"}
PASS_GRADES_PRACTICAL = {"O", "E", "A", "B", "C"}


def compute_grade_points(grade):
    """Convert a grade letter to grade points. Handles suffixes like F(Ex), F(Int)."""
    g = grade.upper().strip()
    # Extract base grade before any parenthesis, e.g. "F(Ex)" -> "F"
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


def compute_sgpa(subjects):
    """
    Compute SGPA from a list of subject dicts with 'credits' and 'grade'.
    Returns (sgpa, total_credits, total_credit_index).
    """
    total_credits = 0
    total_credit_index = 0

    for s in subjects:
        credits = float(s["credits"])
        gp = compute_grade_points(s["grade"])
        total_credits += credits
        total_credit_index += credits * gp

    if total_credits == 0:
        return 0, 0, 0

    sgpa = total_credit_index / total_credits
    return round(sgpa, 2), total_credits, total_credit_index


if __name__ == "__main__":
    init_db()
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.json")
    if os.path.exists(json_path):
        load_students_from_json(json_path)
