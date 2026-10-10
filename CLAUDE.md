# CGPA Monitor Project

## Overview
Building a website called "CGPA Monitor" for students of Trident Academy of Technology (affiliated to BPUT University, Odisha, India). The website helps students track their CGPA/SGPA with special handling for back papers.

## Key Features
1. Open access (no login required) — anyone can view the leaderboard
2. Leaderboard showing all students ranked by CGPA
3. Filters: branch, B.Tech vs Biotech, specific semester (SGPA)
4. Student detail page showing all semesters with subjects, credits, grades, SGPA
5. Search by name or registration number
6. Special back-paper handling: Show cleared subjects in original semester, calculate best-attempt SGPA/CGPA

## Current Status
- Website built and running; mobile optimization + pagination in progress (see PROGRESS.md).
- In-progress (2026-10-06): leaderboard pagination (40 per page), mobile-responsive card layout, mobile filter fix, student detail rank cards (overall + class rank), subject table mobile stacking, spotlight cursor disabled on mobile.

See PROGRESS.md for detailed progress tracking.

## Technical Stack (Planned)
- Scraper: Python (requests, BeautifulSoup, SQLite)
- Database: SQLite (development), Supabase Postgres (production)
- Frontend: Next.js + Tailwind CSS
- Hosting: Vercel

## Important Rules
- Scrape ONCE per semester, store in database, website only READS database
- Be polite to BPUT server: 1 request at a time, 1-2.5s delay, retries
- Save raw response for every student to enable re-parsing
- Store EVERY attempt of every subject, not just final results
- Compare calculated SGPA with BPUT's SGPA to validate maths
- Show "Source: BPUT, fetched on <date>" on result pages
- Mark results as unofficial

## Grade Points
O=10, E=9, A=8, B=7, C=6, D=5 (pass theory), F=2 (fail), M=0 (malpractice), S=0 (absent)
Note: C is pass grade for practical/sessional/project/viva

## Formulas
- Credit Index = credits × grade points
- SGPA = sum(Credit Index of semester) / sum(credits of semester)
- CGPA = sum(Credit Index of ALL semesters) / sum(credits of ALL semesters)
