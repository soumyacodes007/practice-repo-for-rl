"""
CI/CD Pipeline Fixer Environment Implementation
"""
import uuid
from typing import Optional
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from ..models import PipelineFixAction, PipelineFixObservation, PipelineFixState
from ..tasks import TASKS
from ..grader import grade_pipeline_fix


class PipelineFixerEnvironment(Environment):
    """
    Environment for training agents to fix CI/CD pipelines.
    
    Tasks:
    1. Easy: Fix YAML syntax errors
    2. Medium: Add missing dependencies
    3. Hard: Optimize pipeline (caching, parallelization, job dependencies)
    """
    
    def __init__(self):
        self._state = PipelineFixState(episode_id=str(uuid.uuid4()))
    
    def reset(self) -> PipelineFixObservation:
        """Reset environment to Task 1"""
        task = TASKS[1]
        self._state = PipelineFixState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            task_number=1,
            original_yaml=task["broken"],
            current_yaml=task["broken"],
            ground_truth_yaml=task["fixed"],
            fixes_applied=[]
        )
        
        return PipelineFixObservation(
            pipeline_yaml=task["broken"],
            errors=["YAML indentation error detected"],
            warnings=[],
            task_description=task["description"],
            task_number=1,
            done=False,
            reward=0.0
        )
    
    def step(self, action: PipelineFixAction) -> PipelineFixObservation:
        """Execute a pipeline fix action"""
        self._state.step_count += 1
        
        # Update current YAML with submitted fix
        self._state.current_yaml = action.content
        self._state.fixes_applied.append(action.fix_type)
        
        # Grade the submission
        score = grade_pipeline_fix(
            self._state.task_number,
            action.content,
            self._state.ground_truth_yaml
        )
        
        # Check if task is complete (score >= 0.8)
        task_complete = score >= 0.8
        
        if task_complete:
            # Move to next task or end episode
            if self._state.task_number < 3:
                next_task_num = self._state.task_number + 1
                next_task = TASKS[next_task_num]
                
                self._state.task_number = next_task_num
                self._state.original_yaml = next_task["broken"]
                self._state.current_yaml = next_task["broken"]
                self._state.ground_truth_yaml = next_task["fixed"]
                
                return PipelineFixObservation(
                    pipeline_yaml=next_task["broken"],
                    errors=self._get_errors(next_task_num),
                    warnings=[],
                    task_description=next_task["description"],
                    task_number=next_task_num,
                    done=False,
                    reward=score
                )
            else:
                # All tasks complete
                return PipelineFixObservation(
                    pipeline_yaml=action.content,
                    errors=[],
                    warnings=[],
                    task_description="All tasks completed!",
                    task_number=3,
                    done=True,
                    reward=score
                )
        else:
            # Task not complete, provide feedback
            return PipelineFixObservation(
                pipeline_yaml=action.content,
                errors=self._get_errors(self._state.task_number),
                warnings=[f"Score: {score:.2f}/1.0 - Need 0.8+ to proceed"],
                task_description=TASKS[self._state.task_number]["description"],
                task_number=self._state.task_number,
                done=False,
                reward=score
            )
    
    def _get_errors(self, task_number: int) -> list:
        """Get error messages for current task"""
        if task_number == 1:
            return ["YAML indentation error detected"]
        elif task_number == 2:
            return ["Missing Node.js setup", "Missing dependency installation"]
        elif task_number == 3:
            return ["Pipeline not optimized", "Missing caching", "No parallelization"]
        return []
    
    @property
    def state(self) -> State:
        """Get current state"""
        return self._state
