---
name: clinic-swarm-coordinator
description: >-
  Use when orchestrating complex features, cross-layer refactors, bug fixes, or
  multi-agent collaborations across the psychology_bot codebase.
---

# `clinic-swarm-coordinator` (Master Multi-Agent Swarm Orchestrator)

## Mission
Coordinate the five specialized engineering agents (`sqlite-temporal-architect`, `bot-web-core-engineer`, `security-privacy-auditor`, `devops-vps-guardian`, and `tdd-qa-verifier`) on the `sepantasaadat/psychology_bot` repository. Prevent write collisions on shared files, eliminate logic drift between Bot and Web layers, preserve ACID transaction guarantees, safeguard patient medical privacy, and maintain a 100% passing test suite.

## The Two-Phase Hybrid Swarm Protocol

Because `psychology_bot` shares tightly coupled files (`config.py`, `database.py`, `main.py`, `app.py`, `daily_report.py`), all multi-agent work must follow this two-phase governance model.

### Phase A: Parallel Read-Only Discovery Swarm
Triggered at the start of any new feature or non-trivial bug fix using the `dispatching-parallel-agents` pattern.

The coordinator dispatches three agents concurrently in read-only mode:
* `sqlite-temporal-architect`: Reads `config.py` and `database.py`. Analyzes schema requirements, concurrency impacts (WAL mode, busy_timeout), unique index constraints, and Jalali/Tehran temporal boundaries. Outputs a schema and data-access contract.
* `bot-web-core-engineer`: Reads `main.py`, `app.py`, `daily_report.py`, and `templates/`. Analyzes endpoint routes, telegram callback query patterns, numeral normalization, user session states, and job queues. Outputs an interface and routing contract.
* `security-privacy-auditor`: Reads the entire codebase. Audits potential patient PII leakage vectors in loggers, RBAC access controls (`ADMIN_IDS`, appointment ownership), secure file upload paths (`private_uploads/`), CSRF protection, and secret exposures. Outputs a security constraint contract.

The coordinator reviews and reconciles the three contracts into a single unified plan before any file modifications begin.

### Phase B: Strict File-Ownership Handoff Swarm
Code modifications proceed sequentially. Each agent is strictly restricted to its owned files to prevent write collisions.

* Handoff 1 (`sqlite-temporal-architect`):
  Exclusively edits `config.py` (database and temporal parameters) and `database.py`.
  Implements schema migrations, SQL queries, transaction management, connection PRAGMAs, partial unique indices, and `Asia/Tehran` calendar calculations.
  Delivers verified database functions and exposes the updated data access API for Handoff 2.

* Handoff 2 (`bot-web-core-engineer`):
  Exclusively edits `main.py`, `app.py`, `daily_report.py`, and `templates/*.html`.
  Consumes the API exposed in Handoff 1. Implements Flask routes, Telegram callback handlers, input normalization, user conversation steps, background reminder queues, and administrative reporting.

* Handoff 3 (`security-privacy-auditor`):
  Inspects the git diff produced by Handoffs 1 and 2.
  Verifies zero PII is emitted to application loggers, checks authentication and authorization checks on all callback routers and web endpoints, validates UUID-based upload naming, and verifies CSRF tokens.
  Applies surgical security patches if vulnerabilities are detected.

* Handoff 4 (`devops-vps-guardian`):
  Exclusively edits `requirements.txt`, `.env.example`, Docker files (`Dockerfile`, `docker-compose.yml`), systemd unit files (`deploy/systemd/*`), and GitHub Actions workflows (`.github/workflows/*`).
  Pins dependencies, synchronizes configuration templates, ensures unprivileged runtime user security, and verifies deployment configurations.

* Handoff 5 (`tdd-qa-verifier`):
  Exclusively edits `tests/test_*.py`, `conftest.py`, and `pytest.ini`.
  Authors unit, integration, concurrency, and security tests validating the new behavior across both Bot and Web surfaces.
  Executes `pytest -v` across the entire test suite and reports the results to the coordinator.

## Swarm Circuit Breaker (Self-Healing Protocol)

If `pytest -v` produces any failure during Handoff 5, the following self-healing loop is mandatory:

* `tdd-qa-verifier` is strictly prohibited from modifying production application logic (`database.py`, `main.py`, `app.py`, `config.py`, `daily_report.py`).
* `tdd-qa-verifier` isolates the failure: test name, assertion message, and full traceback.
* The coordinator routes the bug back to the responsible owner agent:
  - Database, migration, lock, or temporal errors: routed to `sqlite-temporal-architect`.
  - Handler, routing, UI, job queue, or bot state errors: routed to `bot-web-core-engineer`.
  - Security check, token, or permission errors: routed to `security-privacy-auditor`.
  - Dependency or environment failures: routed to `devops-vps-guardian`.
* The responsible agent applies the minimal required fix to its owned files.
* `tdd-qa-verifier` re-runs `pytest -v`.
* The cycle repeats until 100% of tests pass with zero warnings and zero failures.

## Verification Checklist
- [ ] Phase A discovery agents run concurrently in read-only mode without file mutations.
- [ ] No agent edits files outside its assigned file ownership boundary in Phase B.
- [ ] `database.py` changes precede consuming changes in `main.py` and `app.py`.
- [ ] Security diff audit occurs before deployment packaging and test finalization.
- [ ] `tdd-qa-verifier` does not rewrite production code when tests fail.
- [ ] Full `pytest -v` suite passes with zero failures before task completion.
- [ ] Knowledge graph is refreshed using `python -m graphify update .` after code edits.
