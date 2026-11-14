# Graph Report - psychology_bot  (2026-11-14)

## Corpus Check
- 26 files · ~16,214 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 210 nodes · 426 edges · 14 communities
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 62 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f30be836`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_connection
- get_upcoming_days
- app.py
- Role-Based Booking Date Restrictions Spec
- handle_text
- format_upcoming_week_appointments
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- button_handler
- handle_text
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec
- main.py
- Review Focus
- get_user_confirmed_appointments_for_week

## God Nodes (most connected - your core abstractions)
1. `button_handler()` - 40 edges
2. `get_connection()` - 25 edges
3. `get_main_menu_keyboard()` - 17 edges
4. `format_upcoming_week_appointments()` - 15 edges
5. `add_confirmed_appointment()` - 13 edges
6. `handle_text()` - 13 edges
7. `handle_receipt()` - 12 edges
8. `TestAdminWorkflow` - 12 edges
9. `setup_database()` - 10 edges
10. `get_appointment()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-14-other-admin-approval-workflow-spec.md → main.py
- `Task 1: Add `admin_receipt_messages` Table and Database Helpers` --references--> `setup_database()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-other-admin-approval-workflow.md → database.py
- `Task 1: Add `add_confirmed_appointment` Helper to Database` --references--> `add_confirmed_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → database.py
- `Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py`` --references--> `get_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-user-cancellation.md → database.py

## Import Cycles
- None detected.

## Communities (14 total, 0 thin omitted)

### Community 0 - "get_connection"
Cohesion: 0.14
Nodes (17): add_pending_appointment(), add_user(), delete_admin_receipt_messages(), delete_appointment(), get_admin_receipt_messages(), get_all_confirmed_appointments(), get_booked_times(), get_connection() (+9 more)

### Community 1 - "get_upcoming_days"
Cohesion: 0.21
Nodes (8): Global Constraints, Review Focus, Role-Based Booking Date Restrictions Implementation Plan, Task 1: Update `get_upcoming_days` to Support Role-Based Offsets, Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_upcoming_days(), TestRoleBasedDates

### Community 2 - "app.py"
Cohesion: 0.20
Nodes (7): about(), booking(), get_1405_working_days(), get_available_hours(), get_db_connection(), send_receipt_to_telegram(), setup_web_user()

### Community 3 - "Role-Based Booking Date Restrictions Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, Role-Based Booking Date Restrictions Spec

### Community 4 - "handle_text"
Cohesion: 0.08
Nodes (19): Global Constraints, Other Admin Approval Workflow Implementation Plan, Admin Direct Booking Flow Spec, Goal, Requirements, Bot Flow Updates, Constraints, Context & Problem (+11 more)

### Community 5 - "format_upcoming_week_appointments"
Cohesion: 0.09
Nodes (15): Global Constraints, Handled Appointment Workflow Implementation Plan, Review Focus, Task 1: Extract `complete_admin_review_session` and Update Already-Handled Branch, Task 2: Full Verification, Knowledge Graph Update, and Push to GitHub, Approaches Considered, Constraints, Context & Problem (+7 more)

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "button_handler"
Cohesion: 0.17
Nodes (7): Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan, Global Constraints, Review Focus, Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, button_handler(), TestRoleBasedDatesIntegration

### Community 8 - "handle_text"
Cohesion: 0.12
Nodes (11): add_confirmed_appointment(), get_appointment(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub (+3 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

### Community 11 - "main.py"
Cohesion: 0.19
Nodes (7): get_upcoming_week_appointments(), send_email(), Task 1: Add Datetime Parsing and Cancellation Eligibility Helper, can_cancel_appointment(), get_current_jalali_datetime(), parse_appointment_datetime(), TestCancellationPolicyHelpers

### Community 12 - "Review Focus"
Cohesion: 0.29
Nodes (6): Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 13 - "get_user_confirmed_appointments_for_week"
Cohesion: 0.28
Nodes (7): get_user_confirmed_appointments_for_week(), Global Constraints, Review Focus, Task 1: Add User Weekly Confirmed Appointments Query to Database, Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, User Appointment Cancellation Implementation Plan

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `button_handler()` connect `button_handler` to `get_connection`, `get_upcoming_days`, `handle_text`, `format_upcoming_week_appointments`, `handle_text`, `main.py`, `Review Focus`, `get_user_confirmed_appointments_for_week`?**
  _High betweenness centrality (0.298) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `button_handler()` (e.g. with `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`button_handler()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `get_connection` be split into smaller, more focused modules?**
  _Cohesion score 0.14245014245014245 - nodes in this community are weakly interconnected._
- **Why does `format_upcoming_week_appointments()` connect `format_upcoming_week_appointments` to `get_connection`, `handle_text`, `button_handler`, `handle_text`, `main.py`, `Review Focus`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `get_main_menu_keyboard()` (e.g. with `Task 2: Implement Admin Direct Booking Flow in `handle_text`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`get_main_menu_keyboard()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `handle_text` be split into smaller, more focused modules?**
  _Cohesion score 0.08275862068965517 - nodes in this community are weakly interconnected._
- **Why does `setup_database()` connect `get_connection` to `handle_text`, `handle_text`, `format_upcoming_week_appointments`, `button_handler`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._