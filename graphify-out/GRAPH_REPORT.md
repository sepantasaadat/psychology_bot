# Graph Report - psychology_bot  (2026-11-11)

## Corpus Check
- 19 files · ~11,463 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 144 nodes · 297 edges · 11 communities (10 shown, 1 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `65ac2de4`
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
- Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan
- handle_text
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec

## God Nodes (most connected - your core abstractions)
1. `button_handler()` - 22 edges
2. `get_connection()` - 19 edges
3. `get_main_menu_keyboard()` - 15 edges
4. `handle_text()` - 13 edges
5. `add_confirmed_appointment()` - 13 edges
6. `format_upcoming_week_appointments()` - 10 edges
7. `get_appointment()` - 9 edges
8. `TestDatabaseWeeklyAppointments` - 7 edges
9. `get_user_confirmed_appointments_for_week()` - 7 edges
10. `setup_database()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → main.py
- `Task 2: Implement Admin Direct Booking Flow in `handle_text`` --references--> `get_main_menu_keyboard()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → main.py
- `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan` --references--> `get_main_menu_keyboard()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-cancellation-time-restrictions.md → main.py
- `Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback` --references--> `get_main_menu_keyboard()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-cancellation-time-restrictions.md → main.py
- `User Appointment Cancellation Implementation Plan` --references--> `get_main_menu_keyboard()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-user-cancellation.md → main.py

## Import Cycles
- None detected.

## Communities (11 total, 1 thin omitted)

### Community 0 - "get_connection"
Cohesion: 0.19
Nodes (17): add_pending_appointment(), add_user(), delete_appointment(), get_all_confirmed_appointments(), get_appointment(), get_booked_times(), get_connection(), get_user_confirmed_appointments_for_week() (+9 more)

### Community 1 - "TestDatabaseWeeklyAppointments"
Cohesion: 0.14
Nodes (8): get_upcoming_week_confirmed_appointments(), Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, TestDatabaseWeeklyAppointments

### Community 2 - "app.py"
Cohesion: 0.20
Nodes (7): about(), booking(), get_1405_working_days(), get_available_hours(), get_db_connection(), send_receipt_to_telegram(), setup_web_user()

### Community 4 - "handle_receipt"
Cohesion: 0.18
Nodes (10): Task 1: Add Datetime Parsing and Cancellation Eligibility Helper, can_cancel_appointment(), error_handler(), get_current_jalali_datetime(), get_upcoming_days(), handle_receipt(), main(), parse_appointment_datetime() (+2 more)

### Community 5 - "format_upcoming_week_appointments"
Cohesion: 0.13
Nodes (8): Task 2: Implement Admin Direct Booking Flow in `handle_text`, Admin Direct Booking Flow Spec, Goal, Requirements, format_upcoming_week_appointments(), handle_text(), TestAdminDirectBooking, TestAdminWorkflow

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan"
Cohesion: 0.33
Nodes (5): Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan, Global Constraints, Review Focus, Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 8 - "handle_text"
Cohesion: 0.12
Nodes (9): add_confirmed_appointment(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_main_menu_keyboard(), TestCancellationPolicyIntegration (+1 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `button_handler()` connect `get_connection` to `TestDatabaseWeeklyAppointments`, `handle_receipt`, `format_upcoming_week_appointments`, `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`, `handle_text`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `button_handler()` (e.g. with `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`button_handler()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `TestDatabaseWeeklyAppointments` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `get_main_menu_keyboard()` connect `handle_text` to `get_connection`, `jdatetime`, `handle_receipt`, `format_upcoming_week_appointments`, `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `get_main_menu_keyboard()` (e.g. with `Task 2: Implement Admin Direct Booking Flow in `handle_text`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`get_main_menu_keyboard()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `format_upcoming_week_appointments` be split into smaller, more focused modules?**
  _Cohesion score 0.1286549707602339 - nodes in this community are weakly interconnected._
- **Why does `get_connection()` connect `get_connection` to `handle_text`, `TestDatabaseWeeklyAppointments`, `jdatetime`, `format_upcoming_week_appointments`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._