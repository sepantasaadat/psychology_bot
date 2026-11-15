---
name: clinic-swarm-coordinator
description: Orchestrates multi-agent development on psychology_bot via two-phase discovery and file-ownership handoffs
---

# Workflow: clinic-swarm-coordinator

Follow the `clinic-swarm-coordinator` skill protocol:
1. Phase A: Dispatch `security-privacy-auditor`, `sqlite-temporal-architect`, and `bot-web-core-engineer` in parallel read-only discovery.
2. Phase B: Sequentially execute Handoff 1 (`sqlite-temporal-architect`), Handoff 2 (`bot-web-core-engineer`), Handoff 3 (`security-privacy-auditor`), Handoff 4 (`devops-vps-guardian`), and Handoff 5 (`tdd-qa-verifier`).
3. Self-Healing Circuit Breaker: Route test failures back to component owners until 100% of tests pass.
