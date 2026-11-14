# Graph Report - psychology_bot  (2026-11-15)

## Corpus Check
- 44 files · ~32,830 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 3, .example 1, .ini 1)

## Summary
- 501 nodes · 1054 edges · 30 communities (22 shown, 8 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 105 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e4af7c56`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- database.py
- get_upcoming_days
- TestValidation
- Role-Based Booking Date Restrictions Spec
- expire_stale_pending_appointments
- Handled Appointment Workflow Design Spec
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- main.py
- TestIntegrationEdgeCases
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
- TestRemindersAndReports
- TestBotModularHandlers
- TestWebRoutes
- TestDatabaseWeeklyAppointments
- Other Admin Approval Workflow Design Spec
- add_pending_appointment
- save_admin_receipt_message
- get_connection
- get_appointment
- button_handler

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 58 edges
2. `button_handler()` - 48 edges
3. `get_appointment()` - 25 edges
4. `add_confirmed_appointment()` - 22 edges
5. `main()` - 22 edges
6. `get_upcoming_working_days()` - 20 edges
7. `get_main_menu_keyboard()` - 19 edges
8. `setup_database()` - 18 edges
9. `add_pending_appointment()` - 17 edges
10. `format_upcoming_week_appointments()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-11-handled-appointment-workflow-spec.md → main.py
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-14-other-admin-approval-workflow-spec.md → main.py
- `Core Capabilities & Operational Scope` --references--> `main()`  [INFERRED]
  .agents/skills/devops-vps-guardian/SKILL.md → main.py
- `Task 1: Update `get_upcoming_days` to Support Role-Based Offsets` --references--> `get_upcoming_days()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-role-based-date-restrictions.md → main.py
- `Task 1: Add `admin_receipt_messages` Table and Database Helpers` --references--> `setup_database()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-other-admin-approval-workflow.md → database.py

## Import Cycles
- None detected.

## Communities (30 total, 8 thin omitted)

### Community 0 - "database.py"
Cohesion: 0.09
Nodes (14): booking(), get_1405_working_days(), get_available_hours(), get_db_connection(), send_receipt_to_telegram(), setup_web_user(), normalize_digits(), validate_booking_request() (+6 more)

### Community 1 - "get_upcoming_days"
Cohesion: 0.21
Nodes (8): Global Constraints, Review Focus, Role-Based Booking Date Restrictions Implementation Plan, Task 1: Update `get_upcoming_days` to Support Role-Based Offsets, Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_upcoming_days(), TestRoleBasedDates

### Community 3 - "Role-Based Booking Date Restrictions Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, Role-Based Booking Date Restrictions Spec

### Community 4 - "expire_stale_pending_appointments"
Cohesion: 0.18
Nodes (3): add_user(), expire_stale_pending_appointments(), TestStaleAppointmentExpiration

### Community 5 - "Handled Appointment Workflow Design Spec"
Cohesion: 0.25
Nodes (7): Approaches Considered, Constraints, Context & Problem, Goals, Handled Appointment Workflow Design Spec, Intent, Non-Goals

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "main.py"
Cohesion: 0.06
Nodes (47): add_confirmed_appointment(), delete_appointment(), get_all_confirmed_appointments(), get_booked_times(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database (+39 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

### Community 11 - "setup_database"
Cohesion: 0.07
Nodes (6): setup_database(), Task 1: Add `admin_receipt_messages` Table and Database Helpers, TestAdminDirectBooking, TestConcurrencyDoubleBooking, confirmed_attempt(), book_attempt()

### Community 12 - "conftest.py"
Cohesion: 0.10
Nodes (6): flask_client(), isolated_db(), IsolatedDb, mock_telegram_bot(), mock_telegram_context(), test_pytest_fixture_temporal_and_security()

### Community 13 - "get_upcoming_working_days"
Cohesion: 0.08
Nodes (7): get_upcoming_working_days(), _create_test_image(), test_pytest_fixture_concurrency_web(), _create_dummy_image(), test_pytest_fixture_web_booking_persian_flow(), TestTemporalJalaliCalendar, TestUploadSecurityAndRBAC

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
Cohesion: 0.09
Nodes (20): `bot-web-core-engineer` (Unified Domain Logic, Flask & Telegram Bot Architect), Core Capabilities & Operational Scope, Mission, Verification Checklist, about(), home(), Comprehensive 18-Point Architecture & Hardening Implementation Plan, Global Constraints (+12 more)

### Community 23 - "TestDatabaseWeeklyAppointments"
Cohesion: 0.08
Nodes (16): get_upcoming_week_confirmed_appointments(), get_user_confirmed_appointments_for_week(), update_appointment_status(), Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py` (+8 more)

### Community 24 - "Other Admin Approval Workflow Design Spec"
Cohesion: 0.29
Nodes (6): Constraints, Data Model & Interfaces, Goals, Intent, Non-Goals, Other Admin Approval Workflow Design Spec

### Community 25 - "add_pending_appointment"
Cohesion: 0.17
Nodes (6): add_pending_appointment(), SlotAlreadyBookedError, test_pytest_fixture_concurrency_database(), attempt(), test_pytest_fixture_admin_approval_and_multi_admin_dispatch(), _run()

### Community 26 - "save_admin_receipt_message"
Cohesion: 0.23
Nodes (10): delete_admin_receipt_messages(), save_admin_receipt_message(), Global Constraints, Other Admin Approval Workflow Implementation Plan, Review Focus, Task 2: Track Receipt Messages and Implement Other Admin Cleanup on Approval, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, Bot Flow Updates (+2 more)

### Community 27 - "get_connection"
Cohesion: 0.30
Nodes (3): get_admin_receipt_messages(), get_connection(), TestAdminWorkflow

## Knowledge Gaps
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `database.py`, `expire_stale_pending_appointments`, `main.py`, `TestIntegrationEdgeCases`, `setup_database`, `conftest.py`, `get_upcoming_working_days`, `TestRemindersAndReports`, `TestDatabaseWeeklyAppointments`, `add_pending_appointment`, `save_admin_receipt_message`, `get_appointment`?**
  _High betweenness centrality (0.202) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `button_handler()` (e.g. with `Core Capabilities & Operational Scope` and `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py``) actually correct?**
  _`button_handler()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `database.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08552388004442799 - nodes in this community are weakly interconnected._
- **Why does `button_handler()` connect `button_handler` to `get_upcoming_days`, `main.py`, `TestIntegrationEdgeCases`, `Sub-Agent Task Mapping`, `TestBotModularHandlers`, `TestDatabaseWeeklyAppointments`, `add_pending_appointment`, `save_admin_receipt_message`, `get_connection`, `get_appointment`?**
  _High betweenness centrality (0.165) - this node is a cross-community bridge._
- **Should `TestValidation` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `setup_database()` connect `setup_database` to `database.py`, `expire_stale_pending_appointments`, `main.py`, `TestIntegrationEdgeCases`, `conftest.py`, `TestRemindersAndReports`, `TestBotModularHandlers`, `TestWebRoutes`, `TestDatabaseWeeklyAppointments`, `get_connection`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06103286384976526 - nodes in this community are weakly interconnected._