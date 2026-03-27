"""
Fault injector for LLM Text2SQL Failure Gym.

Defines 3 tasks with increasing difficulty and injects faults into the database.
"""

import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Definition of a SQL optimization task."""
    task_id: int
    difficulty: str
    description: str
    slow_query: str
    target_time_ms: float
    setup_commands: list[str]  # Commands to inject the fault


# Task definitions
TASKS = {
    1: Task(
        task_id=1,
        difficulty="Easy",
        description=(
            "LLM generated query missing index on user_id — full table scan on 200K rows. "
            "The query filters orders by user_id but no index exists, causing a slow sequential scan."
        ),
        slow_query="SELECT * FROM orders WHERE user_id = 42",
        target_time_ms=100.0,
        setup_commands=[
            "DROP INDEX IF EXISTS idx_orders_user"
        ]
    ),
    
    2: Task(
        task_id=2,
        difficulty="Medium",
        description=(
            "LLM generated cartesian join between users and orders — missing JOIN condition. "
            "The query uses comma-separated tables without proper JOIN, creating a cartesian product "
            "of 100K users × 200K orders = 20 billion row combinations before filtering."
        ),
        slow_query=(
            "SELECT u.email, COUNT(o.id) as order_count "
            "FROM users u, orders o "
            "WHERE u.country = 'IN' "
            "GROUP BY u.email"
        ),
        target_time_ms=200.0,
        setup_commands=[]  # No index to drop — fault is in the query itself
    ),
    
    3: Task(
        task_id=3,
        difficulty="Hard",
        description=(
            "LLM generated correlated subquery + two missing indexes. "
            "The query uses a correlated subquery that executes once per user row, "
            "and both the outer query (country filter) and inner query (user_id join) lack indexes. "
            "Must create indexes in correct order and potentially rewrite the subquery as a JOIN."
        ),
        slow_query=(
            "SELECT u.email, "
            "(SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count "
            "FROM users u "
            "WHERE u.country = 'IN'"
        ),
        target_time_ms=150.0,
        setup_commands=[
            "DROP INDEX IF EXISTS idx_orders_user",
            "DROP INDEX IF EXISTS idx_users_country"
        ]
    )
}


class FaultInjector:
    """Injects faults into the database for each task."""
    
    def __init__(self, backend):
        """
        Initialize fault injector.
        
        Args:
            backend: SQLiteBackend instance
        """
        self.backend = backend
    
    def inject_fault(self, task_id: int) -> Dict[str, Any]:
        """
        Inject fault for the specified task.
        
        Args:
            task_id: Task ID (1, 2, or 3)
        
        Returns:
            Dictionary with task details
        """
        if task_id not in TASKS:
            logger.error(f"Invalid task_id: {task_id}")
            return self._get_default_task()
        
        task = TASKS[task_id]
        
        logger.info(f"Injecting fault for Task {task_id} ({task.difficulty})")
        
        # Execute setup commands to inject the fault
        for cmd in task.setup_commands:
            try:
                output, _, _ = self.backend.run_command(cmd)
                logger.info(f"  Setup: {cmd} -> {output}")
            except Exception as e:
                logger.error(f"  Setup failed: {cmd} -> {e}")
        
        # Measure baseline execution time
        baseline_time_ms = self.backend.measure_query_time(task.slow_query)
        query_plan = self.backend.get_query_plan(task.slow_query)
        
        logger.info(f"  Baseline time: {baseline_time_ms:.2f}ms (target: {task.target_time_ms}ms)")
        
        return {
            "task_id": task.task_id,
            "difficulty": task.difficulty,
            "description": task.description,
            "slow_query": task.slow_query,
            "target_time_ms": task.target_time_ms,
            "baseline_time_ms": baseline_time_ms,
            "query_plan": query_plan
        }
    
    def _get_default_task(self) -> Dict[str, Any]:
        """Return default task (Task 1) if invalid task_id provided."""
        return self.inject_fault(1)
    
    @staticmethod
    def get_task_description(task_id: int) -> str:
        """Get human-readable description for a task."""
        if task_id in TASKS:
            return TASKS[task_id].description
        return "Unknown task"
    
    @staticmethod
    def get_all_tasks() -> Dict[int, Task]:
        """Get all task definitions."""
        return TASKS
