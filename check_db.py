"""Quick DB status check."""
import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgpa_monitor.db")
conn = sqlite3.connect(DB_PATH)

print("=== Results per semester ===")
rows = conn.execute("SELECT semester_number, exam_session, COUNT(*) FROM results GROUP BY semester_number, exam_session ORDER BY semester_number").fetchall()
for r in rows:
    print(f"  Sem {r[0]} ({r[1]}): {r[2]}/435")

print("\n=== Subject attempts per semester ===")
rows = conn.execute("SELECT semester_number, COUNT(DISTINCT registration_number), COUNT(*) FROM subject_attempts GROUP BY semester_number ORDER BY semester_number").fetchall()
for r in rows:
    print(f"  Sem {r[0]}: {r[1]} students, {r[2]} subject records")

print("\n=== Scrape sessions (completed) ===")
rows = conn.execute("SELECT id, exam_session, semester_number, started_at, completed_at, successful, failed, no_result, status FROM scrape_sessions ORDER BY id").fetchall()
for r in rows:
    print(f"  Session {r[0]}: Sem {r[2]} ({r[1]}) - success={r[5]}, fail={r[6]}, no_result={r[7]} [{r[8]}]")

conn.close()
