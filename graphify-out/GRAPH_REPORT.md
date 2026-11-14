# Graph Report - psychology_bot  (2026-11-14)

## Corpus Check
- 35 files · ~22,766 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 294 nodes · 567 edges · 20 communities (16 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 71 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7eb831ce`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- database.py
- get_upcoming_days
- app.py
- Role-Based Booking Date Restrictions Spec
- add_confirmed_appointment
- format_upcoming_week_appointments
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- `devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer)
- TestDatabaseWeeklyAppointments
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec
- setup_database
- get_connection
- get_upcoming_working_days
- can_cancel_appointment
- `security-privacy-auditor` (AppSec & Healthcare PII Guardian)
- `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)
- `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)
- SlotAlreadyBookedError
- TestSecuritySecretsAndPII

## God Nodes (most connected - your core abstractions)
1. `button_handler()` - 44 edges
2. `get_connection()` - 33 edges
3. `add_confirmed_appointment()` - 17 edges
4. `get_main_menu_keyboard()` - 17 edges
5. `format_upcoming_week_appointments()` - 15 edges
6. `TestAdminWorkflow` - 14 edges
7. `handle_text()` - 13 edges
8. `get_appointment()` - 12 edges
9. `handle_receipt()` - 12 edges
10. `setup_database()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add `admin_receipt_messages` Table and Database Helpers` --references--> `setup_database()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-other-admin-approval-workflow.md → database.py
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-14-other-admin-approval-workflow-spec.md → main.py
- `Core Capabilities & Operational Scope` --references--> `main()`  [INFERRED]
  .agents/skills/devops-vps-guardian/SKILL.md → main.py
- `Task 1: Add `add_confirmed_appointment` Helper to Database` --references--> `add_confirmed_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → database.py
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py

## Import Cycles
- None detected.

## Communities (20 total, 4 thin omitted)

### Community 1 - "get_upcoming_days"
Cohesion: 0.21
Nodes (8): Global Constraints, Review Focus, Role-Based Booking Date Restrictions Implementation Plan, Task 1: Update `get_upcoming_days` to Support Role-Based Offsets, Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_upcoming_days(), TestRoleBasedDates

### Community 2 - "app.py"
Cohesion: 0.08
Nodes (26): `bot-web-core-engineer` (Unified Domain Logic, Flask & Telegram Bot Architect), Core Capabilities & Operational Scope, Mission, Verification Checklist, about(), booking(), get_1405_working_days(), get_available_hours() (+18 more)

### Community 3 - "Role-Based Booking Date Restrictions Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, Role-Based Booking Date Restrictions Spec

### Community 4 - "add_confirmed_appointment"
Cohesion: 0.11
Nodes (15): add_confirmed_appointment(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, error_handler() (+7 more)

### Community 5 - "format_upcoming_week_appointments"
Cohesion: 0.10
Nodes (17): Global Constraints, Handled Appointment Workflow Implementation Plan, Review Focus, Task 1: Extract `complete_admin_review_session` and Update Already-Handled Branch, Task 2: Full Verification, Knowledge Graph Update, and Push to GitHub, Admin Direct Booking Flow Spec, Goal, Requirements (+9 more)

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "`devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, `devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer), Mission, Verification Checklist

### Community 8 - "TestDatabaseWeeklyAppointments"
Cohesion: 0.09
Nodes (14): get_upcoming_week_confirmed_appointments(), get_user_confirmed_appointments_for_week(), Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub (+6 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

### Community 12 - "get_connection"
Cohesion: 0.08
Nodes (30): add_pending_appointment(), add_user(), delete_admin_receipt_messages(), delete_appointment(), get_admin_receipt_messages(), get_all_confirmed_appointments(), get_appointment(), get_booked_times() (+22 more)

### Community 14 - "can_cancel_appointment"
Cohesion: 0.19
Nodes (10): Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan, Global Constraints, Review Focus, Task 1: Add Datetime Parsing and Cancellation Eligibility Helper, Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, can_cancel_appointment(), get_current_jalali_datetime() (+2 more)

### Community 15 - "`security-privacy-auditor` (AppSec & Healthcare PII Guardian)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `security-privacy-auditor` (AppSec & Healthcare PII Guardian), Verification Checklist

### Community 16 - "`sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist), Verification Checklist

### Community 17 - "`tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer), Verification Checklist

### Community 18 - "SlotAlreadyBookedError"
Cohesion: 0.18
Nodes (3): expire_stale_pending_appointments(), SlotAlreadyBookedError, TestStaleAppointmentExpiration

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `button_handler()` connect `get_connection` to `database.py`, `get_upcoming_days`, `app.py`, `add_confirmed_appointment`, `format_upcoming_week_appointments`, `TestDatabaseWeeklyAppointments`, `can_cancel_appointment`?**
  _High betweenness centrality (0.299) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `button_handler()` (e.g. with `Core Capabilities & Operational Scope` and `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py``) actually correct?**
  _`button_handler()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08021390374331551 - nodes in this community are weakly interconnected._
- **Why does `format_upcoming_week_appointments()` connect `format_upcoming_week_appointments` to `TestDatabaseWeeklyAppointments`, `database.py`, `add_confirmed_appointment`, `get_connection`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `add_confirmed_appointment()` (e.g. with `Admin Direct Booking Implementation Plan` and `Task 1: Add `add_confirmed_appointment` Helper to Database`) actually correct?**
  _`add_confirmed_appointment()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `add_confirmed_appointment` be split into smaller, more focused modules?**
  _Cohesion score 0.10837438423645321 - nodes in this community are weakly interconnected._
- **Why does `Task 6: Flask Route Separation & Modular Telegram Callback Routing` connect `app.py` to `get_connection`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._