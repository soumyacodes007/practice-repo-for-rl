# WebSocket vs HTTP in OpenEnv: The Full Story

## TL;DR

**OpenEnv DOES recommend WebSocket** - but hackathon judges test via HTTP. This creates a mismatch.

## What OpenEnv Actually Says

From the official OpenEnv documentation:

> "The `EnvClient` maintains a persistent **WebSocket connection** to the server, enabling **efficient multi-step interactions** with **lower latency** compared to HTTP."

> "Each client instance corresponds to a **dedicated environment session** on the server."

### OpenEnv's Recommended Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Your Training Code (Python)                            │
│  ────────────────────────────────────────────────────   │
│  from envs.my_env import MyEnv                          │
│                                                          │
│  env = MyEnv(base_url="ws://localhost:8000")  ← WebSocket!
│  result = env.reset()                                   │
│  result = env.step(action)                              │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │  WebSocket Connection (Persistent)
                  │  Maintains session state server-side
                  │
┌─────────────────▼───────────────────────────────────────┐
│  OpenEnv Server (FastAPI + WebSocket)                   │
│  ────────────────────────────────────────────────────   │
│  - /ws endpoint (WebSocket)                             │
│  - Session management via _sessions dict                │
│  - One environment instance per WebSocket connection    │
└─────────────────────────────────────────────────────────┘
```

## Why OpenEnv Recommends WebSocket

From `OpenEnv/src/openenv/core/env_client.py`:

```python
"""
Environment client for persistent sessions.

This module provides a WebSocket-based client that maintains a persistent connection
to an environment server, enabling efficient multi-step interactions without
the overhead of HTTP request/response cycles.

Features:
- Lower latency for sequential interactions
- Session state is maintained server-side
- Better suited for long-running episodes
- Async by default for modern Python async/await patterns
"""
```

### Benefits of WebSocket

| Feature | WebSocket | HTTP |
|---------|-----------|------|
| **Connection** | Persistent (one connection) | New connection per request |
| **Latency** | Low (no handshake overhead) | Higher (TCP + TLS handshake each time) |
| **Session State** | Built-in via `_sessions` dict | Must implement manually |
| **Overhead** | Minimal after initial connection | Headers + handshake every request |
| **Use Case** | Long episodes, many steps | Stateless APIs, one-off requests |

## So Why Do Hackathons Use HTTP?

### The Mismatch

**OpenEnv's Design:**
- Built for researchers using Python
- Assumes you'll use their `EnvClient` class
- WebSocket provides best performance

**Hackathon Reality:**
- Judges test with simple HTTP requests
- No WebSocket client setup
- Need to work with any HTTP library (curl, requests, etc.)

### Why Judges Prefer HTTP

1. **Simplicity**: Just POST requests, no connection management
2. **Universal**: Works with any language/tool (curl, Postman, requests)
3. **Debugging**: Easy to log and inspect requests/responses
4. **Compatibility**: Works with all RL frameworks without custom clients
5. **Testing**: Can test with simple bash scripts

### Example: Judge's Test Script

```bash
# This is what judges do - simple HTTP
curl -X POST http://your-env:8000/reset -d '{"task_id": 1}'
curl -X POST http://your-env:8000/step -d '{"action": {...}}'
```

vs

```python
# This is what OpenEnv expects - WebSocket client
from envs.my_env import MyEnv
env = MyEnv(base_url="ws://your-env:8000")
env.reset()
env.step(action)
```

## The Problem: HTTP Endpoints Are Stateless

OpenEnv DOES provide HTTP endpoints (`/reset`, `/step`), but they're **stateless by design**:

```python
# From OpenEnv's http_server.py
async def reset_handler(request: ResetRequest) -> ResetResponse:
    _env = self._env_factory()  # NEW instance
    try:
        observation = await _env.reset(**valid_kwargs)
        return ResetResponse(**serialize_observation(observation))
    finally:
        _env.close()  # DESTROYED immediately
```

**What happens:**
1. `/reset` → Creates env → Returns obs → **Destroys env**
2. `/step` → Creates NEW env → No memory of reset → **FAILS**

## The Solution: Custom HTTP Session Management

Since OpenEnv's HTTP endpoints are stateless, you MUST implement your own session management:

```python
# Global session store
sessions: Dict[str, Environment] = {}

@app.post("/reset")
async def reset(request: ResetRequest):
    env = YourEnvironment()
    obs = env.reset()
    sessions[request.session_id] = env  # Store it!
    return obs

@app.post("/step")
async def step(request: StepRequest):
    env = sessions[request.session_id]  # Retrieve it!
    obs = env.step(request.action)
    return obs
```

## Why OpenEnv Doesn't Provide This

OpenEnv is designed for two use cases:

### 1. Interactive Use (WebSocket)
```python
# Researchers using Python
env = MyEnv.from_hub("username/my-env")
with env:
    result = env.reset()
    for _ in range(100):
        result = env.step(action)
```
✅ Session managed by WebSocket connection

### 2. Stateless HTTP APIs
```python
# Each request is independent (like REST APIs)
POST /reset → Get initial state
POST /step → Execute one action (no state)
```
✅ No session needed (stateless by design)

### What's Missing: Stateful HTTP
```python
# What hackathons need
POST /reset → Initialize session
POST /step → Use same session (state persists)
POST /step → Use same session (state persists)
```
❌ Not provided by OpenEnv

## Summary

| Aspect | OpenEnv's Design | Hackathon Reality |
|--------|------------------|-------------------|
| **Recommended** | WebSocket via `EnvClient` | HTTP via curl/requests |
| **Session Management** | Built-in for WebSocket | Must implement for HTTP |
| **Use Case** | Python researchers | Language-agnostic judges |
| **Performance** | Optimal (persistent connection) | Good enough (simple requests) |
| **Complexity** | Higher (WebSocket client) | Lower (just HTTP) |

## What You Need to Do

For hackathon validation, you MUST:

1. ✅ Keep OpenEnv's WebSocket support (for researchers)
2. ✅ Add custom HTTP session management (for judges)
3. ✅ Support both modes simultaneously

This is why the solution in `server/app.py` with the `sessions` dict is necessary - it bridges the gap between OpenEnv's WebSocket-first design and hackathon's HTTP-first validation.

## References

- OpenEnv Documentation: "WebSocket-based client for persistent sessions"
- OpenEnv Source: `src/openenv/core/env_client.py` - WebSocket implementation
- OpenEnv Source: `src/openenv/core/env_server/http_server.py` - Stateless HTTP endpoints
- Your Project: `server/app.py` - Custom HTTP session management
