Subject: HTTP Session Management Question for Multi-Step RL Environments

Hi OpenEnv Team,

I need clarification on session management for HTTP endpoints in multi-step RL environments.

**The Issue:**
My environment requires multiple sequential HTTP calls per episode (reset → step → step → done). However, OpenEnv's `create_app()` HTTP handlers create and destroy a new environment instance for each request, losing all episode state.

**The Contradiction:**
- The validation script tests HTTP: `curl -X POST "$PING_URL/reset"`
- OpenEnv's HTTP handlers are stateless (each request creates/destroys env)
- A mod said: "Do NOT override /step, /reset. Stick with create_app()"
- But without session management, step() has no memory of reset()

**My Questions:**
1. Does the Phase 2 evaluator use HTTP or WebSocket?
2. Is custom HTTP session management required?
3. How should state persist between /reset and /step calls?

**Current Situation:**
- With `create_app()` only: Step fails (no session state)
- With custom session management: Everything works

Could you clarify the correct approach? I want to ensure my submission works with your evaluation pipeline.

**Test case:**
```bash
# Without session management:
curl -X POST /reset -d '{"task_id": 1}'  # Works
curl -X POST /step -d '{"action": {...}}'  # Fails - no context

# With session management:
curl -X POST /reset -d '{"task_id": 1, "session_id": "test"}'  # Works
curl -X POST /step -d '{"session_id": "test", "action": {...}}'  # Works
```

Thanks!
[Your Name]
