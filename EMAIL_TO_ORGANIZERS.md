Subject: Clarification Needed: HTTP Session Management for Multi-Step RL Environments

Dear OpenEnv Hackathon Organizers,

I'm working on a multi-step RL environment for the hackathon and need clarification on session management for HTTP endpoints, as I've received conflicting information.

## The Issue

My environment requires multiple sequential steps per episode:
1. `POST /reset` - Initialize task (e.g., "optimize this slow SQL query")
2. `POST /step` - Execute action 1 (e.g., "CREATE INDEX...")
3. `POST /step` - Execute action 2 (if needed)
4. Continue until `done=True`

Each step needs access to episode state from reset (task info, baseline metrics, action history, etc.) to calculate rewards correctly.

## The Contradiction

**The validation script (`validate-submission.sh`) tests HTTP endpoints:**
```bash
curl -X POST "$PING_URL/reset" -H "Content-Type: application/json" -d '{}'
```

**However, OpenEnv's `create_app()` HTTP handlers are stateless** (from `src/openenv/core/env_server/http_server.py`):
```python
async def reset_handler(request: ResetRequest) -> ResetResponse:
    _env = self._env_factory()  # Creates new env
    try:
        observation = await _env.reset(**valid_kwargs)
        return ResetResponse(**serialize_observation(observation))
    finally:
        _env.close()  # Destroys env immediately

async def step_handler(request: StepRequest) -> StepResponse:
    _env = self._env_factory()  # Creates another new env
    try:
        observation = await _env.step(action, **valid_kwargs)
        return StepResponse(**serialize_observation(observation))
    finally:
        _env.close()  # Destroys env immediately
```

This means each HTTP request creates and destroys a new environment instance, losing all episode state between `/reset` and `/step` calls.

## My Implementation

To maintain state across HTTP requests, I implemented custom session management:

```python
# server/app.py
sessions: Dict[str, Environment] = {}

@app.post("/reset")
async def reset(request: ResetRequest):
    env = MyEnvironment()
    obs = env.reset(task_id=request.task_id)
    sessions[request.session_id] = env  # Store environment
    return {"observation": obs.model_dump(), "done": False}

@app.post("/step")
async def step(request: StepRequest):
    if request.session_id not in sessions:
        raise HTTPException(400, "Session not found. Call /reset first.")
    
    env = sessions[request.session_id]  # Retrieve same environment
    obs = env.step(request.action)
    
    if obs.done:
        del sessions[request.session_id]  # Cleanup
    
    return {"observation": obs.model_dump(), "reward": obs.reward, "done": obs.done}
```

## The Mod's Guidance

A moderator stated:
> "You do NOT need to replace it with your own HTTP implementation. Do NOT override /step, /reset, etc. Stick with create_app(...) as provided. OpenEnv handles the abstraction for you — the evaluator will interact via HTTP, and your environment should work correctly through the default setup."

However, this contradicts the source code behavior where HTTP endpoints are stateless.

## My Questions

1. **Does the Phase 2 evaluator use HTTP or WebSocket?**
   - If HTTP: How does state persist between `/reset` and `/step` calls with `create_app()`?
   - If WebSocket: Why does the validation script test HTTP endpoints?

2. **Is custom HTTP session management required or not?**
   - The validation script suggests HTTP is used
   - The source code shows HTTP endpoints are stateless
   - But the mod says not to implement custom session management

3. **How should multi-step episodes work over HTTP?**
   - Should environments maintain state at the class level?
   - Should we pass `episode_id` in every request?
   - Or is there a mechanism in `create_app()` I'm missing?

4. **Can you provide an example of how the evaluator calls environments?**
   - This would clarify whether HTTP or WebSocket is used
   - And how state is expected to persist across calls

## Why This Matters

Without session management:
- Environment forgets which task it's solving between `/reset` and `/step`
- Can't calculate rewards (no baseline to compare against)
- Can't track episode progress (step count, action history)
- Multi-step episodes fail completely

With my custom session management:
- All tests pass locally
- State persists correctly across HTTP requests
- Episodes complete successfully

## Request

Could you please clarify:
1. The correct approach for HTTP session management
2. Whether custom session management is needed or if `create_app()` handles it
3. How the Phase 2 evaluator actually interacts with environments (HTTP vs WebSocket)

I want to ensure my submission follows the correct pattern and will work with your evaluation pipeline.

Thank you for your help!

Best regards,
[Your Name]
[Your Team Name]

---

## Technical Details (for reference)

**Environment**: Multi-step RL environment for SQL query optimization
**OpenEnv Version**: [Your version]
**Repository**: [Your repo URL if applicable]
**HuggingFace Space**: [Your space URL if deployed]

**Test Case**:
```bash
# With create_app() only (stateless):
curl -X POST http://localhost:8000/reset -d '{"task_id": 1}'
# Returns observation

curl -X POST http://localhost:8000/step -d '{"action": {"command": "CREATE INDEX..."}}'
# Fails - new env instance has no memory of reset

# With custom session management:
curl -X POST http://localhost:8000/reset -d '{"task_id": 1, "session_id": "test"}'
# Returns observation, stores env

curl -X POST http://localhost:8000/step -d '{"session_id": "test", "action": {"command": "CREATE INDEX..."}}'
# Works - retrieves same env instance, calculates reward correctly
```
