# QA Case Study: Task Manager Module

A complete QA cycle on a small Python module — spec review, systematic
test design, bug discovery, professional bug reporting, fix
verification. Built to demonstrate QA process, not just "I can write
tests."

## The story, in order

1. **`task_manager.py`** — a task-management module with a written
   specification (see its docstring) and 5 real, intentionally-placed
   bugs of varying severity.
2. **`test_plan.md`** — the test strategy: what's in/out of scope, which
   techniques were used (equivalence partitioning, boundary value
   analysis, negative testing) and why, entry/exit criteria.
3. **`test_task_manager.py`** — 21 automated tests written against the
   *specification*, not against the existing code's behavior. That
   distinction is what makes the suite catch real bugs instead of just
   confirming whatever the code already does.
4. **`bug_reports.md`** — 5 professional bug reports, one per defect
   found, each with severity, steps to reproduce, expected vs. actual
   result, root cause, and suggested fix.
5. **`task_manager_fixed.py`** — the corrected module.

## Actual test run (not simulated)

Running the suite against the original buggy module:

```
$ pytest test_task_manager.py -v
...
FAILED test_task_manager.py::TestAddTask::test_default_tags_are_isolated_between_tasks
FAILED test_task_manager.py::TestAddTask::test_id_not_reused_after_deletion
FAILED test_task_manager.py::TestOverdueTasks::test_task_due_today_is_overdue
FAILED test_task_manager.py::TestSearchTasks::test_search_is_case_insensitive
FAILED test_task_manager.py::TestSortByPriority::test_sorts_double_digit_priority_numerically_not_lexically
5 failed, 16 passed in 0.08s
```

Running the same suite against the fixed module:

```
$ pytest test_task_manager.py -v   (import changed to task_manager_fixed)
...
21 passed in 0.04s
```

## How to reproduce this yourself

```bash
pip install pytest

# See the bugs fail:
pytest test_task_manager.py -v

# Confirm the fix: point the same suite at the fixed module
sed 's/from task_manager import/from task_manager_fixed import/' \
    test_task_manager.py > test_against_fixed.py
pytest test_against_fixed.py -v
rm test_against_fixed.py
```

## Bugs found at a glance

| ID | Severity | Issue |
|---|---|---|
| BUG-01 | High | Mutable default argument causes tasks to silently share tags |
| BUG-02 | High | Task due "today" not flagged as overdue (boundary bug) |
| BUG-03 | Medium | Search is case-sensitive despite being specified as case-insensitive |
| BUG-04 | Critical | Task IDs can be reused after deletion, causing collisions |
| BUG-05 | Medium | Priorities sorted as strings, not numbers ("10" before "2") |

Full detail on each in `bug_reports.md`.

## Why this shape of project

A lot of QA portfolios show only "here are some tests I wrote." This
one is built to show the full loop a client is actually paying for:
reading a spec, designing tests that would actually catch violations of
that spec (not just re-testing the happy path), writing up what's found
in a way a developer could act on without back-and-forth, and verifying
the fix closes the loop.
