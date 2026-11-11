# Graph Report - psychology_bot  (2026-11-11)

## Corpus Check
- 16 files · ~9,663 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 119 nodes · 244 edges · 10 communities (9 shown, 1 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ad5f0d1f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_connection
- TestDatabaseWeeklyAppointments
- app.py
- jdatetime
- handle_receipt
- format_upcoming_week_appointments
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- TestAdminDirectBooking
- handle_text
- User Appointment Cancellation Feature Spec

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 19 edges
2. `button_handler()` - 17 edges
3. `handle_text()` - 13 edges
4. `add_confirmed_appointment()` - 10 edges
5. `format_upcoming_week_appointments()` - 10 edges
6. `get_main_menu_keyboard()` - 10 edges
7. `get_appointment()` - 7 edges
8. `get_user_confirmed_appointments_for_week()` - 7 edges
9. `TestDatabaseWeeklyAppointments` - 7 edges
10. `setup_database()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add `add_confirmed_appointment` Helper to Database` --references--> `add_confirmed_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → database.py
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Task 1: Add User Weekly Confirmed Appointments Query to Database` --references--> `get_user_confirmed_appointments_for_week()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-user-cancellation.md → database.py
- `Task 2: Implement Admin Direct Booking Flow in `handle_text`` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → main.py
- `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → main.py

## Import Cycles
- None detected.

## Communities (10 total, 1 thin omitted)

### Community 0 - "get_connection"
Cohesion: 0.20
Nodes (16): add_pending_appointment(), delete_appointment(), get_all_confirmed_appointments(), get_appointment(), get_booked_times(), get_connection(), get_user_confirmed_appointments_for_week(), setup_database() (+8 more)

### Community 1 - "TestDatabaseWeeklyAppointments"
Cohesion: 0.14
Nodes (8): get_upcoming_week_confirmed_appointments(), Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, TestDatabaseWeeklyAppointments

### Community 2 - "app.py"
Cohesion: 0.24
Nodes (7): about(), booking(), get_1405_working_days(), get_available_hours(), get_db_connection(), send_receipt_to_telegram(), setup_web_user()

### Community 3 - "jdatetime"
Cohesion: 0.25
Nodes (3): get_upcoming_week_appointments(), send_email(), get_upcoming_days()

### Community 4 - "handle_receipt"
Cohesion: 0.32
Nodes (6): add_user(), error_handler(), handle_receipt(), handle_text(), main(), start()

### Community 5 - "format_upcoming_week_appointments"
Cohesion: 0.20
Nodes (5): Admin Direct Booking Flow Spec, Goal, Requirements, format_upcoming_week_appointments(), TestAdminWorkflow

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 8 - "handle_text"
Cohesion: 0.18
Nodes (9): add_confirmed_appointment(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_main_menu_keyboard() (+1 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `TestDatabaseWeeklyAppointments`, `jdatetime`, `handle_receipt`, `format_upcoming_week_appointments`, `TestAdminDirectBooking`, `handle_text`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `button_handler()` (e.g. with `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` and `Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py``) actually correct?**
  _`button_handler()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `TestDatabaseWeeklyAppointments` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `format_upcoming_week_appointments()` connect `format_upcoming_week_appointments` to `get_connection`, `TestDatabaseWeeklyAppointments`, `jdatetime`, `handle_receipt`, `handle_text`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `handle_text()` (e.g. with `Admin Direct Booking Implementation Plan` and `Task 2: Implement Admin Direct Booking Flow in `handle_text``) actually correct?**
  _`handle_text()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Why does `button_handler()` connect `get_connection` to `TestDatabaseWeeklyAppointments`, `jdatetime`, `handle_receipt`, `format_upcoming_week_appointments`, `handle_text`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `add_confirmed_appointment()` (e.g. with `Admin Direct Booking Implementation Plan` and `Task 1: Add `add_confirmed_appointment` Helper to Database`) actually correct?**
  _`add_confirmed_appointment()` has 3 INFERRED edges - model-reasoned connections that need verification._