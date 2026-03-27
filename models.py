"""
Data models for LLM Text2SQL Failure Gym.

Defines Action, Observation, State for SQL query optimization training.
"""

from pydantic import BaseModel, Field
from typing import Optional
from openenv.core.env_server.types import Action, Observation, State


class QueryAction(Action):
    """Agent's action — a SQL command to optimize the slow query."""
    command: str = Field(
        ..., 
        min_length=1,
        description="SQL command: CREATE INDEX, EXPLAIN QUERY PLAN, ANALYZE, or optimized SELECT"
    )
    # Examples:
    # "CREATE INDEX idx_orders_user ON orders(user_id)"
    # "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE user_id=1"
    # "ANALYZE orders"
    # "SELECT u.email FROM users u JOIN orders o ON u.id=o.user_id WHERE u.country='IN'"


class QueryObservation(Observation):
    """What the agent sees after each action."""
    task_id: int = Field(default=1, ge=1, le=3, description="Current task (1=easy, 2=medium, 3=hard)")
    task_description: str = Field(default="", description="Human-readable task description")
    slow_query: str = Field(default="", description="The original slow query to optimize")
    execution_time_ms: float = Field(default=0.0, ge=0.0, description="Current query execution time in milliseconds")
    query_plan: str = Field(default="", description="EXPLAIN QUERY PLAN output")
    command_output: str = Field(default="", description="Output from the last command")
    history: list[str] = Field(default_factory=list, description="All commands executed so far")
    step: int = Field(default=0, ge=0, description="Current step number")
    max_steps: int = Field(default=10, description="Maximum steps allowed")
    reward_breakdown: dict = Field(
        default_factory=dict,
        description="Breakdown of reward components: speed, index_used, penalty"
    )


class QueryState(State):
    """Episode metadata and state."""
    episode_id: str = ""
    task_id: int = 1
    baseline_time_ms: float = 0.0
    current_time_ms: float = 0.0
    target_time_ms: float = 0.0
    steps_taken: int = 0
    is_solved: bool = False
    cumulative_reward: float = 0.0
    commands_history: list[str] = []
