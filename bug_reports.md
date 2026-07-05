# Bug Reports — Task Manager

Found via systematic testing of `task_manager.py` against its documented
specification. Each report below corresponds to a real, reproducible
test failure (see `test_task_manager.py` and the run log in `README.md`).

Severity scale used: **Critical** (data loss / corruption) · **High**
(feature works incorrectly for common inputs) · **Medium** (feature
works incorrectly for edge-case inputs) · **Low** (cosmetic / minor).

---

## BUG-01 — Tasks silently share tags due to mutable default argument

**Severity:** High
**Component:** `TaskManager.add_task()`
**Status:** Fixed in `task_manager_fixed.py`

**Steps to reproduce:**
1. Call `add_task("Task A")` without a `tags` argument
2. Call `add_task("Task B")` without a `tags` argument
3. Call `tag_task(task_a_id, "urgent")`
4. Inspect `task_b.tags`

**Expected result:** Task B's tags remain `[]` — it was never tagged.

**Actual result:** Task B's tags contain `["urgent"]`. Any two tasks
created without an explicit `tags` argument secretly share the same
underlying list object, so tagging one silently tags all the others
that used the default.

**Root cause:** Classic Python mutable-default-argument pitfall —
`def add_task(..., tags=[]):` evaluates the empty list once, at
function-definition time, not once per call.

**Why it matters:** This would ship completely invisibly. Nothing
crashes; tags just accumulate across unrelated tasks over time, and by
the time a user notices "this task has a tag I never added," the cause
is nowhere near the symptom.

**Suggested fix:** Use `tags: list[str] | None = None` as the default,
and create a new list inside the function body when it's `None`.

---

## BUG-02 — Task due "today" is not flagged as overdue

**Severity:** High
**Component:** `TaskManager.get_overdue_tasks()`
**Status:** Fixed in `task_manager_fixed.py`

**Steps to reproduce:**
1. Add a task with `due_date=date.today()`
2. Call `get_overdue_tasks()`

**Expected result:** The task appears in the returned list. Per spec,
"overdue" means due today or earlier.

**Actual result:** The task is excluded. It only appears once the date
rolls over to tomorrow.

**Root cause:** Boundary condition error — the comparison uses
`t.due_date < as_of` (strictly before today) instead of `<=` (today or
before).

**Why it matters:** This is a boundary bug, so normal manual testing
tends to miss it entirely — a developer testing "add a task due
yesterday" and "add a task due next week" would see correct results in
both cases and never notice the one date that's actually broken. Users
would see tasks due today quietly missing from their overdue list.

**Suggested fix:** Change the comparison operator from `<` to `<=`.

---

## BUG-03 — Search is case-sensitive despite being specified as case-insensitive

**Severity:** Medium
**Component:** `TaskManager.search_tasks()`
**Status:** Fixed in `task_manager_fixed.py`

**Steps to reproduce:**
1. Add a task titled `"Buy Milk"`
2. Call `search_tasks("milk")` (lowercase)

**Expected result:** One result — the search matches regardless of
case, per the method's own docstring.

**Actual result:** Zero results. The search does a raw substring check
with no case normalization.

**Root cause:** Missing `.lower()` normalization on both the keyword and
the title before comparing.

**Why it matters:** Search that silently fails to match reasonable,
expected input is a poor user experience and directly contradicts the
documented behavior — a user typing a perfectly reasonable search term
gets "no results" and has no way to know why.

**Suggested fix:** Lowercase both `keyword` and `t.title` before the
`in` comparison.

---

## BUG-04 — Task IDs can be reused after deletion

**Severity:** Critical
**Component:** `TaskManager.add_task()` / `_next_id()`
**Status:** Fixed in `task_manager_fixed.py`

**Steps to reproduce:**
1. Add three tasks (IDs 1, 2, 3)
2. Delete task 2
3. Add a new task

**Expected result:** The new task receives an ID that has never been
used before (e.g. 4).

**Actual result:** The new task is assigned ID 3 — colliding with the
still-existing task 3. Two different tasks now share the same ID.

**Root cause:** `_next_id()` derives the next ID from `len(self.tasks) +
1`. This works only if tasks are never deleted; as soon as the list
length no longer matches "how many tasks have ever existed," IDs start
colliding.

**Why it matters:** This is the most severe bug in the set: ID
collisions mean `get_task()`, `complete_task()`, and `delete_task()` can
silently operate on the wrong task. In a real product this is a
data-integrity bug, not just a display glitch — flagged Critical
because the failure mode is silent data corruption, not a crash.

**Suggested fix:** Use a monotonically increasing counter
(`itertools.count`) that is never reset or derived from list length.

---

## BUG-05 — Priorities sorted alphabetically instead of numerically

**Severity:** Medium
**Component:** `TaskManager.sort_by_priority()`

**Steps to reproduce:**
1. Add a task with `priority=10`
2. Add a task with `priority=2`
3. Call `sort_by_priority()`

**Expected result:** Priority 2 (higher priority) appears before
priority 10.

**Actual result:** Priority 10 appears before priority 2 — the sort key
is `str(t.priority)`, and `"10" < "2"` is true lexicographically even
though `10 < 2` is false numerically.

**Root cause:** Sorting on the string representation of a number
instead of the number itself.

**Why it matters:** Only manifests once priority values reach double
digits, so a quick manual test with priorities 1–5 would never catch
it — exactly the kind of bug systematic boundary testing is meant to
surface.

**Suggested fix:** Sort using `key=lambda t: t.priority` (the int
directly), not its string form.

---

## Summary

| ID | Severity | Component | Status |
|---|---|---|---|
| BUG-01 | High | add_task (tags) | Fixed |
| BUG-02 | High | get_overdue_tasks | Fixed |
| BUG-03 | Medium | search_tasks | Fixed |
| BUG-04 | Critical | add_task (ID assignment) | Fixed |
| BUG-05 | Medium | sort_by_priority | Fixed |

5 of 5 bugs found via systematic spec-based testing, documented, and
verified fixed — full retest log in `README.md`.
