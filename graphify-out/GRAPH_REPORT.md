# Graph Report - psychology_bot  (2026-11-14)

## Corpus Check
- 32 files · ~20,831 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 252 nodes · 475 edges · 18 communities
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 69 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7acf0b21`
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
- Sub-Agent Task Mapping
- User Appointment Cancellation Feature Spec
- Appointment Cancellation Time Restrictions & Button Expiration Spec
- main.py
- get_connection
- User Appointment Cancellation Implementation Plan
- Review Focus
- `security-privacy-auditor` (AppSec & Healthcare PII Guardian)
- `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)
- `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)

## God Nodes (most connected - your core abstractions)
1. `button_handler()` - 44 edges
2. `get_connection()` - 28 edges
3. `get_main_menu_keyboard()` - 17 edges
4. `format_upcoming_week_appointments()` - 15 edges
5. `TestAdminWorkflow` - 14 edges
6. `add_confirmed_appointment()` - 13 edges
7. `handle_text()` - 13 edges
8. `handle_receipt()` - 12 edges
9. `Sub-Agent Task Mapping` - 11 edges
10. `get_appointment()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Task 1: Add Weekly Confirmed Appointments Query to Database` --references--> `get_upcoming_week_confirmed_appointments()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-admin-workflow-reset.md → database.py
- `Task 1: Add User Weekly Confirmed Appointments Query to Database` --references--> `get_user_confirmed_appointments_for_week()`  [INFERRED]
  docs/superpowers/plans/2026-11-11-user-cancellation.md → database.py
- `Core Capabilities & Operational Scope` --references--> `button_handler()`  [INFERRED]
  .agents/skills/bot-web-core-engineer/SKILL.md → main.py
- `Core Capabilities & Operational Scope` --references--> `main()`  [INFERRED]
  .agents/skills/devops-vps-guardian/SKILL.md → main.py
- `Task 6: Flask Route Separation & Modular Telegram Callback Routing` --references--> `button_handler()`  [INFERRED]
  docs/superpowers/plans/2026-11-14-comprehensive-18-point-architecture-plan.md → main.py

## Import Cycles
- None detected.

## Communities (18 total, 0 thin omitted)

### Community 0 - "button_handler"
Cohesion: 0.13
Nodes (6): delete_appointment(), get_appointment(), Task 2: Implement Dynamic Cancellation Buttons and Callback Handler in `main.py`, button_handler(), TestAdminWorkflow, TestRoleBasedDatesIntegration

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
Cohesion: 0.08
Nodes (17): add_confirmed_appointment(), Admin Direct Booking Implementation Plan, Global Constraints, Review Focus, Task 1: Add `add_confirmed_appointment` Helper to Database, Task 2: Implement Admin Direct Booking Flow in `handle_text`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan (+9 more)

### Community 5 - "format_upcoming_week_appointments"
Cohesion: 0.09
Nodes (18): Global Constraints, Handled Appointment Workflow Implementation Plan, Review Focus, Task 1: Extract `complete_admin_review_session` and Update Already-Handled Branch, Task 2: Full Verification, Knowledge Graph Update, and Push to GitHub, Admin Direct Booking Flow Spec, Goal, Requirements (+10 more)

### Community 6 - "Admin Workflow Post-Decision Reset & Weekly Schedule Spec"
Cohesion: 0.40
Nodes (4): Admin Workflow Post-Decision Reset & Weekly Schedule Spec, Background & Problem, Goal, Requirements

### Community 7 - "handle_receipt"
Cohesion: 0.10
Nodes (17): Core Capabilities & Operational Scope, `devops-vps-guardian` (CI/CD, Systemd, Docker & Repo Hygiene Engineer), Mission, Verification Checklist, Global Constraints, Other Admin Approval Workflow Implementation Plan, Bot Flow Updates, Constraints (+9 more)

