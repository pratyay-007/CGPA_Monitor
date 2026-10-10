"""Run scraping for all semesters in order, logging to a file.
Uses unbuffered output so progress can be monitored in real time."""
import sys
import os
import datetime

# Force unbuffered stdout
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_all_semesters

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrape_log.txt")

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

log("=" * 60)
log("STARTING FULL SCRAPE (all semesters)")
log("=" * 60)

try:
    scrape_all_semesters()
    log("ALL SEMESTERS COMPLETED SUCCESSFULLY")
except Exception as e:
    log(f"ERROR: {e}")
    import traceback
    log(traceback.format_exc())

log("SCRAPE SCRIPT FINISHED")
