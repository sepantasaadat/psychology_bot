# Graph Report - psychology_bot  (2026-11-14)

## Corpus Check
- 26 files · ~16,573 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 212 nodes · 434 edges · 14 communities (13 shown, 1 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 62 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fbd4c3f4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- button_handler
- get_upcoming_days
- app.py
- Role-Based Booking Date Restrictions Spec
- add_confirmed_appointment
- format_upcoming_week_appointments
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- handle_receipt
- setup_database
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec
- TestDatabaseWeeklyAppointments
- get_main_menu_keyboard

## God Nodes (most connected - your core abstractions)
1. `button_handler()` - 42 edges
2. `get_connection()` - 28 edges
3. `get_main_menu_keyboard()` - 17 edges
4. `format_upcoming_week_appointments()` - 15 edges
5. `TestAdminWorkflow` - 14 edges
6. `add_confirmed_appointment()` - 13 edges
7. `handle_text()` - 13 edges
8. `handle_receipt()` - 12 edges
9. `setup_database()` - 10 edges
10. `get_appointment()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-14-other-admin-approval-workflow-spec.md → main.py
- `Task 1: Add `admin_receipt_messages` Table and Database Helpers` --references--> `setup_database()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-other-admin-approval-workflow.md → database.py
- `Task 1: Add `add_confirmed_appointment` Helper to Database` --references--> `add_confirmed_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → database.py
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Task 1: Add User Weekly Confirmed Appointments Query to Database` --references--> `get_user_confirmed_appointments_for_week()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-user-cancellation.md → database.py

## Import Cycles
- None detected.

## Communities (14 total, 1 thin omitted)

### Community 0 - "button_handler"
Cohesion: 0.14
Nodes (11): delete_appointment(), get_admin_receipt_messages(), get_all_confirmed_appointments(), get_appointment(), get_booked_times(), get_connection(), update_appointment_status(), Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py` (+3 more)

### Community 1 - "get_upcoming_days"
Cohesion: 0.21
Nodes (8): Global Constraints, Review Focus, Role-Based Booking Date Restrictions Implementation Plan, Task 1: Update `get_upcoming_days` to Support Role-Based Offsets, Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_upcoming_days(), TestRoleBasedDates

### Community 2 - "app.py"
Cohesion: 0.17
Nodes (9): about(), booking(), get_1405_working_days(), get_available_hours(), get_db_connection(), send_receipt_to_telegram(), setup_web_user(), get_upcoming_week_appointments() (+1 more)

### Community 3 - "Role-Based Booking Date Restrictions Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, Role-Based Booking Date Restrictions Spec

### Community 4 - "add_confirmed_appointment"
Cohesion: 0.10
Nodes (16): add_confirmed_appointment(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, Admin Direct Booking Flow Spec (+8 more)

### Community 5 - "format_upcoming_week_appointments"
Cohesion: 0.12
Nodes (14): Global Constraints, Handled Appointment Workflow Implementation Plan, Review Focus, Task 1: Extract `complete_admin_review_session` and Update Already-Handled Branch, Task 2: Full Verification, Knowledge Graph Update, and Push to GitHub, Approaches Considered, Constraints, Context & Problem (+6 more)

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "handle_receipt"
Cohesion: 0.12
Nodes (18): add_pending_appointment(), add_user(), delete_admin_receipt_messages(), save_admin_receipt_message(), Global Constraints, Other Admin Approval Workflow Implementation Plan, Review Focus, Task 2: Track Receipt Messages and Implement Other Admin Cleanup on Approval (+10 more)

### Community 8 - "setup_database"
Cohesion: 0.13
Nodes (3): setup_database(), Task 1: Add `admin_receipt_messages` Table and Database Helpers, TestCancellationPolicyIntegration

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

### Community 12 - "TestDatabaseWeeklyAppointments"
Cohesion: 0.14
Nodes (8): get_upcoming_week_confirmed_appointments(), Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, TestDatabaseWeeklyAppointments

### Community 13 - "get_main_menu_keyboard"
Cohesion: 0.13
Nodes (17): get_user_confirmed_appointments_for_week(), Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan, Global Constraints, Review Focus, Task 1: Add Datetime Parsing and Cancellation Eligibility Helper, Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, Global Constraints (+9 more)

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `button_handler()` connect `button_handler` to `get_upcoming_days`, `add_confirmed_appointment`, `format_upcoming_week_appointments`, `handle_receipt`, `main.py`, `TestDatabaseWeeklyAppointments`, `get_main_menu_keyboard`?**
  _High betweenness centrality (0.303) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `button_handler()` (e.g. with `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`button_handler()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `button_handler` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `format_upcoming_week_appointments()` connect `format_upcoming_week_appointments` to `button_handler`, `add_confirmed_appointment`, `handle_receipt`, `main.py`, `TestDatabaseWeeklyAppointments`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `get_main_menu_keyboard()` (e.g. with `Task 2: Implement Admin Direct Booking Flow in `handle_text`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`get_main_menu_keyboard()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `add_confirmed_appointment` be split into smaller, more focused modules?**
  _Cohesion score 0.09971509971509972 - nodes in this community are weakly interconnected._
- **Why does `setup_database()` connect `setup_database` to `button_handler`, `main.py`, `add_confirmed_appointment`, `TestDatabaseWeeklyAppointments`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._