"""
Quick test script to verify environment works correctly.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)

# Test imports
print("Testing imports...")
try:
    from models import QueryAction, QueryObservation, QueryState
    print("✓ Models imported")
except Exception as e:
    print(f"✗ Models import failed: {e}")
    sys.exit(1)

try:
    from server.sqlite_backend import SQLiteBackend
    print("✓ SQLite backend imported")
except Exception as e:
    print(f"✗ SQLite backend import failed: {e}")
    sys.exit(1)

try:
    from server.fault_injector import FaultInjector
    print("✓ Fault injector imported")
except Exception as e:
    print(f"✗ Fault injector import failed: {e}")
    sys.exit(1)

try:
    from server.grader import Grader
    print("✓ Grader imported")
except Exception as e:
    print(f"✗ Grader import failed: {e}")
    sys.exit(1)

try:
    from server.environment import LLMQueryOptimizerEnvironment
    print("✓ Environment imported")
except Exception as e:
    print(f"✗ Environment import failed: {e}")
    sys.exit(1)

# Test environment creation
print("\nTesting environment creation...")
try:
    env = LLMQueryOptimizerEnvironment()
    print("✓ Environment created")
except Exception as e:
    print(f"✗ Environment creation failed: {e}")
    sys.exit(1)

# Test reset
print("\nTesting reset...")
try:
    obs = env.reset(task_id=1)
    print(f"✓ Reset successful")
    print(f"  Task: {obs.task_id}")
    print(f"  Baseline time: {obs.execution_time_ms:.2f}ms")
    print(f"  Slow query: {obs.slow_query[:50]}...")
except Exception as e:
    print(f"✗ Reset failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test step
print("\nTesting step...")
try:
    action = QueryAction(command="CREATE INDEX idx_orders_user ON orders(user_id)")
    obs = env.step(action)
    print(f"✓ Step successful")
    print(f"  New time: {obs.execution_time_ms:.2f}ms")
    print(f"  Reward: {obs.reward:.4f}")
    print(f"  Done: {obs.done}")
except Exception as e:
    print(f"✗ Step failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test state
print("\nTesting state...")
try:
    state = env.state
    print(f"✓ State retrieved")
    print(f"  Episode ID: {state.episode_id}")
    print(f"  Steps taken: {state.steps_taken}")
except Exception as e:
    print(f"✗ State retrieval failed: {e}")
    sys.exit(1)

# Cleanup
env.close()

print("\n" + "=" * 50)
print("All tests passed! ✓")
print("=" * 50)
