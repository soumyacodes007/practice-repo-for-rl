"""
CI/CD Pipeline Fixer Gym - Pydantic Models
"""
from typing import Dict, List, Optional
from pydantic import Field
from openenv.core.env_server.types import Action, Observation, State


class PipelineFixAction(Action):
    """Action to fix a CI/CD pipeline."""
    fix_type: str = Field(..., description="Type of fix: 'yaml_syntax', 'add_dependency', 'optimize'")
    content: str = Field(..., description="The fixed pipeline YAML content")
    explanation: str = Field(default="", description="Explanation of the fix")


class PipelineFixObservation(Observation):
    """Observation after attempting a pipeline fix."""
    pipeline_yaml: str = Field(..., description="Current pipeline YAML")
    errors: List[str] = Field(default_factory=list, description="List of errors found")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    task_description: str = Field(..., description="Current task description")
    task_number: int = Field(..., description="Current task number (1-3)")
    done: bool = Field(default=False, description="Whether episode is complete")
    reward: float = Field(default=0.0, description="Reward for this step")


class PipelineFixState(State):
    """State of the CI/CD pipeline fixing environment."""
    task_number: int = Field(default=1, description="Current task (1=easy, 2=medium, 3=hard)")
    original_yaml: str = Field(default="", description="Original broken pipeline")
    current_yaml: str = Field(default="", description="Current pipeline state")
    ground_truth_yaml: str = Field(default="", description="Expected correct pipeline")
    fixes_applied: List[str] = Field(default_factory=list, description="List of fixes applied")
