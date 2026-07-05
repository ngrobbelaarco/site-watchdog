"""
test_task_manager.py

QA test suite for task_manager.py, written against the specification in
that file's module docstring — NOT against whatever the current code
happens to do. That distinction is the point of this suite: several of
these tests are expected to FAIL against the current (buggy) version,
and those failures are exactly what's written up in bug_reports.md.

Test design approach
---------------------
- Equivalence partitioning: for each method, tests cover the "normal"
  input class plus each distinct edge case class (empty input, single
  item, boundary value, invalid ID).
- Boundary value analysis: due-date tests specifically probe the boundary
  between "due today" and "due tomorrow" / "due yesterday", since that's
  where off-by-one bugs live.
- Negative testing: operations on non-existent task IDs are expected to
  raise KeyError, not fail silently or crash with an unrelated error.

Run with:
    pytest test_task_manager.py -v

To see ONLY the currently-passing tests (i.e. what the shipped code gets
right), run against task_manager_fixed.py instead by changing the import
at the top of this file — see README.md for the two-mode instructions.
"""

from datetime import date, timedelta

import pytest

from task_manager import TaskManager


@pytest.fixture
def manager():
    return TaskManager()


# ---------------------------------------------------------------------------
# add_task: normal cases + BUG-01 (mutable default argument) + BUG-04 (ID reuse)
# ---------------------------------------------------------------------------

class TestAddTask:
    def test_returns_an_id(self, manager):
        task_id = manager.add_task("Buy milk")
        assert isinstance(task_id, int)

    def test_ids_are_unique_across_normal_use(self, manager):
        id1 = manager.add_task("Task A")
        id2 = manager.add_task("Task B")
        id3 = manager.add_task("Task C")
        assert len({id1, id2, id3}) == 3

    def test_task_is_retrievable_after_adding(self, manager):
        task_id = manager.add_task("Buy milk", priority=1)
        task = manager.get_task(task_id)
        assert task.title == "Buy milk"
        assert task.priority == 1

    def test_default_tags_are_isolated_between_tasks(self, manager):
        """
        BUG-01: tasks created without an explicit `tags` argument should
        never share state. Tagging one default-tagged task must not
        affect another default-tagged task.
        Expected to FAIL against the current code (see bug_reports.md, BUG-01).
        """
        id1 = manager.add_task("Task A")  # no tags passed -> uses default
        id2 = manager.add_task("Task B")  # no tags passed -> uses default

        manager.tag_task(id1, "urgent")

        task_b = manager.get_task(id2)
        assert task_b.tags == [], (
            f"Task B should have no tags, but got {task_b.tags!r} — "
            "tagging Task A leaked into Task B's tags list."
        )

    def test_id_not_reused_after_deletion(self, manager):
        """
        BUG-04: IDs must remain unique for the life of the TaskManager,
        even after tasks are deleted and new ones are added.
        Expected to FAIL against the current code (see bug_reports.md, BUG-04).
        """
        id1 = manager.add_task("Task A")
        id2 = manager.add_task("Task B")
        id3 = manager.add_task("Task C")

        manager.delete_task(id2)
        id4 = manager.add_task("Task D")

        all_ids_ever_issued = [id1, id2, id3, id4]
        remaining_ids = {t.id for t in manager.tasks}

        assert id4 not in (id1, id3), (
            f"New task got id={id4}, which collides with an existing task id. "
            f"Remaining task ids after delete+add: {remaining_ids}"
        )


# ---------------------------------------------------------------------------
# complete_task / delete_task: normal cases + negative testing
# ---------------------------------------------------------------------------

class TestCompleteAndDelete:
    def test_complete_task_marks_completed(self, manager):
        task_id = manager.add_task("Buy milk")
        manager.complete_task(task_id)
        assert manager.get_task(task_id).completed is True

    def test_complete_nonexistent_task_raises_keyerror(self, manager):
        with pytest.raises(KeyError):
            manager.complete_task(999)

    def test_delete_task_removes_it(self, manager):
        task_id = manager.add_task("Buy milk")
        manager.delete_task(task_id)
        with pytest.raises(KeyError):
            manager.get_task(task_id)

    def test_delete_nonexistent_task_raises_keyerror(self, manager):
        with pytest.raises(KeyError):
            manager.delete_task(999)

    def test_list_tasks_excludes_completed_by_default(self, manager):
        id1 = manager.add_task("Active task")
        id2 = manager.add_task("Done task")
        manager.complete_task(id2)

        visible = manager.list_tasks()
        assert {t.id for t in visible} == {id1}

    def test_list_tasks_can_include_completed(self, manager):
        id1 = manager.add_task("Active task")
        id2 = manager.add_task("Done task")
        manager.complete_task(id2)

        all_tasks = manager.list_tasks(include_completed=True)
        assert {t.id for t in all_tasks} == {id1, id2}


