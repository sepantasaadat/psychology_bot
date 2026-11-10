# Graph Report - psychology_bot  (2026-11-11)

## Corpus Check
- 6 files · ~4,326 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 47 nodes · 100 edges · 8 communities (4 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `70f7bbe1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- database.py
- daily_report.py
- handle_receipt
- booking
- send_receipt_to_telegram
- about

## God Nodes (most connected - your core abstractions)
1. `button_handler()` - 11 edges
2. `get_connection()` - 10 edges
3. `booking()` - 6 edges
4. `handle_receipt()` - 6 edges
5. `main()` - 6 edges
6. `get_db_connection()` - 5 edges
7. `start()` - 5 edges
8. `handle_text()` - 5 edges
9. `send_receipt_to_telegram()` - 4 edges
10. `get_main_menu_keyboard()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `handle_receipt()` --calls--> `add_pending_appointment()`  [EXTRACTED]
  main.py → database.py
- `handle_receipt()` --calls--> `add_user()`  [EXTRACTED]
  main.py → database.py
- `button_handler()` --calls--> `delete_appointment()`  [EXTRACTED]
  main.py → database.py
- `button_handler()` --calls--> `get_all_confirmed_appointments()`  [EXTRACTED]
  main.py → database.py
- `button_handler()` --calls--> `get_appointment()`  [EXTRACTED]
  main.py → database.py

## Import Cycles
- None detected.

## Communities (8 total, 4 thin omitted)

### Community 0 - "database.py"
Cohesion: 0.40
Nodes (10): add_pending_appointment(), add_user(), delete_appointment(), get_all_confirmed_appointments(), get_appointment(), get_booked_times(), get_connection(), setup_database() (+2 more)

### Community 3 - "daily_report.py"
Cohesion: 0.39
Nodes (4): get_1405_working_days(), get_upcoming_week_appointments(), send_email(), get_upcoming_days()

### Community 4 - "handle_receipt"
Cohesion: 0.46
Nodes (6): error_handler(), get_main_menu_keyboard(), handle_receipt(), handle_text(), main(), start()

### Community 5 - "booking"
Cohesion: 0.67
Nodes (4): booking(), get_available_hours(), get_db_connection(), setup_web_user()

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `database.py` to `daily_report.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `main()` (e.g. with `button_handler()` and `error_handler()`) actually correct?**
  _`main()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Why does `button_handler()` connect `database.py` to `main.py`, `daily_report.py`, `handle_receipt`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `handle_receipt()` connect `handle_receipt` to `database.py`, `main.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._