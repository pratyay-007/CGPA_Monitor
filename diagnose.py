"""Diagnostic: check branch counts and leaderboard issue."""
import sqlite3, os
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cgpa_monitor.db")
conn = sqlite3.connect(DB)

print("=== Branch counts ===")
rows = conn.execute("SELECT branch, COUNT(*) FROM students GROUP BY branch ORDER BY branch").fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]}")

print("\n=== Back paper subjects (subject in multiple semesters for same student) ===")
rows = conn.execute("""
    SELECT COUNT(DISTINCT registration_number) 
    FROM (
        SELECT registration_number, subject_code
        FROM subject_attempts
        GROUP BY registration_number, subject_code
        HAVING COUNT(DISTINCT semester_number) > 1
    )
""").fetchone()
print(f"  Students with back papers stored across semesters: {rows[0]}")

# Count total cross-semester back paper entries
rows = conn.execute("""
    SELECT COUNT(*) 
    FROM subject_attempts sa
    WHERE EXISTS (
        SELECT 1 FROM subject_attempts sa2
        WHERE sa2.registration_number = sa.registration_number
        AND sa2.subject_code = sa.subject_code
        AND sa2.semester_number < sa.semester_number
    )
""").fetchone()
print(f"  Total back paper attempts stored in wrong semester: {rows[0]}")

# Show a sample student with back papers
print("\n=== Sample: Student 2401289006 all subjects by semester ===")
for sem in [1,2,3,4]:
    rows = conn.execute("""
        SELECT subject_code, subject_name, grade, grade_points, credits
        FROM subject_attempts 
        WHERE registration_number='2401289006' AND semester_number=?
        ORDER BY subject_code
    """, (sem,)).fetchall()
    print(f"\n  Semester {sem} ({len(rows)} subjects):")
    for r in rows:
        print(f"    {r[0]} {r[1][:35]:35s} {r[2]:8s} GP={r[3]} Cr={r[4]}")

conn.close()
