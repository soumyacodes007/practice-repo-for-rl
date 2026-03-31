"""
FastAPI server for CI/CD Pipeline Fixer Gym
"""
from openenv.core.env_server import create_app
from ..models import PipelineFixAction, PipelineFixObservation
from .pipeline_environment import PipelineFixerEnvironment

# Create FastAPI app with environment factory
app = create_app(
    PipelineFixerEnvironment,
    PipelineFixAction,
    PipelineFixObservation,
    env_name="cicd_pipeline_gym"
)
