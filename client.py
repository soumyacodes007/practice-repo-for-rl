"""
Client for LLM Text2SQL Failure Gym.

Synchronous HTTP client for interacting with the environment.
"""

from openenv.core.env_client import SyncEnvClient
from .models import QueryAction, QueryObservation, QueryState


class LLMQueryOptimizerClient(SyncEnvClient[QueryAction, QueryObservation, QueryState]):
    """Synchronous client for LLM Query Optimizer environment."""
    
    def reset(self, task_id: int = 1) -> QueryObservation:
        """
        Reset environment with specified task.
        
        Args:
            task_id: Task ID (1=easy, 2=medium, 3=hard)
        
        Returns:
            Initial observation
        """
        return super().reset(task_id=task_id)