### Community 8 - "Sub-Agent Task Mapping"
Cohesion: 0.14
Nodes (13): Comprehensive 18-Point Architecture & Hardening Implementation Plan, Global Constraints, Review Focus, Sub-Agent Task Mapping, Task 10: Production Deployment Hardening, Systemd, Docker & CI/CD, Task 1: SQLite WAL Mode, Pragmas & Engine-Level Slot Uniqueness, Task 2: Dynamic Rolling Jalali Calendar & Soft-Delete Governance, Task 3: Secrets Management, .env Loading & Zero-PII Logging (+5 more)

### Community 9 - "User Appointment Cancellation Feature Spec"
Cohesion: 0.50
Nodes (3): Goal, Requirements, User Appointment Cancellation Feature Spec

### Community 10 - "Appointment Cancellation Time Restrictions & Button Expiration Spec"
Cohesion: 0.50
Nodes (3): Appointment Cancellation Time Restrictions & Button Expiration Spec, Goal, Requirements

### Community 11 - "main.py"
Cohesion: 0.23
Nodes (5): Task 1: Add Datetime Parsing and Cancellation Eligibility Helper, can_cancel_appointment(), get_current_jalali_datetime(), parse_appointment_datetime(), TestCancellationPolicyHelpers

### Community 12 - "get_connection"
Cohesion: 0.13
Nodes (17): add_pending_appointment(), add_user(), delete_admin_receipt_messages(), get_admin_receipt_messages(), get_all_confirmed_appointments(), get_booked_times(), get_connection(), get_upcoming_week_confirmed_appointments() (+9 more)

### Community 13 - "User Appointment Cancellation Implementation Plan"
Cohesion: 0.33
Nodes (5): Global Constraints, Review Focus, Task 1: Add User Weekly Confirmed Appointments Query to Database, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub, User Appointment Cancellation Implementation Plan

### Community 14 - "Review Focus"
Cohesion: 0.29
Nodes (6): Admin Workflow Post-Decision Reset & Weekly Schedule Implementation Plan, Global Constraints, Review Focus, Task 1: Add Weekly Confirmed Appointments Query to Database, Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py`, Task 3: Full Verification, Knowledge Graph Update, and Push to GitHub

### Community 15 - "`security-privacy-auditor` (AppSec & Healthcare PII Guardian)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `security-privacy-auditor` (AppSec & Healthcare PII Guardian), Verification Checklist

### Community 16 - "`sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `sqlite-temporal-architect` (Concurrency, Schema & Jalali Timezone Specialist), Verification Checklist

### Community 17 - "`tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer)"
Cohesion: 0.40
Nodes (4): Core Capabilities & Operational Scope, Mission, `tdd-qa-verifier` (Pytest & Superpowers Red-Green-Refactor Enforcer), Verification Checklist

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `button_handler()` connect `button_handler` to `get_upcoming_days`, `app.py`, `add_confirmed_appointment`, `format_upcoming_week_appointments`, `handle_receipt`, `main.py`, `get_connection`, `User Appointment Cancellation Implementation Plan`, `Review Focus`?**
  _High betweenness centrality (0.348) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `button_handler()` (e.g. with `Core Capabilities & Operational Scope` and `Task 2: Implement Weekly Schedule Formatter and Admin Flow Reset in `main.py``) actually correct?**
  _`button_handler()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Should `button_handler` be split into smaller, more focused modules?**
  _Cohesion score 0.13405797101449277 - nodes in this community are weakly interconnected._
- **Why does `format_upcoming_week_appointments()` connect `format_upcoming_week_appointments` to `button_handler`, `add_confirmed_appointment`, `main.py`, `get_connection`, `Review Focus`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `get_main_menu_keyboard()` (e.g. with `Task 2: Implement Admin Direct Booking Flow in `handle_text`` and `Appointment Cancellation Time Restrictions & Button Expiration Implementation Plan`) actually correct?**
  _`get_main_menu_keyboard()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12307692307692308 - nodes in this community are weakly interconnected._
- **Why does `Task 6: Flask Route Separation & Modular Telegram Callback Routing` connect `app.py` to `Sub-Agent Task Mapping`, `button_handler`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._