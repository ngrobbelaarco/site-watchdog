"""
task_manager_fixed.py

Corrected version of task_manager.py, with all 5 bugs from bug_reports.md
fixed. See that file for the original defect writeups, and see the
"Fix" note above each change below for what changed and why.

Running test_task_manager.py against this module (instead of
task_manager.py) should show 21/21 tests passing. See README.md for how
to point the test suite at this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import count


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
        # Fix for BUG-04: a monotonically increasing counter that is never
        # reused, instead of deriving the next id from the current list
        # length (which collides after deletions).
        self._id_counter = count(start=1)

    # Fix for BUG-01: use `None` as the sentinel default and create a new
    # list inside the function body on each call, instead of sharing one
    # mutable list object across every call that omits `tags`.
    def add_task(
        self,
        title: str,
        due_date: date | None = None,
        priority: int = 3,
        tags: list[str] | None = None,
    ) -> int:
        task_id = self._next_id()
        task = Task(
            id=task_id,
            title=title,
            due_date=due_date,
            priority=priority,
            tags=list(tags) if tags is not None else [],  # fresh list every time
        )
        self.tasks.append(task)
        return task_id

    def _next_id(self) -> int:
        return next(self._id_counter)

    def get_task(self, task_id: int) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"No task with id {task_id}")

    def complete_task(self, task_id: int) -> None:
        self.get_task(task_id).completed = True

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)
        self.tasks.remove(task)

    def tag_task(self, task_id: int, tag: str) -> None:
        self.get_task(task_id).tags.append(tag)

    def list_tasks(self, include_completed: bool = False) -> list[Task]:
        if include_completed:
            return list(self.tasks)
        return [t for t in self.tasks if not t.completed]

    # Fix for BUG-02: `<=` instead of `<` so a task due exactly today is
    # included, matching the "due today or earlier" spec.
    def get_overdue_tasks(self, as_of: date | None = None) -> list[Task]:
        as_of = as_of or date.today()
        return [
            t for t in self.tasks
            if not t.completed and t.due_date is not None and t.due_date <= as_of
        ]

    # Fix for BUG-03: lowercase both sides before comparing, so the
    # search is genuinely case-insensitive as specified.
    def search_tasks(self, keyword: str) -> list[Task]:
        keyword_lower = keyword.lower()
        return [t for t in self.tasks if keyword_lower in t.title.lower()]

    # Fix for BUG-05: sort by the numeric priority value directly instead
    # of its string representation.
    def sort_by_priority(self) -> list[Task]:
        return sorted(self.tasks, key=lambda t: t.priority)
