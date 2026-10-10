"""Check students with missing actual semester subjects."""
import sqlite3, os
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgpa_monitor.db")
conn = sqlite3.connect(DB)

for sem in [3, 4]:
    rows = conn.execute("""
        SELECT registration_number, COUNT(*) as cnt
        FROM subject_attempts WHERE semester_number = ?
        GROUP BY registration_number
        HAVING cnt < 5
        ORDER BY cnt
    """, (sem,)).fetchall()
    print(f"Sem {sem}: {len(rows)} students with <5 subjects (likely only back papers scraped)")
    for r in rows[:5]:
        print(f"  {r[0]}: {r[1]} subjects")

# Normal subject count per semester
for sem in [1,2,3,4]:
    rows = conn.execute("""
        SELECT COUNT(DISTINCT registration_number) as students, 
               ROUND(AVG(cnt),1) as avg_subj
        FROM (
            SELECT registration_number, COUNT(*) as cnt
            FROM subject_attempts WHERE semester_number = ?
            GROUP BY registration_number
        )
    """, (sem,)).fetchone()
    print(f"Sem {sem}: {rows[0]} students, avg {rows[1]} subjects per student")

conn.close()
