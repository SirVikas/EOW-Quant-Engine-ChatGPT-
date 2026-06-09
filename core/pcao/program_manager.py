"""
PHOENIX PCAO — Program Management Engine  [GAP-013]

Manages programs as structured units of work:

  Program
    ↓
  Tasks (ordered, with dependencies)
    ↓
  Progress tracking
    ↓
  Completion criteria

Each Program is linked to a StrategicObjective (from pcao_engine.py).
Tasks within a program can have dependencies — task B cannot start until task A completes.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProgramTask:
    task_id: str
    program_id: str
    title: str
    description: str
    depends_on: List[str]   # task_ids that must complete first
    status: str = "PENDING"  # PENDING / IN_PROGRESS / BLOCKED / COMPLETE / SKIPPED
    assigned_to: str = "UNASSIGNED"
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    completion_notes: str = ""


@dataclass
class Program:
    program_id: str
    obj_id: str             # linked StrategicObjective
    title: str
    description: str
    status: str = "ACTIVE"  # ACTIVE / PAUSED / COMPLETE / CANCELLED
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0


class ProgramManager:
    """
    Hierarchical program/task tracking with dependency resolution.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._programs: Dict[str, Program] = {}
        self._tasks: Dict[str, ProgramTask] = {}     # task_id → task
        self._prog_tasks: Dict[str, List[str]] = {}  # program_id → [task_ids]
        self._seed_founding_programs()

    def _seed_founding_programs(self) -> None:
        programs_seed = [
            ("PROG-KGE-001", "PCAO-OBJ-001", "FTD-KGE-001 Execution", "Knowledge Graph Expansion implementation program"),
            ("PROG-HKE-001", "PCAO-OBJ-002", "FTD-HKE-001 Execution", "Historical Knowledge Extraction implementation program"),
            ("PROG-AEG-001", "PCAO-OBJ-003", "FTD-AEG-001 Execution", "AEG full activation program"),
            ("PROG-ETE-001", "PCAO-OBJ-004", "ETE Phase-2 Calibration", "Truth Engine calibration program — 500 trade target"),
            ("PROG-PCAO-001", "PCAO-OBJ-005", "PCAO Phase-2 Autonomy", "PCAO autonomous task routing activation"),
        ]
        for prog_id, obj_id, title, desc in programs_seed:
            p = Program(program_id=prog_id, obj_id=obj_id, title=title, description=desc)
            self._programs[prog_id] = p
            self._prog_tasks[prog_id] = []

    # ── Programs ──────────────────────────────────────────────────────────────

    def create_program(self, obj_id: str, title: str, description: str) -> Program:
        prog_id = f"PROG-{int(time.time()*1000)}"
        p = Program(program_id=prog_id, obj_id=obj_id, title=title, description=description)
        with self._lock:
            self._programs[prog_id] = p
            self._prog_tasks[prog_id] = []
        return p

    def update_program_status(self, program_id: str, status: str) -> dict:
        with self._lock:
            p = self._programs.get(program_id)
        if not p:
            return {"error": f"Program '{program_id}' not found"}
        p.status = status
        if status == "COMPLETE":
            p.completed_at = time.time()
        return {"updated": True, "program_id": program_id, "status": status}

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def add_task(
        self,
        program_id: str,
        title: str,
        description: str,
        depends_on: Optional[List[str]] = None,
        assigned_to: str = "UNASSIGNED",
    ) -> ProgramTask:
        task_id = f"TASK-{program_id}-{int(time.time()*1000)}"
        task = ProgramTask(
            task_id=task_id,
            program_id=program_id,
            title=title,
            description=description,
            depends_on=depends_on or [],
            assigned_to=assigned_to,
        )
        with self._lock:
            self._tasks[task_id] = task
            self._prog_tasks.setdefault(program_id, []).append(task_id)
        return task

    def start_task(self, task_id: str) -> dict:
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found"}
        blockers = [d for d in task.depends_on if self._tasks.get(d, ProgramTask(d, "", "", "", [])).status != "COMPLETE"]
        if blockers:
            task.status = "BLOCKED"
            return {"error": f"Blocked by dependencies: {blockers}", "task_id": task_id}
        task.status = "IN_PROGRESS"
        task.started_at = time.time()
        return {"started": True, "task_id": task_id}

    def complete_task(self, task_id: str, notes: str = "") -> dict:
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found"}
        task.status = "COMPLETE"
        task.completed_at = time.time()
        task.completion_notes = notes
        return {"completed": True, "task_id": task_id}

    # ── Query ─────────────────────────────────────────────────────────────────

    def program_status(self, program_id: str) -> dict:
        with self._lock:
            p = self._programs.get(program_id)
            task_ids = self._prog_tasks.get(program_id, [])
            tasks = [self._tasks[tid] for tid in task_ids if tid in self._tasks]
        if not p:
            return {"error": f"Program '{program_id}' not found"}
        total = len(tasks)
        complete = sum(1 for t in tasks if t.status == "COMPLETE")
        return {
            "program_id":   p.program_id,
            "obj_id":       p.obj_id,
            "title":        p.title,
            "status":       p.status,
            "total_tasks":  total,
            "complete":     complete,
            "progress_pct": round(complete / total * 100, 1) if total else 0.0,
            "tasks":        [self._ser_task(t) for t in tasks],
            "created_at":   p.created_at,
            "completed_at": p.completed_at or None,
        }

    def all_programs(self) -> List[dict]:
        with self._lock:
            prog_ids = list(self._programs.keys())
        return [self.program_status(pid) for pid in prog_ids]

    def blocked_tasks(self) -> List[dict]:
        with self._lock:
            items = [t for t in self._tasks.values() if t.status == "BLOCKED"]
        return [self._ser_task(t) for t in items]

    @staticmethod
    def _ser_task(t: ProgramTask) -> dict:
        return {
            "task_id":          t.task_id,
            "program_id":       t.program_id,
            "title":            t.title,
            "description":      t.description,
            "status":           t.status,
            "depends_on":       t.depends_on,
            "assigned_to":      t.assigned_to,
            "created_at":       t.created_at,
            "started_at":       t.started_at or None,
            "completed_at":     t.completed_at or None,
            "completion_notes": t.completion_notes,
        }


# Singleton
program_manager = ProgramManager()
