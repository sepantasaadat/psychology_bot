# Graph Report - psychology_bot  (2026-11-11)

## Corpus Check
- 22 files · ~13,027 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 167 nodes · 336 edges · 11 communities
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 41 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c560a982`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- database.py
- get_upcoming_days
- app.py
- Role-Based Booking Date Restrictions Spec
- handle_receipt
- format_upcoming_week_appointments
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- button_handler
- handle_text
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec

## God Nodes (most connected - your core abstractions)
1. `button_handler()` - 27 edges
2. `get_connection()` - 19 edges
3. `get_main_menu_keyboard()` - 15 edges
4. `handle_text()` - 13 edges
5. `add_confirmed_appointment()` - 13 edges
6. `format_upcoming_week_appointments()` - 10 edges
7. `get_upcoming_days()` - 9 edges
8. `get_appointment()` - 9 edges
9. `setup_database()` - 8 edges
10. `TestDatabaseWeeklyAppointments` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Task 1: Update `get_upcoming_days` to Support Role-Based Offsets` --references--> `get_upcoming_days()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-role-based-date-restrictions.md → main.py
- `Task 2: Implement Admin Direct Booking Flow in `handle_text`` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → main.py
- `Task 2: Implement Admin Direct Booking Flow in `handle_text`` --references--> `get_main_menu_keyboard()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → main.py
- `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` --references--> `button_handler()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → main.py

## Import Cycles
- None detected.

## Communities (11 total, 0 thin omitted)

### Community 0 - "database.py"
Cohesion: 0.12
Nodes (10): add_pending_appointment(), delete_appointment(), get_all_confirmed_appointments(), get_booked_times(), get_connection(), get_upcoming_week_confirmed_appointments(), setup_database(), update_appointment_status() (+2 more)

### Community 1 - "get_upcoming_days"
Cohesion: 0.21
Nodes (8): Global Constraints, Review Focus, Role-Based Booking Date Restrictions Implementation Plan, Task 1: Update `get_upcoming_days` to Support Role-Based Offsets, Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_upcoming_days(), TestRoleBasedDates

### Community 2 - "app.py"
Cohesion: 0.15
Nodes (9): about(), booking(), get_1405_working_days(), get_available_hours(), get_db_connection(), send_receipt_to_telegram(), setup_web_user(), get_upcoming_week_appointments() (+1 more)

### Community 3 - "Role-Based Booking Date Restrictions Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, Role-Based Booking Date Restrictions Spec

### Community 4 - "handle_receipt"
Cohesion: 0.19
Nodes (11): add_user(), Task 1: Add Datetime Parsing and Cancellation Eligibility Helper, can_cancel_appointment(), error_handler(), get_current_jalali_datetime(), handle_receipt(), handle_text(), main() (+3 more)

### Community 5 - "format_upcoming_week_appointments"
Cohesion: 0.11
Nodes (11): Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, Admin Direct Booking Flow Spec, Goal (+3 more)

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "button_handler"
Cohesion: 0.14
Nodes (15): get_user_confirmed_appointments_for_week(), Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan, Global Constraints, Review Focus, Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, Global Constraints, Review Focus (+7 more)

### Community 8 - "handle_text"
Cohesion: 0.12
Nodes (10): add_confirmed_appointment(), get_appointment(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub (+2 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `button_handler()` connect `button_handler` to `database.py`, `get_upcoming_days`, `app.py`, `handle_receipt`, `format_upcoming_week_appointments`, `handle_text`?**
  _High betweenness centrality (0.216) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `button_handler()` (e.g. with `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`button_handler()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `database.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12333333333333334 - nodes in this community are weakly interconnected._
- **Why does `get_connection()` connect `database.py` to `app.py`, `handle_receipt`, `format_upcoming_week_appointments`, `button_handler`, `handle_text`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `get_main_menu_keyboard()` (e.g. with `Task 2: Implement Admin Direct Booking Flow in `handle_text`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`get_main_menu_keyboard()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14838709677419354 - nodes in this community are weakly interconnected._
- **Why does `setup_database()` connect `database.py` to `handle_text`, `format_upcoming_week_appointments`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._