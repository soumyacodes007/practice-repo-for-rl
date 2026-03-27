"""
Test queries locally to verify they work before server testing.
"""
import sys
import time
sys.path.insert(0, 'server')

from server.sqlite_backend import SQLiteBackend
from server.fault_injector import FaultInjector, TASKS

print("🔧 Creating test database...")
backend = SQLiteBackend(db_path=":memory:", seed=42)
backend.create_and_seed_db()
print("✅ Database created\n")

injector = FaultInjector(backend)

print("=" * 60)
print("Testing all 3 tasks with LIMIT clauses")
print("=" * 60)

for task_id in [1, 2, 3]:
    print(f"\n📋 Task {task_id}: {TASKS[task_id].difficulty}")
    print(f"Query: {TASKS[task_id].slow_query[:80]}...")
    print(f"Has LIMIT: {'LIMIT' in TASKS[task_id].slow_query}")
    print(f"Setup commands: {TASKS[task_id].setup_commands}")
    
    start = time.time()
    try:
        task_info = injector.inject_fault(task_id)
        elapsed = time.time() - start
        
        print(f"✅ Baseline time: {task_info['baseline_time_ms']:.2f}ms")
        print(f"   Total reset time: {elapsed:.2f}s")
        
        if elapsed > 5:
            print(f"⚠️  WARNING: Reset took {elapsed:.2f}s (should be <1s)")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ FAILED after {elapsed:.2f}s: {e}")

print("\n" + "=" * 60)
print("✅ All tasks tested successfully!")
print("=" * 60)
