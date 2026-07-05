"""
task_manager.py

A small in-memory task manager module — the "application under test" for
this QA case study.

SPECIFICATION
=============
This is the intended behavior each method should follow. The test suite
in test_task_manager.py is written against this specification, not
against whatever the code happens to do — which is how it catches the
bugs below.

- add_task(title, due_date=None, priority=3, tags=None) -> int
    Adds a task and returns its unique task ID. Each task must get an
    ID that is never reused, even after other tasks are deleted. Tags
    passed to one call must never be visible on a task from a different
    call unless explicitly shared by the caller.

- complete_task(task_id) -> None
    Marks a task completed. Raises KeyError if the ID doesn't exist.

- delete_task(task_id) -> None
    Removes a task permanently. Raises KeyError if the ID doesn't exist.

- get_overdue_tasks(as_of=None) -> list[Task]
    Returns all incomplete tasks whose due_date is TODAY OR EARLIER
    (i.e. a task due today counts as overdue, not just tasks due
    strictly before today). Defaults `as_of` to today.

- search_tasks(keyword) -> list[Task]
    Case-insensitive search of task titles for the given keyword.

- sort_by_priority() -> list[Task]
    Returns all tasks sorted from highest priority (1) to lowest (10),
    in correct numeric order.

NOTE: This file intentionally contains bugs (see BUG comments) for the
purposes of the QA case study — the test suite and bug_reports.md
document them. See task_manager_fixed.py for the corrected version.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    id: int
    title: str
    due_date: date | None
    priority: int
    tags: list[str]
    completed: bool = False


class TaskManager:
    def __init__(self) -> None:
        self.tasks: list[Task] = []

    # BUG-01 (see bug_reports.md): mutable default argument.
    # `tags=[]` creates ONE list object at function-definition time, and
    # every call that doesn't pass its own `tags` shares that same list.
    def add_task(
        self,
        title: str,
        due_date: date | None = None,
        priority: int = 3,
        tags: list[str] = [],  # <-- BUG-01
    ) -> int:
        task_id = self._next_id()
        task = Task(id=task_id, title=title, due_date=due_date, priority=priority, tags=tags)
        self.tasks.append(task)
        return task_id

    # BUG-04 (see bug_reports.md): ID reuse after deletion.
    # Basing the next ID on the current LENGTH of the list means a
    # deleted task's ID can be handed out again to a new task.
    def _next_id(self) -> int:
        return len(self.tasks) + 1  # <-- BUG-04

    def get_task(self, task_id: int) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"No task with id {task_id}")

    def complete_task(self, task_id: int) -> None:
        self.get_task(task_id).completed = True

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)  # raises KeyError if missing
        self.tasks.remove(task)

    def tag_task(self, task_id: int, tag: str) -> None:
        self.get_task(task_id).tags.append(tag)

    def list_tasks(self, include_completed: bool = False) -> list[Task]:
        if include_completed:
            return list(self.tasks)
        return [t for t in self.tasks if not t.completed]

    # BUG-02 (see bug_reports.md): off-by-one at the boundary.
    # Spec says a task due TODAY counts as overdue. `<` excludes today;
    # it should be `<=`.
    def get_overdue_tasks(self, as_of: date | None = None) -> list[Task]:
        as_of = as_of or date.today()
        return [
            t for t in self.tasks
            if not t.completed and t.due_date is not None and t.due_date < as_of  # <-- BUG-02
        ]

    # BUG-03 (see bug_reports.md): search is case-sensitive despite the
    # feature being specified (and named) as case-insensitive search.
    def search_tasks(self, keyword: str) -> list[Task]:
        return [t for t in self.tasks if keyword in t.title]  # <-- BUG-03

    # BUG-05 (see bug_reports.md): sorting priority as a string instead
    # of numerically. "10" sorts before "2" lexicographically.
    def sort_by_priority(self) -> list[Task]:
        return sorted(self.tasks, key=lambda t: str(t.priority))  # <-- BUG-05
