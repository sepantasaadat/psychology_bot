# Graph Report - psychology_bot  (2026-11-11)

## Corpus Check
- 10 files · ~6,206 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 78 nodes · 154 edges · 8 communities (6 shown, 2 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `abb48a84`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- database.py
- Review Focus
- app.py
- daily_report.py
- handle_receipt
- format_upcoming_week_appointments
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- TestDatabaseWeeklyAppointments

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 14 edges
2. `button_handler()` - 14 edges
3. `format_upcoming_week_appointments()` - 7 edges
4. `get_upcoming_week_confirmed_appointments()` - 6 edges
5. `handle_receipt()` - 6 edges
6. `main()` - 6 edges
7. `TestAdminWorkflow` - 6 edges
8. `booking()` - 6 edges
9. `start()` - 5 edges
10. `handle_text()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → main.py
- `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` --references--> `button_handler()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → main.py
- `handle_receipt()` --calls--> `add_user()`  [EXTRACTED]
  main.py → database.py
- `handle_receipt()` --calls--> `add_pending_appointment()`  [EXTRACTED]
  main.py → database.py

## Import Cycles
- None detected.

## Communities (8 total, 2 thin omitted)

### Community 0 - "database.py"
Cohesion: 0.32
Nodes (11): add_pending_appointment(), add_user(), delete_appointment(), get_all_confirmed_appointments(), get_appointment(), get_booked_times(), get_connection(), get_upcoming_week_confirmed_appointments() (+3 more)

### Community 1 - "Review Focus"
Cohesion: 0.29
Nodes (6): Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 2 - "app.py"
Cohesion: 0.22
Nodes (7): about(), booking(), get_1405_working_days(), get_available_hours(), get_db_connection(), send_receipt_to_telegram(), setup_web_user()

### Community 3 - "daily_report.py"
Cohesion: 0.24
Nodes (3): get_upcoming_week_appointments(), send_email(), get_upcoming_days()

### Community 4 - "handle_receipt"
Cohesion: 0.33
Nodes (6): error_handler(), get_main_menu_keyboard(), handle_receipt(), handle_text(), main(), start()

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `format_upcoming_week_appointments()` connect `format_upcoming_week_appointments` to `database.py`, `Review Focus`, `daily_report.py`, `handle_receipt`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `button_handler()` (e.g. with `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` and `main()`) actually correct?**
  _`button_handler()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Why does `get_connection()` connect `database.py` to `daily_report.py`, `format_upcoming_week_appointments`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `button_handler()` connect `database.py` to `Review Focus`, `daily_report.py`, `handle_receipt`, `format_upcoming_week_appointments`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._