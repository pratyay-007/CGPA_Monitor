# Progress Tracker

## Project Goal
Build a website called "CGPA Monitor" for Trident Academy of Technology students (BPUT affiliated) that:
- Shows students ranked by CGPA on a leaderboard
- Tracks SGPA per semester
- Handles back papers by showing cleared subjects in their ORIGINAL semester
- Displays both "Official SGPA (BPUT)" and "Updated SGPA (after back papers)"

## BPUT Result Website
URL: https://results.bput.ac.in/
Flow: Select session (e.g., Odd (2024-25) for sem 1) → enter registration number → enter any DOB → click View → see result list → click View on a result → click Reset to redo

## Sessions
- Sem 1 = Odd (2024-25)
- Sem 2 = Even (2024-25)
- Sem 3 = Odd (2025-26)
- Sem 4 = Even (2025-26)

## Data
- students.json: 435 students with registration numbers starting with 24 (2024 batch)
- Sample registration numbers to test: 2401289308, 2401289285

## Current Status
Tick 'X' on each step after completing

[X] Phase 1: Data Collection - Semester 1
  [X] 1.1 Investigate BPUT result site (network requests, form fields)
  [X] 1.2 Test on sample registration numbers (2401289308, 2401289285)
  [X] 1.3 Scrape all 435 students for semester 1 — *COMPLETE: 435/435 scraped*
  [X] 1.4 Save raw responses + structured data in SQLite

[X] Phase 2: Database & Calculations (Semester 1)
  [X] 2.1 Create SQLite schema (students, results, attempts)
  [X] 2.2 Implement SGPA/CGPA calculations
  [X] 2.3 Validate calculated SGPA vs BPUT SGPA
  [X] 2.4 Back-paper merge logic

[X] Phase 3: Semesters 2-4 & Back Papers
  [X] 3.1 Scrape semesters 2, 3, 4 — *COMPLETE: all 435 students × 4 semesters, 0 failures (finished 2026-10-04 10:21 AM)*
  [X] 3.2 Update calculations for multiple semesters
  [X] 3.3 Sem 1 re-scrape of remaining 73 students — *DONE*

[X] Phase 4: Web Application
  [X] 4.1 SQLite-reading web app
  [X] 4.2 Google login — *skipped: site is open access, no login required*
  [X] 4.3 Leaderboard with filters
  [X] 4.4 Student detail pages
  [X] 4.5 Search functionality

## Recent Changes (Mobile Optimization & Pagination)
- [X] Add pagination to leaderboard (40 students per page)
- [X] Optimize leaderboard table for mobile (stack rows vertically)
- [X] Fix mobile filter dropdown (don't cover whole screen)
- [X] Remove "Total Credits" from student detail header card
- [X] Add Overall Rank and Class Rank to student detail page
- [X] Optimize subject tables for mobile (stack columns)
- [X] Remove SpotlightCursor on mobile devices
- [X] Add mobile layout breakpoints for leaderboard cards

## Open Issues / Next Fixes (mobile polish, 2026-10-08)
- [X] Leaderboard top-3 gradient highlight is based on page index, not global rank — rank #41 shows as "1st" when it lands on a new page. Only highlight top 3 when on page 1 (use `student.rank <= 3`).
- [X] Leaderboard cards merge into the background border — add a visible card border/background so each student card feels separate.
- [X] Header text too big on mobile — center + smaller font for title/subtitle.
- [X] Filters panel too bulky on mobile — replace the big card with a slim pill button that expands inline.
- [X] Student detail CGPA/rank cards too large and "floating" — make them compact chips in a single row.
- [X] Student detail auto-expands Sem 1 on load — remove auto-expand; no semester open by default.
- [X] Subject detail layout awkward (type/credit/gp/ci on separate lines) — redesign as a compact single-row chip layout.
- [X] Pagination "Previous" cut off and "Next" needs horizontal scroll — make pagination a horizontally scrollable strip with compact buttons.
- [X] Mobile scroll laggy — reduce BeamsBackground intensity/beams on mobile, lower DPR, reduce PER_PAGE 40 → 25.

[X] Phase 5: Production
  [X] Deployment

## Key Decisions
- Python (requests + BeautifulSoup) for scraping
- SQLite for development, Supabase Postgres for production
- All data stored in project folder
- One request at a time with 1-2.5s delays
- Open access: no authentication needed (anyone can view the leaderboard)
- Backend API already supports `page` and `per_page` params for leaderboard pagination
- Student detail API enhanced with rank computation
- Frontend card-based layout for mobile responsiveness