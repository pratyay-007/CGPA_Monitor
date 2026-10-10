"""Fix stale scrape sessions marked as 'running' from interrupted scrapes."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgpa_monitor.db")
conn = sqlite3.connect(DB_PATH)
conn.execute("UPDATE scrape_sessions SET status='interrupted', completed_at=datetime('now') WHERE status='running'")
conn.commit()
print("Fixed stale scrape sessions")
rows = conn.execute("SELECT id, exam_session, semester_number, status FROM scrape_sessions ORDER BY id").fetchall()
for r in rows:
    print(r)
conn.close()
