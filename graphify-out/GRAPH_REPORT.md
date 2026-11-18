# Graph Report - psychology_bot  (2026-11-18)

## Corpus Check
- 55 files · ~48,328 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 5, .service 5, .example 1)

## Summary
- 743 nodes · 1484 edges · 52 communities (38 shown, 14 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 126 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `259a577e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- database.py
- get_upcoming_days
- TestValidation
- Role-Based Booking Date Restrictions Spec
- get_appointment
- Handled Appointment Workflow Design Spec
- Admin Workflow Post-Decision Reset & Weekly Schedule Spec
- main.py
- TestBotModularHandlers
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec
- handle_text
- conftest.py
- get_upcoming_working_days
- `devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer)
- `security-privacy-auditor` (AppSec & Healthcare PII Guardian)
- `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)
- `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)
- Sub-Agent Task Mapping
- TestSecuritySecretsAndPII
- TestRemindersAndReports
- TestIntegrationEdgeCases
- TestWebRoutes
- TestDatabaseWeeklyAppointments
- bot
- steps
- Psychology Clinic Bot & Web Service — VPS Deployment Guide
- TestAdminWorkflow
- TestCheckoutTimeout
- `clinic-swarm-coordinator` (Master Multi-Agent Swarm Orchestrator)
- get_user_confirmed_appointments_for_week
- Review Focus
- TestDevOpsDeployment
- Other Admin Approval Workflow Design Spec
- setup_database
- Psychology Clinic Bot and Web Reservation System
- Admin Direct Booking Implementation Plan
- button_handler
- clinic-swarm-coordinator.md
- SlotAlreadyBookedError
- add_pending_appointment
- get_main_menu_keyboard
- Handled Appointment Workflow Implementation Plan
- admin_view_pending_callback
- app.py
- daily_report.py
- can_cancel_appointment
- TestConcurrencyDoubleBooking
- booking.js
- none_callback
- setup_root_services.sh

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 74 edges
2. `button_handler()` - 53 edges
3. `get_appointment()` - 33 edges
4. `main()` - 28 edges
5. `add_confirmed_appointment()` - 25 edges
6. `get_upcoming_working_days()` - 22 edges
7. `get_main_menu_keyboard()` - 22 edges
8. `handle_text()` - 21 edges
9. `setup_database()` - 21 edges
10. `add_pending_appointment()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Task 1: Add `add_confirmed_appointment` Helper to Database` --references--> `add_confirmed_appointment()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-direct-booking.md → database.py
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-11-handled-appointment-workflow-spec.md → main.py
- `Goals` --references--> `format_upcoming_week_appointments()`  [INFERRED]
  docs/superpowers/specs/2026-11-14-other-admin-approval-workflow-spec.md → main.py
- `Core Capabilities & Operational Scope` --references--> `main()`  [INFERRED]
  .agents/skills/devops-vps-guardian/SKILL.md → main.py

## Import Cycles
- None detected.

## Communities (52 total, 14 thin omitted)

### Community 0 - "database.py"
Cohesion: 0.09
Nodes (11): booking(), get_available_hours(), is_appointment_past(), normalize_digits(), now_jalali(), validate_booking_input(), validate_booking_request(), delete_appointment() (+3 more)

### Community 1 - "get_upcoming_days"
Cohesion: 0.21
Nodes (8): Global Constraints, Review Focus, Role-Based Booking Date Restrictions Implementation Plan, Task 1: Update `get_upcoming_days` to Support Role-Based Offsets, Task 2: Integrate Date Restrictions in Booking Flow and Callback Guard, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, get_upcoming_days(), TestRoleBasedDates

### Community 3 - "Role-Based Booking Date Restrictions Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, Role-Based Booking Date Restrictions Spec

### Community 4 - "get_appointment"
Cohesion: 0.11
Nodes (4): add_confirmed_appointment(), get_appointment(), TestCancellationPolicyIntegration, TestUserCancellation

### Community 5 - "Handled Appointment Workflow Design Spec"
Cohesion: 0.25
Nodes (7): Approaches Considered, Constraints, Context & Problem, Goals, Handled Appointment Workflow Design Spec, Intent, Non-Goals

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "main.py"
Cohesion: 0.21
Nodes (20): get_all_confirmed_appointments(), admin_confirmed_list_callback(), admin_delete_callback(), admin_panel_callback(), admin_pending_list_callback(), admin_weekly_schedule_callback(), book_appointment_callback(), cancel_checkout_timeout_job() (+12 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

### Community 11 - "handle_text"
Cohesion: 0.19
Nodes (5): add_user(), handle_receipt(), handle_text(), is_booking_session_expired(), TestBotWorkflowFixes

### Community 12 - "conftest.py"
Cohesion: 0.10
Nodes (6): flask_client(), isolated_db(), IsolatedDb, mock_telegram_bot(), mock_telegram_context(), test_pytest_fixture_temporal_and_security()

### Community 13 - "get_upcoming_working_days"
Cohesion: 0.06
Nodes (9): get_1405_working_days(), get_1405_working_days(), get_upcoming_working_days(), _create_test_image(), test_pytest_fixture_concurrency_web(), _create_dummy_image(), test_pytest_fixture_web_booking_persian_flow(), TestTemporalJalaliCalendar (+1 more)

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

### Community 23 - "TestDatabaseWeeklyAppointments"
Cohesion: 0.16
Nodes (4): get_appointment_by_id(), get_upcoming_week_confirmed_appointments(), get_weekly_appointments(), TestDatabaseWeeklyAppointments

### Community 24 - "bot"
Cohesion: 0.08
Nodes (26): build, command, container_name, depends_on, env_file, environment, restart, volumes (+18 more)

### Community 25 - "steps"
Cohesion: 0.11
Nodes (17): jobs, test, name, on, pull_request, push, branches, branches (+9 more)

### Community 26 - "Psychology Clinic Bot & Web Service — VPS Deployment Guide"
Cohesion: 0.17
Nodes (11): 1. System Prerequisites, 2. User & Directory Setup, 3. Environment Configuration, 4. Install & Enable Systemd Units, 5. Verify & Monitor Services, 6. Nginx Reverse Proxy & TLS Configuration, 7. Service Management Cheatsheet, Architecture Overview (+3 more)

### Community 27 - "TestAdminWorkflow"
Cohesion: 0.15
Nodes (5): delete_admin_receipt_messages(), get_admin_receipt_messages(), get_connection(), save_admin_receipt_message(), TestAdminWorkflow

### Community 29 - "`clinic-swarm-coordinator` (Master Multi-Agent Swarm Orchestrator)"
Cohesion: 0.25
Nodes (7): `clinic-swarm-coordinator` (Master Multi-Agent Swarm Orchestrator), Mission, Phase A: Parallel Read-Only Discovery Swarm, Phase B: Strict File-Ownership Handoff Swarm, Swarm Circuit Breaker (Self-Healing Protocol), The Two-Phase Hybrid Swarm Protocol, Verification Checklist

### Community 30 - "get_user_confirmed_appointments_for_week"
Cohesion: 0.28
Nodes (7): get_user_confirmed_appointments_for_week(), Global Constraints, Review Focus, Task 1: Add User Weekly Confirmed Appointments Query to Database, Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, User Appointment Cancellation Implementation Plan

### Community 31 - "Review Focus"
Cohesion: 0.33
Nodes (5): Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 33 - "Other Admin Approval Workflow Design Spec"
Cohesion: 0.22
Nodes (8): Bot Flow Updates, Constraints, Context & Problem, Data Model & Interfaces, Goals, Intent, Non-Goals, Other Admin Approval Workflow Design Spec

### Community 34 - "setup_database"
Cohesion: 0.07
Nodes (8): init_db(), setup_database(), Global Constraints, Other Admin Approval Workflow Implementation Plan, Review Focus, Task 1: Add `admin_receipt_messages` Table and Database Helpers, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, TestAdminDirectBooking

### Community 35 - "Psychology Clinic Bot and Web Reservation System"
Cohesion: 0.20
Nodes (9): Docker Deployment, Environment Variables, Leaked Secret Remediation with git-filter-repo, Psychology Clinic Bot and Web Reservation System, Security and Privacy Guardrails, Service Installation, System Architecture, Testing & Quality Assurance (+1 more)

### Community 36 - "Admin Direct Booking Implementation Plan"
Cohesion: 0.33
Nodes (5): Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 37 - "button_handler"
Cohesion: 0.15
Nodes (7): Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan, Global Constraints, Review Focus, Task 2: Integrate Expired Button Hiding and 48-Hour Restriction Callback, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, button_handler(), TestRoleBasedDatesIntegration

### Community 40 - "add_pending_appointment"
Cohesion: 0.12
Nodes (7): add_pending_appointment(), expire_stale_pending_appointments(), get_user_appointments(), test_pytest_fixture_concurrency_database(), attempt(), test_pytest_fixture_admin_approval_and_multi_admin_dispatch(), _run()

### Community 41 - "get_main_menu_keyboard"
Cohesion: 0.24
Nodes (11): Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 1: Extract `complete_admin_review_session` and Update Already-Handled Branch, Task 2: Track Receipt Messages and Implement Other Admin Cleanup on Approval, Admin Direct Booking Flow Spec, Goal, Requirements, admin_review_callback() (+3 more)

### Community 42 - "Handled Appointment Workflow Implementation Plan"
Cohesion: 0.40
Nodes (4): Global Constraints, Handled Appointment Workflow Implementation Plan, Review Focus, Task 2: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 44 - "admin_view_pending_callback"
Cohesion: 0.18
Nodes (3): admin_view_pending_callback(), safe_edit_message(), safe_edit_review_caption()

### Community 45 - "app.py"
Cohesion: 0.06
Nodes (29): `bot-web-core-engineer` (Unified Domain Logic, Flask & Telegram Bot Architect), Core Capabilities & Operational Scope, Mission, Verification Checklist, about(), admin_approve(), admin_cancel(), admin_dashboard() (+21 more)

### Community 46 - "daily_report.py"
Cohesion: 0.27
Nodes (4): get_upcoming_week_appointments(), send_daily_report(), send_email(), send_telegram_broadcast()

### Community 47 - "can_cancel_appointment"
Cohesion: 0.43
Nodes (5): Task 1: Add Datetime Parsing and Cancellation Eligibility Helper, can_cancel_appointment(), get_current_jalali_datetime(), parse_appointment_datetime(), TestCancellationPolicyHelpers

### Community 48 - "TestConcurrencyDoubleBooking"
Cohesion: 0.18
Nodes (3): TestConcurrencyDoubleBooking, confirmed_attempt(), book_attempt()

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `TestAdminWorkflow` to `database.py`, `get_appointment`, `main.py`, `handle_text`, `conftest.py`, `get_upcoming_working_days`, `TestRemindersAndReports`, `TestIntegrationEdgeCases`, `TestDatabaseWeeklyAppointments`, `TestCheckoutTimeout`, `get_user_confirmed_appointments_for_week`, `setup_database`, `SlotAlreadyBookedError`, `add_pending_appointment`, `.test_unauthorized_admin_approval_blocked`, `admin_view_pending_callback`, `app.py`, `daily_report.py`, `TestConcurrencyDoubleBooking`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `button_handler()` (e.g. with `Core Capabilities & Operational Scope` and `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py``) actually correct?**
  _`button_handler()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `database.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09036658141517477 - nodes in this community are weakly interconnected._
- **Why does `button_handler()` connect `button_handler` to `get_upcoming_days`, `setup_database`, `Other Admin Approval Workflow Design Spec`, `get_appointment`, `main.py`, `add_pending_appointment`, `get_main_menu_keyboard`, `.test_unauthorized_admin_approval_blocked`, `admin_view_pending_callback`, `app.py`, `none_callback`, `TestIntegrationEdgeCases`, `TestAdminWorkflow`, `get_user_confirmed_appointments_for_week`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `main()` (e.g. with `Core Capabilities & Operational Scope` and `admin_confirmed_list_callback()`) actually correct?**
  _`main()` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Should `TestValidation` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `setup_database()` connect `setup_database` to `database.py`, `main.py`, `TestBotModularHandlers`, `conftest.py`, `TestConcurrencyDoubleBooking`, `TestRemindersAndReports`, `TestIntegrationEdgeCases`, `TestWebRoutes`, `TestDatabaseWeeklyAppointments`, `TestAdminWorkflow`, `TestCheckoutTimeout`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._