# Graph Report - psychology_bot  (2026-11-14)

## Corpus Check
- 34 files · ~22,224 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 281 nodes · 543 edges · 18 communities (17 shown, 1 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 71 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fdf812e1`
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
- handle_text
- Sub-Agent Task Mapping
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec
- setup_database
- get_connection
- get_upcoming_working_days
- Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan
- `security-privacy-auditor` (AppSec & Healthcare PII Guardian)
- `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)
- `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)

## God Nodes (most connected - your core abstractions)
1. `button_handler()` - 44 edges
2. `get_connection()` - 32 edges
3. `add_confirmed_appointment()` - 17 edges
4. `get_main_menu_keyboard()` - 17 edges
5. `format_upcoming_week_appointments()` - 15 edges
6. `TestAdminWorkflow` - 14 edges
7. `handle_text()` - 13 edges
8. `get_appointment()` - 12 edges
9. `handle_receipt()` - 12 edges
10. `setup_database()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Task 1: Add `admin_receipt_messages` Table and Database Helpers` --references--> `setup_database()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-other-admin-approval-workflow.md → database.py
- `Task 1: Add `add_confirmed_appointment` Helper to Database` --references--> `add_confirmed_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → database.py
- `Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py`` --references--> `get_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-user-cancellation.md → database.py
- `Task 1: Add User Weekly Confirmed Appointments Query to Database` --references--> `get_user_confirmed_appointments_for_week()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-user-cancellation.md → database.py

## Import Cycles
- None detected.

## Communities (18 total, 1 thin omitted)

### Community 0 - "database.py"
Cohesion: 0.21
Nodes (5): Task 1: Add Datetime Parsing and Cancellation Eligibility Helper, can_cancel_appointment(), get_current_jalali_datetime(), parse_appointment_datetime(), TestCancellationPolicyHelpers

### Community 1 - "get_upcoming_days"
Cohesion: 0.21
Nodes (8): Global Constraints, Review Focus, Role-Based Booking Date Restrictions Implementation Plan, Task 1: Update `get_upcoming_days` to Support Role-Based Offsets, Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_upcoming_days(), TestRoleBasedDates

### Community 2 - "app.py"
Cohesion: 0.12
Nodes (15): `bot-web-core-engineer` (Unified Domain Logic, Flask & Telegram Bot Architect), Core Capabilities & Operational Scope, Mission, Verification Checklist, about(), booking(), get_1405_working_days(), get_available_hours() (+7 more)

### Community 3 - "Role-Based Booking Date Restrictions Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, Role-Based Booking Date Restrictions Spec

### Community 4 - "add_confirmed_appointment"
Cohesion: 0.10
Nodes (15): add_confirmed_appointment(), add_pending_appointment(), expire_stale_pending_appointments(), get_appointment(), SlotAlreadyBookedError, Admin Direct Booking Implementation Plan, Global Constraints, Review Focus (+7 more)

### Community 5 - "format_upcoming_week_appointments"
Cohesion: 0.07
Nodes (24): Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, Global Constraints, Handled Appointment Workflow Implementation Plan (+16 more)

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "handle_text"
Cohesion: 0.09
Nodes (18): Core Capabilities & Operational Scope, `devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer), Mission, Verification Checklist, add_user(), Bot Flow Updates, Constraints, Context & Problem (+10 more)

### Community 8 - "Sub-Agent Task Mapping"
Cohesion: 0.14
Nodes (13): Comprehensive 18-Point Architecture & Hardening Implementation Plan, Global Constraints, Review Focus, Sub-Agent Task Mapping, Task 10: Production Deployment Hardening, Systemd, Docker & CI/CD, Task 1: SQLite WAL Mode, Pragmas & Engine-Level Slot Uniqueness, Task 2: Dynamic Rolling Jalali Calendar & Soft-Delete Governance, Task 3: Secrets Management, .env Loading & Zero-PII Logging (+5 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

### Community 11 - "setup_database"
Cohesion: 0.12
Nodes (6): setup_database(), Global Constraints, Other Admin Approval Workflow Implementation Plan, Review Focus, Task 1: Add `admin_receipt_messages` Table and Database Helpers, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 12 - "get_connection"
Cohesion: 0.09
Nodes (21): delete_admin_receipt_messages(), delete_appointment(), get_admin_receipt_messages(), get_all_confirmed_appointments(), get_booked_times(), get_connection(), get_upcoming_week_confirmed_appointments(), get_user_confirmed_appointments_for_week() (+13 more)

### Community 14 - "Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan"
Cohesion: 0.33
Nodes (5): Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan, Global Constraints, Review Focus, Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 15 - "`security-privacy-auditor` (AppSec & Healthcare PII Guardian)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `security-privacy-auditor` (AppSec & Healthcare PII Guardian), Verification Checklist

### Community 16 - "`sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist), Verification Checklist

### Community 17 - "`tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer), Verification Checklist

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `button_handler()` connect `get_connection` to `database.py`, `get_upcoming_days`, `app.py`, `add_confirmed_appointment`, `format_upcoming_week_appointments`, `handle_text`, `setup_database`, `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`?**
  _High betweenness centrality (0.321) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `button_handler()` (e.g. with `Core Capabilities & Operational Scope` and `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py``) actually correct?**
  _`button_handler()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12307692307692308 - nodes in this community are weakly interconnected._
- **Why does `format_upcoming_week_appointments()` connect `format_upcoming_week_appointments` to `database.py`, `add_confirmed_appointment`, `get_connection`, `handle_text`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `add_confirmed_appointment()` (e.g. with `Admin Direct Booking Implementation Plan` and `Task 1: Add `add_confirmed_appointment` Helper to Database`) actually correct?**
  _`add_confirmed_appointment()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `add_confirmed_appointment` be split into smaller, more focused modules?**
  _Cohesion score 0.09659090909090909 - nodes in this community are weakly interconnected._
- **Why does `Task 6: Flask Route Separation & Modular Telegram Callback Routing` connect `app.py` to `Sub-Agent Task Mapping`, `get_connection`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._