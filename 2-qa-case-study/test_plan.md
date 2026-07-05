# Test Plan — Task Manager Module

## 1. Objective

Verify that `task_manager.py` correctly implements the behavior defined
in its specification (see the module docstring), and document any
deviations found as bug reports.

## 2. Scope

**In scope:** all public methods of `TaskManager` — `add_task`,
`complete_task`, `delete_task`, `tag_task`, `list_tasks`,
`get_overdue_tasks`, `search_tasks`, `sort_by_priority`.

**Out of scope:** persistence/storage (this module is in-memory only,
no database or file I/O to test), concurrency (single-threaded use
only), UI (no interface exists yet — this is a backend logic module).

## 3. Test strategy

Three complementary techniques were used, chosen to match where bugs
typically hide in logic like this:

- **Equivalence partitioning.** For each method, identify the distinct
  classes of input it can receive (e.g. for `delete_task`: an existing
  ID vs. a non-existent ID) and test at least one representative from
  each class, rather than testing many similar "normal" inputs.
- **Boundary value analysis.** For anything involving a comparison
  (dates, priority ordering), test values sitting exactly on the
  boundary — a task due *exactly* today, not just "clearly overdue" or
  "clearly not due yet." This is where off-by-one errors live, and
  where they're least likely to be caught by casual manual testing.
- **Negative testing.** Confirm the module fails safely and predictably
  on invalid input (e.g. operating on a task ID that doesn't exist
  should raise `KeyError`, not crash with an unrelated error or fail
  silently).

## 4. Test environment

- Python 3.10+
- pytest 7.4+
- No external services, database, or network access required — the
  entire suite runs in-memory and completes in well under a second.

## 5. Entry / exit criteria

**Entry:** `task_manager.py` implements all methods listed in section 2
and matches the documented function signatures.

**Exit:** All 21 test cases pass. (At the time of this case study, 5 of
21 failed against the first version submitted for testing — see
`bug_reports.md`. All 5 were fixed and the full suite was re-run to
confirm the fix, per the retest log in `README.md`.)

## 6. Test case summary

| Area | Test cases | Technique |
|---|---|---|
| `add_task` | ID returned, ID uniqueness under normal use, task retrievable, tag isolation between tasks, ID uniqueness after deletion | Equivalence partitioning, state-based testing |
| `complete_task` / `delete_task` | Normal operation, operation on non-existent ID, filtering completed from `list_tasks` | Equivalence partitioning, negative testing |
| `get_overdue_tasks` | Due yesterday, due exactly today, due tomorrow, completed task excluded, no-due-date task excluded | Boundary value analysis |
| `search_tasks` | Exact case match, mismatched case, no match | Equivalence partitioning |
| `sort_by_priority` | Single-digit priorities, mixed single/double-digit priorities | Boundary value analysis |

## 7. Risk-based prioritization

Testing effort was weighted toward `get_overdue_tasks` and `add_task`
first, since a task manager's core value proposition is "tell me what's
overdue" and "don't lose or corrupt my tasks" — a failure in either
undermines the whole tool, whereas a failure in `sort_by_priority` is
comparatively low-stakes (annoying, not data-threatening).

## 8. Deliverables

- `test_task_manager.py` — the automated suite itself
- `bug_reports.md` — one report per defect found, with repro steps,
  expected vs. actual, root cause, and suggested fix
- `task_manager_fixed.py` — corrected implementation
- Retest confirmation (in `README.md`) that all 21 tests pass against
  the fixed version
