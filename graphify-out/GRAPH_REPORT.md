# Graph Report - psychology_bot  (2026-11-11)

## Corpus Check
- 13 files · ~7,706 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 98 nodes · 198 edges · 11 communities (7 shown, 4 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 20 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `97d6f49a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- database.py
- Review Focus
- app.py
- jdatetime
- handle_receipt
- TestAdminWorkflow
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- TestDatabaseWeeklyAppointments
- handle_text
- booking
- sqlite3

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 17 edges
2. `button_handler()` - 14 edges
3. `handle_text()` - 13 edges
4. `format_upcoming_week_appointments()` - 10 edges
5. `add_confirmed_appointment()` - 7 edges
6. `get_upcoming_week_confirmed_appointments()` - 6 edges
7. `handle_receipt()` - 6 edges
8. `main()` - 6 edges
9. `TestDatabaseWeeklyAppointments` - 6 edges
10. `TestAdminWorkflow` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Task 1: Add `add_confirmed_appointment` Helper to Database` --references--> `add_confirmed_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → database.py
- `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → main.py
- `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` --references--> `button_handler()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → main.py
- `Admin Direct Booking Implementation Plan` --references--> `add_confirmed_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → database.py

## Import Cycles
- None detected.

## Communities (11 total, 4 thin omitted)

### Community 0 - "database.py"
Cohesion: 0.35
Nodes (10): add_pending_appointment(), add_user(), delete_appointment(), get_all_confirmed_appointments(), get_appointment(), get_booked_times(), get_connection(), get_upcoming_week_confirmed_appointments() (+2 more)

### Community 1 - "Review Focus"
Cohesion: 0.29
Nodes (6): Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 4 - "handle_receipt"
Cohesion: 0.29
Nodes (5): error_handler(), get_upcoming_days(), handle_receipt(), main(), start()

### Community 5 - "TestAdminWorkflow"
Cohesion: 0.15
Nodes (3): setup_database(), TestAdminDirectBooking, TestAdminWorkflow

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 8 - "handle_text"
Cohesion: 0.20
Nodes (13): add_confirmed_appointment(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, Admin Direct Booking Flow Spec (+5 more)

### Community 9 - "booking"
Cohesion: 0.40
Nodes (5): about(), booking(), get_available_hours(), get_db_connection(), setup_web_user()

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `format_upcoming_week_appointments()` connect `handle_text` to `database.py`, `Review Focus`, `jdatetime`, `handle_receipt`, `TestAdminWorkflow`?**
  _High betweenness centrality (0.165) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `button_handler()` (e.g. with `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` and `main()`) actually correct?**
  _`button_handler()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Why does `get_connection()` connect `database.py` to `handle_text`, `sqlite3`, `TestAdminWorkflow`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `handle_text()` (e.g. with `Admin Direct Booking Implementation Plan` and `Task 2: Implement Admin Direct Booking Flow in `handle_text``) actually correct?**
  _`handle_text()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Why does `handle_text()` connect `handle_text` to `database.py`, `handle_receipt`, `TestAdminWorkflow`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `format_upcoming_week_appointments()` (e.g. with `Task 2: Implement Admin Direct Booking Flow in `handle_text`` and `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py``) actually correct?**
  _`format_upcoming_week_appointments()` has 3 INFERRED edges - model-reasoned connections that need verification._