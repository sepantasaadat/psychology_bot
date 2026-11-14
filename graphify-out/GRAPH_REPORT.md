# Graph Report - psychology_bot  (2026-11-15)

## Corpus Check
- 43 files · ~30,219 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 3, .example 1, .ini 1)

## Summary
- 467 nodes · 960 edges · 27 communities (23 shown, 4 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 103 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2924ea4e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- database.py
- get_upcoming_days
- app.py
- Role-Based Booking Date Restrictions Spec
- add_confirmed_appointment
- Handled Appointment Workflow Design Spec
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- main.py
- Review Focus
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec
- setup_database
- conftest.py
- get_upcoming_working_days
- `devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer)
- `security-privacy-auditor` (AppSec & Healthcare PII Guardian)
- `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)
- `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)
- Sub-Agent Task Mapping
- TestSecuritySecretsAndPII
- get_connection
- TestBotModularHandlers
- daily_report.py
- get_user_confirmed_appointments_for_week
- Other Admin Approval Workflow Design Spec
- Handled Appointment Workflow Implementation Plan
- Admin Direct Booking Flow Spec

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 56 edges
2. `button_handler()` - 44 edges
3. `main()` - 22 edges
4. `add_confirmed_appointment()` - 19 edges
5. `get_main_menu_keyboard()` - 19 edges
6. `setup_database()` - 17 edges
7. `get_upcoming_working_days()` - 15 edges
8. `get_appointment()` - 15 edges
9. `format_upcoming_week_appointments()` - 15 edges
10. `TestAdminWorkflow` - 14 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add `admin_receipt_messages` Table and Database Helpers` --references--> `setup_database()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-other-admin-approval-workflow.md → database.py
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-11-handled-appointment-workflow-spec.md → main.py
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-14-other-admin-approval-workflow-spec.md → main.py
- `Core Capabilities & Operational Scope` --references--> `main()`  [INFERRED]
  .agents/skills/devops-vps-guardian/SKILL.md → main.py

## Import Cycles
- None detected.

## Communities (27 total, 4 thin omitted)

### Community 1 - "get_upcoming_days"
Cohesion: 0.21
Nodes (8): Global Constraints, Review Focus, Role-Based Booking Date Restrictions Implementation Plan, Task 1: Update `get_upcoming_days` to Support Role-Based Offsets, Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_upcoming_days(), TestRoleBasedDates

### Community 2 - "app.py"
Cohesion: 0.07
Nodes (16): `bot-web-core-engineer` (Unified Domain Logic, Flask & Telegram Bot Architect), Core Capabilities & Operational Scope, Mission, Verification Checklist, about(), booking(), get_1405_working_days(), get_available_hours() (+8 more)

### Community 3 - "Role-Based Booking Date Restrictions Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, Role-Based Booking Date Restrictions Spec

### Community 4 - "add_confirmed_appointment"
Cohesion: 0.05
Nodes (17): add_confirmed_appointment(), add_pending_appointment(), expire_stale_pending_appointments(), SlotAlreadyBookedError, Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database (+9 more)

### Community 5 - "Handled Appointment Workflow Design Spec"
Cohesion: 0.25
Nodes (7): Approaches Considered, Constraints, Context & Problem, Goals, Handled Appointment Workflow Design Spec, Intent, Non-Goals

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "main.py"
Cohesion: 0.09
Nodes (41): add_user(), delete_appointment(), Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan, Global Constraints, Review Focus, Task 1: Add Datetime Parsing and Cancellation Eligibility Helper (+33 more)

### Community 8 - "Review Focus"
Cohesion: 0.33
Nodes (5): Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

### Community 11 - "setup_database"
Cohesion: 0.07
Nodes (4): setup_database(), TestAdminDirectBooking, captured_templates(), TestWebRoutes

### Community 12 - "conftest.py"
Cohesion: 0.11
Nodes (5): flask_client(), isolated_db(), IsolatedDb, mock_telegram_bot(), mock_telegram_context()

### Community 13 - "get_upcoming_working_days"
Cohesion: 0.10
Nodes (5): get_upcoming_working_days(), _create_test_image(), test_pytest_fixture_concurrency_web(), TestTemporalJalaliCalendar, TestUploadSecurityAndRBAC

### Community 14 - "`devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, `devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer), Mission, Verification Checklist

### Community 15 - "`security-privacy-auditor` (AppSec & Healthcare PII Guardian)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `security-privacy-auditor` (AppSec & Healthcare PII Guardian), Verification Checklist

### Community 16 - "`sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist), Verification Checklist

### Community 17 - "`tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer), Verification Checklist

### Community 18 - "Sub-Agent Task Mapping"
Cohesion: 0.14
Nodes (13): Comprehensive 18-Point Architecture & Hardening Implementation Plan, Global Constraints, Review Focus, Sub-Agent Task Mapping, Task 10: Production Deployment Hardening, Systemd, Docker & CI/CD, Task 1: SQLite WAL Mode, Pragmas & Engine-Level Slot Uniqueness, Task 2: Dynamic Rolling Jalali Calendar & Soft-Delete Governance, Task 3: Secrets Management, .env Loading & Zero-PII Logging (+5 more)

### Community 20 - "get_connection"
Cohesion: 0.05
Nodes (17): delete_admin_receipt_messages(), get_admin_receipt_messages(), get_all_confirmed_appointments(), get_appointment(), get_booked_times(), get_connection(), get_upcoming_week_confirmed_appointments(), mark_reminder_as_sent() (+9 more)

### Community 22 - "daily_report.py"
Cohesion: 0.27
Nodes (4): get_upcoming_week_appointments(), send_daily_report(), send_email(), send_telegram_broadcast()

### Community 23 - "get_user_confirmed_appointments_for_week"
Cohesion: 0.32
Nodes (7): get_user_confirmed_appointments_for_week(), Global Constraints, Review Focus, Task 1: Add User Weekly Confirmed Appointments Query to Database, Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, User Appointment Cancellation Implementation Plan

### Community 24 - "Other Admin Approval Workflow Design Spec"
Cohesion: 0.29
Nodes (6): Constraints, Data Model & Interfaces, Goals, Intent, Non-Goals, Other Admin Approval Workflow Design Spec

### Community 25 - "Handled Appointment Workflow Implementation Plan"
Cohesion: 0.40
Nodes (4): Global Constraints, Handled Appointment Workflow Implementation Plan, Review Focus, Task 2: Full Verification, Knowledge Graph Update, and Push to GitHub

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `database.py`, `app.py`, `add_confirmed_appointment`, `main.py`, `setup_database`, `conftest.py`, `get_upcoming_working_days`, `daily_report.py`, `get_user_confirmed_appointments_for_week`?**
  _High betweenness centrality (0.205) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `button_handler()` (e.g. with `Core Capabilities & Operational Scope` and `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py``) actually correct?**
  _`button_handler()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07422402159244265 - nodes in this community are weakly interconnected._
- **Why does `button_handler()` connect `main.py` to `get_upcoming_days`, `app.py`, `add_confirmed_appointment`, `get_connection`, `get_user_confirmed_appointments_for_week`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `main()` (e.g. with `Core Capabilities & Operational Scope` and `admin_delete_callback()`) actually correct?**
  _`main()` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `add_confirmed_appointment` be split into smaller, more focused modules?**
  _Cohesion score 0.05272895467160037 - nodes in this community are weakly interconnected._
- **Why does `setup_database()` connect `setup_database` to `database.py`, `add_confirmed_appointment`, `main.py`, `conftest.py`, `get_connection`, `TestBotModularHandlers`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._