# ---------------------------------------------------------------------------
# get_overdue_tasks: boundary value analysis -- this is where BUG-02 lives
# ---------------------------------------------------------------------------

class TestOverdueTasks:
    def test_task_due_yesterday_is_overdue(self, manager):
        yesterday = date.today() - timedelta(days=1)
        task_id = manager.add_task("Old task", due_date=yesterday)
        overdue = manager.get_overdue_tasks()
        assert task_id in {t.id for t in overdue}

    def test_task_due_today_is_overdue(self, manager):
        """
        BUG-02: boundary case. Per spec, a task due exactly today counts
        as overdue. Expected to FAIL against the current code
        (see bug_reports.md, BUG-02).
        """
        today = date.today()
        task_id = manager.add_task("Due today task", due_date=today)
        overdue = manager.get_overdue_tasks()
        assert task_id in {t.id for t in overdue}, (
            "Task due today was not flagged as overdue, but the spec "
            "requires 'due today or earlier' to count as overdue."
        )

    def test_task_due_tomorrow_is_not_overdue(self, manager):
        tomorrow = date.today() + timedelta(days=1)
        task_id = manager.add_task("Future task", due_date=tomorrow)
        overdue = manager.get_overdue_tasks()
        assert task_id not in {t.id for t in overdue}

    def test_completed_task_is_never_overdue(self, manager):
        yesterday = date.today() - timedelta(days=1)
        task_id = manager.add_task("Old but done", due_date=yesterday)
        manager.complete_task(task_id)
        overdue = manager.get_overdue_tasks()
        assert task_id not in {t.id for t in overdue}

    def test_task_with_no_due_date_is_never_overdue(self, manager):
        task_id = manager.add_task("Someday task", due_date=None)
        overdue = manager.get_overdue_tasks()
        assert task_id not in {t.id for t in overdue}


# ---------------------------------------------------------------------------
# search_tasks: BUG-03 (case sensitivity)
# ---------------------------------------------------------------------------

class TestSearchTasks:
    def test_exact_case_match_still_works(self, manager):
        manager.add_task("Buy milk")
        results = manager.search_tasks("milk")
        assert len(results) == 1

    def test_search_is_case_insensitive(self, manager):
        """
        BUG-03: search is specified (and named) as case-insensitive.
        Expected to FAIL against the current code (see bug_reports.md, BUG-03).
        """
        manager.add_task("Buy Milk")
        results = manager.search_tasks("milk")
        assert len(results) == 1, (
            "Searching lowercase 'milk' should match task titled 'Buy Milk' "
            "per the case-insensitive search spec."
        )

    def test_search_no_match_returns_empty_list(self, manager):
        manager.add_task("Buy milk")
        results = manager.search_tasks("xyz-nonexistent")
        assert results == []


# ---------------------------------------------------------------------------
# sort_by_priority: BUG-05 (string sort instead of numeric)
# ---------------------------------------------------------------------------

class TestSortByPriority:
    def test_sorts_single_digit_priorities_correctly(self, manager):
        manager.add_task("Low", priority=5)
        manager.add_task("High", priority=1)
        result = manager.sort_by_priority()
        assert [t.priority for t in result] == [1, 5]

    def test_sorts_double_digit_priority_numerically_not_lexically(self, manager):
        """
        BUG-05: priority 2 must sort before priority 10 numerically.
        Expected to FAIL against the current code (see bug_reports.md, BUG-05),
        because string-sorting puts "10" before "2".
        """
        manager.add_task("Low priority", priority=10)
        manager.add_task("High priority", priority=2)
        result = manager.sort_by_priority()
        assert [t.priority for t in result] == [2, 10], (
            f"Expected priority order [2, 10], got {[t.priority for t in result]} "
            "-- looks like priorities are being sorted as strings."
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
