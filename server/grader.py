"""
Programmatic grader for LLM Text2SQL Failure Gym.

Computes rewards based on query performance improvements.
No LLM judge needed — all metrics are objective and deterministic.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class Grader:
    """Programmatic grader for SQL query optimization."""
    
    @staticmethod
    def compute_reward(
        before_ms: float,
        after_ms: float,
        query_plan: str,
        action_history: List[str]
    ) -> Dict[str, float]:
        """
        Compute reward for a single step.
        
        Args:
            before_ms: Execution time before this action
            after_ms: Execution time after this action
            query_plan: EXPLAIN QUERY PLAN output
            action_history: List of all commands executed so far
        
        Returns:
            Dictionary with reward breakdown:
                - speed_improvement: 0.0 to 0.5 based on speedup ratio
                - index_used: 0.35 if index is used, 0.0 otherwise
                - repeat_penalty: -0.15 per repeated command
                - total: sum of all components
        """
        # Speed improvement component (0.0 - 0.5)
        if before_ms > 0 and after_ms > 0:
            ratio = before_ms / after_ms
            # Cap at 10x speedup for reward calculation
            speed_improvement = min(ratio, 10.0) / 10.0 * 0.5
        else:
            speed_improvement = 0.0
        
        # Index usage component (0.0 or 0.35)
        index_used = 0.35 if "USING INDEX" in query_plan.upper() else 0.0
        
        # Repeat penalty (-0.15 per repeated command)
        unique_commands = len(set(action_history))
        total_commands = len(action_history)
        repeated_count = total_commands - unique_commands
        repeat_penalty = -0.15 * repeated_count
        
        # Total reward
        total = speed_improvement + index_used + repeat_penalty
        
        # Clamp to reasonable range
        total = max(-2.0, min(total, 8.0))
        
        return {
            "speed_improvement": round(speed_improvement, 4),
            "index_used": round(index_used, 4),
            "repeat_penalty": round(repeat_penalty, 4),
            "total": round(total, 4)
        }
    
    @staticmethod
    def grade_final(final_ms: float, target_ms: float) -> float:
        """
        Compute final grade for the episode (0.0 - 1.0).
        
        Args:
            final_ms: Final execution time in milliseconds
            target_ms: Target execution time in milliseconds
        
        Returns:
            Score from 0.0 to 1.0
        """
        if final_ms <= 0:
            return 0.0
        
        if final_ms <= target_ms:
            # Perfect score if at or below target
            return 1.0
        elif final_ms <= target_ms * 3:
            # Good score if within 3x of target
            return 0.6
        elif final_ms <= target_ms * 10:
            # Partial credit if within 10x of target
            return 0.3
        else:
            # Poor score if still very slow
            return 0.0
    
    @staticmethod
    def compute_terminal_bonus(
        final_ms: float,
        target_ms: float,
        steps_taken: int,
        max_steps: int
    ) -> float:
        """
        Compute terminal bonus for successfully completing the task.
        
        Args:
            final_ms: Final execution time
            target_ms: Target execution time
            steps_taken: Number of steps taken
            max_steps: Maximum steps allowed
        
        Returns:
            Bonus reward (0.0 to 5.0)
        """
        if final_ms > target_ms:
            # No bonus if target not met
            return 0.0
        
        # Base bonus for meeting target
        base_bonus = 3.0
        
        # Efficiency bonus for solving quickly
        efficiency_ratio = 1.0 - (steps_taken / max_steps)
        efficiency_bonus = efficiency_ratio * 2.0
        
        total_bonus = base_bonus + efficiency_bonus
        
        return round(max(0.0, min(total_bonus, 5.0)), 4)
    
    @staticmethod
    def is_valid_optimization_command(command: str) -> bool:
        """
        Check if command is a valid optimization action.
        
        Args:
            command: SQL command string
        
        Returns:
            True if valid, False otherwise
        """
        command_upper = command.strip().upper()
        
        valid_prefixes = [
            "CREATE INDEX",
            "DROP INDEX",
            "EXPLAIN QUERY PLAN",
            "ANALYZE",
            "SELECT"
        ]
        
        return any(command_upper.startswith(prefix) for prefix in valid_prefixes)
