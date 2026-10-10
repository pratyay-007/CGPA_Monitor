import sqlite3
import os
from database import compute_grade_points, compute_sgpa

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgpa_monitor.db")
conn = sqlite3.connect(DB_PATH)

# Update grade_points and credit_index for all subject_attempts
rows = conn.execute("SELECT id, grade, credits FROM subject_attempts").fetchall()
for row in rows:
    attempt_id = row[0]
    grade = row[1]
    credits = float(row[2])
    
    # Recalculate
    gp = compute_grade_points(grade)
    credit_idx = credits * gp
    
    conn.execute(
        "UPDATE subject_attempts SET grade_points = ?, credit_index = ? WHERE id = ?",
        (gp, credit_idx, attempt_id)
    )

print("Updated subject_attempts.")

# Recalculate sgpa_calculated for all results
results = conn.execute("SELECT registration_number, exam_session, semester_number FROM results").fetchall()
for res in results:
    reg_no = res[0]
    session = res[1]
    sem_num = res[2]
    
    # Get all subjects for this result
    subjects = conn.execute(
        "SELECT credits, grade FROM subject_attempts WHERE registration_number = ? AND exam_session = ? AND semester_number = ?",
        (reg_no, session, sem_num)
    ).fetchall()
    
    valid_subjects = [
        {"credits": s[0], "grade": s[1]}
        for s in subjects if s[1] and s[1] != "P"
    ]
    calc_sgpa, _, _ = compute_sgpa(valid_subjects)
    
    conn.execute(
        "UPDATE results SET sgpa_calculated = ? WHERE registration_number = ? AND exam_session = ? AND semester_number = ?",
        (calc_sgpa, reg_no, session, sem_num)
    )

conn.commit()
conn.close()
print("Updated results.")
