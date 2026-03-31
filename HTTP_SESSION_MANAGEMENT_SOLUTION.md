# HTTP Session Management Solution for OpenEnv Environments

## Why Not Use WebSockets?

**TL;DR**: Hackathon judges test via HTTP, not WebSocket. If your environment only works via WebSocket, you fail validation.

### The WebSocket vs HTTP Issue

| Aspect | WebSocket | HTTP |
|--------|-----------|------|
| **Connection** | Persistent, bidirectional | Request/response, stateless |
| **Session Management** | Built-in via OpenEnv's `_sessions` dict | Not provided by OpenEnv |
| **Hackathon Validation** | ❌ Judges don't use WebSocket | ✅ Judges use HTTP endpoints |
| **Training Compatibility** | ⚠️ Requires WebSocket client | ✅ Works with standard HTTP libraries |
| **Simplicity** | More complex (connection management) | Simpler (just POST requests) |

### Why Judges Use HTTP

1. **Standardization**: HTTP is universal - works with curl, requests, any HTTP client
2. **Simplicity**: No connection management, reconnection logic, or WebSocket libraries needed
3. **Compatibility**: Works with all RL training frameworks (Stable-Baselines3, RLlib, etc.)
4. **Testing**: Easy to test with curl or Postman
5. **Debugging**: HTTP requests/responses are easier to log and debug

### Example: Judge's Test Script

```python
import requests

# This is what judges do - simple HTTP requests
response = requests.post("http://your-env:8000/reset", json={"task_id": 1})
obs = response.json()

for _ in range(10):
    response = requests.post("http://your-env:8000/step", 
                            json={"action": {"command": "..."}})
    obs = response.json()
    if obs["done"]:
        break
```

If your environment requires WebSocket, this test fails immediately.

### What Happens If You Use WebSocket

```python
# WebSocket approach (what OpenEnv provides)
from openenv import EnvClient

client = EnvClient("ws://your-env:8000/ws")  # WebSocket connection
obs = client.reset(task_id=1)
for _ in range(10):
    obs = client.step(action={"command": "..."})
    if obs.done:
        break
client.close()
```

