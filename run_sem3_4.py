import sys, os
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_semester
from calculations import calculate_cgpa, get_connection

print("Scraping Sem 3...")
scrape_semester(3)
print("Scraping Sem 4...")
scrape_semester(4)

print("Recalculating all results just to be sure...")
conn = get_connection()
rows = conn.execute("SELECT registration_number FROM students").fetchall()
for r in rows:
    # Trigger full CGPA recalculation which also updates sgpa_calculated if needed
    calculate_cgpa(conn, r[0])
conn.commit()
conn.close()

print("ALL DONE")
