# OpenEnv Hackathon Validation Checklist

## What the Validation Script Tests

The official validation script (`validate-submission.sh`) performs 3 checks:

### ✅ Step 1: HTTP `/reset` Endpoint Test
```bash
curl -X POST https://your-space.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{}' \
  --max-time 30
```

**Expected**: HTTP 200 response

**This confirms**: Your environment MUST work via HTTP, not just WebSocket!

### ✅ Step 2: Docker Build
```bash
docker build <your-dockerfile-directory>
```

**Expected**: Build succeeds within 600 seconds

### ✅ Step 3: OpenEnv Validate
```bash
cd <your-repo> && openenv validate
```

**Expected**: All validation checks pass

## Your Action Plan

### For the SQL Query Optimizer (`server/`)

#### 1. Verify HTTP Session Management is Working

Test locally:
```bash
# Start your server
cd server
uvicorn app:app --host 0.0.0.0 --port 8000

# In another terminal, test HTTP endpoints
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "session_id": "test123"}'

# Should return observation with task details

curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123",
    "action": {"command": "CREATE INDEX idx_orders_user ON orders(user_id)"}
  }'

# Should return observation with execution time and reward
```

**Expected**: Both requests succeed, state persists between them.

#### 2. Check Required Endpoints

Your `server/app.py` should have:
- ✅ `POST /reset` - Initialize environment (with session management)
- ✅ `POST /step` - Execute action (with session management)
- ✅ `GET /health` - Health check
- ✅ `GET /metadata` - Environment metadata
- ✅ `GET /schema` - JSON schemas
- ✅ `GET /state` - Current state (optional but recommended)

#### 3. Verify Docker Build

```bash
cd server
docker build -t llm-query-optimizer:test .
```

**Expected**: Build succeeds

#### 4. Test with Validation Script

```bash
# Download the script
curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/validate-submission.sh -o validate-submission.sh
chmod +x validate-submission.sh

# Run against your local server
./validate-submission.sh http://localhost:8000 ./server
```

### For the CI/CD Pipeline Fixer (`cicd_pipeline_gym/`)

#### 1. Apply the Same HTTP Session Management Fix

Your `cicd_pipeline_gym/server/app.py` currently uses:
```python
app = create_app(
    PipelineFixerEnvironment,
    PipelineFixAction,
    PipelineFixObservation,
    env_name="cicd_pipeline_gym"
)
```

**This is BROKEN for HTTP!** You need to add session management like in `server/app.py`.

#### 2. Update `cicd_pipeline_gym/server/app.py`

Replace the entire file with custom session management:

```python
"""
FastAPI server for CI/CD Pipeline Fixer Gym with HTTP session management.
"""
import logging
from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cicd_pipeline_gym.server.pipeline_environment import PipelineFixerEnvironment
from cicd_pipeline_gym.models import PipelineFixAction, PipelineFixObservation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CI/CD Pipeline Fixer Gym")

# Global session store for HTTP state management
sessions: Dict[str, PipelineFixerEnvironment] = {}

class ResetRequest(BaseModel):
    session_id: str = Field(default="default")

class StepRequest(BaseModel):
    action: PipelineFixAction
    session_id: str = Field(default="default")

@app.post("/reset")
async def reset(request: ResetRequest):
    """Reset environment with session management."""
    session_id = request.session_id
    logger.info(f"Reset called for session: {session_id}")
    
    # Create fresh environment
    env = PipelineFixerEnvironment()
    obs = env.reset()
    
    # Store in session
    sessions[session_id] = env
    logger.info(f"Session {session_id} created")
    
    return {
        "observation": obs.model_dump(),
        "reward": None,
        "done": False
    }

@app.post("/step")
async def step(request: StepRequest):
    """Execute step with session management."""
    session_id = request.session_id
    logger.info(f"Step called for session: {session_id}")
    
    # Retrieve existing environment
    if session_id not in sessions:
        raise HTTPException(
            status_code=400,
            detail="Session not found. Call /reset first."
        )
    
    env = sessions[session_id]
    obs = env.step(request.action)
    
    # Clean up if done
    if obs.done:
        logger.info(f"Episode done, cleaning up session {session_id}")
        del sessions[session_id]
    
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward,
        "done": obs.done,
        "info": {}
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "active_sessions": len(sessions)}

@app.get("/metadata")
async def metadata():
    return {
        "name": "cicd-pipeline-fixer-gym",
        "description": "RL environment for fixing CI/CD pipeline configurations",
        "version": "0.1.0"
    }

@app.get("/schema")
async def schema():
    return {
        "action": PipelineFixAction.model_json_schema(),
        "observation": PipelineFixObservation.model_json_schema()
    }
```