**Problems:**
1. ❌ Judges don't have WebSocket client code
2. ❌ Requires persistent connection (fails if connection drops)
3. ❌ More complex error handling (reconnection, timeouts)
4. ❌ Harder to test with standard tools (curl doesn't support WebSocket)
5. ❌ **You fail Phase 1 validation automatically**

### The Real Issue from Your Project

From your conversation history, the problem was:

```python
# Your initial app.py (BROKEN for HTTP)
from openenv.core.env_server import create_app

app = create_app(
    PipelineFixerEnvironment,
    PipelineFixAction,
    PipelineFixObservation,
    env_name="cicd_pipeline_gym"
)
```

**What happened:**
- `/reset` via HTTP → Creates env → Returns obs → **Destroys env**
- `/step` via HTTP → Creates NEW env → No memory of reset → **FAILS**
- `/ws` via WebSocket → Works perfectly (OpenEnv's built-in session management)

**Judge's test:**
```bash
curl -X POST http://localhost:8000/reset -d '{"task_id": 1}'  # Works
curl -X POST http://localhost:8000/step -d '{"action": {...}}'  # FAILS - no session
```

**Result**: ❌ Validation failed - environment doesn't maintain state across HTTP requests

## The Problem

OpenEnv's `create_app()` creates a **NEW environment instance for EVERY HTTP request**:

```python
# In OpenEnv's http_server.py reset_handler:
async def reset_handler(request: ResetRequest) -> ResetResponse:
    _env = self._env_factory()  # NEW instance created
    try:
        observation = await _env.reset(**valid_kwargs)
        return ResetResponse(**serialize_observation(observation))
    finally:
        _env.close()  # Instance destroyed immediately
```

This means:
- `/reset` creates env → returns observation → **destroys env**
- `/step` creates NEW env → has **no memory** of previous reset → **fails**

## Why This Happens

OpenEnv has TWO modes:
1. **WebSocket mode**: Uses internal `_sessions` dict for persistent state
2. **HTTP mode**: Creates/destroys env per request (stateless by design)

For hackathon judges testing via HTTP, you MUST implement your own session management.

## The Solution: In-Memory Session Store

### Step 1: Add Global Session Dictionary

```python
from typing import Dict
from fastapi import FastAPI, HTTPException

# Global session store
sessions: Dict[str, YourEnvironment] = {}
```

### Step 2: Modify Request Models

```python
from pydantic import BaseModel, Field

class ResetRequest(BaseModel):
    task_id: int = Field(default=1)
    session_id: str = Field(default="default")  # ADD THIS

class StepRequest(BaseModel):
    action: YourAction
    session_id: str = Field(default="default")  # ADD THIS
```

### Step 3: Modify /reset Endpoint

```python
@app.post("/reset")
async def reset(request: ResetRequest):
    session_id = request.session_id
    
    # Create fresh environment
    env = YourEnvironment()
    obs = env.reset(task_id=request.task_id)
    
    # CRITICAL: Store in memory
    sessions[session_id] = env
    
    return {
        "observation": obs.model_dump(),
        "reward": None,
        "done": False
    }
```

### Step 4: Modify /step Endpoint

```python
@app.post("/step")
async def step(request: StepRequest):
    session_id = request.session_id
    
    # CRITICAL: Retrieve existing environment
    if session_id not in sessions:
        raise HTTPException(
            status_code=400,
            detail="Session not found. Call /reset first with the same session_id."
        )
    
    env = sessions[session_id]  # Get SAME instance
    obs = env.step(request.action)
    
    # Clean up when done
    if obs.done:
        env.close()
        del sessions[session_id]
    
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward,
        "done": obs.done,
        "info": {}
    }
```

## How OpenEnv Examples Handle This

**IMPORTANT**: After checking ALL OpenEnv example environments (git_env, finrl_env, wildfire_env, openspiel_env, textarena_env, unity_env, etc.), **NONE of them implement custom HTTP session management**.

They all use the **factory function** pattern:

```python
# git_env/server/app.py
def create_git_environment():
    """Factory function that creates GitTaskEnvironment with config."""
    return GitTaskEnvironment(
        gitea_url=gitea_url,
        username=gitea_username,
        password=gitea_password,
        workspace_dir=workspace_dir,
    )

# Pass factory function (not class) to create_app
app = create_app(create_git_environment, GitAction, GitObservation, env_name="git_env")
```

This works because:
- **WebSocket connections**: OpenEnv's internal `_sessions` dict manages state
- **HTTP requests**: Each request gets a fresh environment (stateless by design)

### Why This is a Problem for Hackathons

OpenEnv examples are designed for:
1. **Interactive use** - Users connect via WebSocket and maintain session
2. **Stateless APIs** - Each HTTP request is independent (like REST APIs)

But hackathon judges test via **HTTP with stateful expectations**:
- Call `/reset` to initialize environment
- Call `/step` multiple times expecting state to persist
- This requires custom session management that OpenEnv doesn't provide

**Conclusion**: For HTTP-based hackathon validation, you MUST implement custom session management as shown in this document. This is NOT provided by OpenEnv's `create_app()`.

## Testing Your Implementation

```bash
# 1. Reset with session ID
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "session_id": "test123"}'

# 2. Step with SAME session ID
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123",
    "action": {"command": "CREATE INDEX idx_orders_user ON orders(user_id)"}
  }'

# 3. Verify state persists
curl -X GET "http://localhost:8000/state?session_id=test123"
```

## Key Takeaways

1. **OpenEnv's `create_app()` is stateless for HTTP** - creates/destroys env per request
2. **WebSocket mode has built-in session management** - but judges use HTTP
3. **NO OpenEnv examples implement HTTP session management** - they all rely on WebSocket or stateless HTTP
4. **You MUST implement your own session store** for HTTP-based validation
5. **Use `session_id` parameter** to track environment instances across requests
6. **Clean up sessions** when episode is done to prevent memory leaks

## Comparison: OpenEnv vs Custom Session Management

| Feature | OpenEnv `create_app()` | Custom Session Management |
|---------|------------------------|---------------------------|
| **WebSocket Support** | ✅ Built-in via `_sessions` dict | ✅ Can add if needed |
| **HTTP Stateful Sessions** | ❌ Creates new env per request | ✅ Persists env across requests |
| **Session ID Tracking** | ❌ Not supported for HTTP | ✅ Via `session_id` parameter |
| **Memory Management** | ✅ Auto cleanup after request | ⚠️ Manual cleanup required |
| **Hackathon Compatible** | ❌ Fails HTTP validation | ✅ Passes HTTP validation |
| **Use Case** | Interactive WebSocket apps | HTTP-based RL training/testing |

## When to Use Each Approach

### Use OpenEnv's `create_app()` when:
- Users interact via WebSocket (web UI, interactive sessions)
- HTTP requests are truly stateless (each request is independent)
- You don't need state persistence across HTTP calls

### Use Custom Session Management when:
- Judges/validators test via HTTP (hackathons, competitions)
- Training loops call `/reset` once, then `/step` many times
- You need state to persist across multiple HTTP requests
- You're building an RL environment for HTTP-based agents

## Files Modified

- `server/app.py` - Added session management
- `models.py` - Added `session_id` to ResetRequest and StepRequest (if needed)

This pattern works for ANY OpenEnv environment that needs HTTP session persistence!