#### 3. Test Both Environments

```bash
# Test SQL Query Optimizer
curl -X POST http://localhost:8000/reset -d '{"task_id": 1, "session_id": "test1"}'
curl -X POST http://localhost:8000/step -d '{"session_id": "test1", "action": {...}}'

# Test CI/CD Pipeline Fixer
curl -X POST http://localhost:8001/reset -d '{"session_id": "test2"}'
curl -X POST http://localhost:8001/step -d '{"session_id": "test2", "action": {...}}'
```

## Common Issues and Fixes

### Issue 1: `/reset` returns 200 but `/step` fails
**Cause**: No session management - environment destroyed after `/reset`
**Fix**: Implement `sessions` dict as shown above

### Issue 2: Docker build times out
**Cause**: Large dependencies or slow network
**Fix**: 
- Use Docker layer caching
- Pre-download large datasets
- Optimize Dockerfile

### Issue 3: `openenv validate` fails
**Cause**: Missing required files or incorrect structure
**Fix**: Ensure you have:
- `openenv.yaml` with correct metadata
- `models.py` with Action/Observation classes
- `server/app.py` with FastAPI endpoints
- `README.md` with documentation

## Final Pre-Submission Checklist

Before running the validation script:

- [ ] HTTP `/reset` endpoint works (returns 200)
- [ ] HTTP `/step` endpoint works (returns 200)
- [ ] State persists between `/reset` and `/step` calls
- [ ] Session management implemented (not using OpenEnv's stateless HTTP)
- [ ] Docker image builds successfully
- [ ] All required endpoints exist (`/health`, `/metadata`, `/schema`)
- [ ] `openenv validate` passes locally
- [ ] HuggingFace Space is deployed and running
- [ ] Space URL is accessible from browser

## Running the Validation Script

```bash
# Against your HuggingFace Space
./validate-submission.sh https://your-username-your-env.hf.space

# Against local server (for testing)
./validate-submission.sh http://localhost:8000 ./server
```

**Expected output:**
```
========================================
  OpenEnv Submission Validator
========================================
[HH:MM:SS] Repo:     /path/to/your/repo
[HH:MM:SS] Ping URL: https://your-space.hf.space

[HH:MM:SS] Step 1/3: Pinging HF Space ...
[HH:MM:SS] PASSED -- HF Space is live and responds to /reset

[HH:MM:SS] Step 2/3: Running docker build ...
[HH:MM:SS] PASSED -- Docker build succeeded

[HH:MM:SS] Step 3/3: Running openenv validate ...
[HH:MM:SS] PASSED -- openenv validate passed

========================================
  All 3/3 checks passed!
  Your submission is ready to submit.
========================================
```

## If Validation Fails

### Step 1 Fails (HTTP /reset)
1. Check if your Space is running on HuggingFace
2. Test locally: `curl -X POST http://localhost:8000/reset -d '{}'`
3. Verify session management is implemented
4. Check server logs for errors

### Step 2 Fails (Docker build)
1. Test locally: `docker build server/`
2. Check Dockerfile syntax
3. Verify all dependencies are available
4. Increase timeout if needed

### Step 3 Fails (openenv validate)
1. Run locally: `cd server && openenv validate --verbose`
2. Check error messages
3. Verify `openenv.yaml` exists and is valid
4. Ensure all required files are present

## Summary

The validation script confirms that **HTTP session management is REQUIRED**. Your environments must:

1. ✅ Respond to HTTP POST `/reset` (not just WebSocket)
2. ✅ Maintain state across multiple HTTP requests
3. ✅ Use `session_id` parameter to track sessions
4. ✅ Build successfully in Docker
5. ✅ Pass `openenv validate` checks

The solution we implemented in `server/app.py` with the `sessions` dict is exactly what's needed to pass validation!
