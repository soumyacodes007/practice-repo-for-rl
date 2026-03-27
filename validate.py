"""
Validation script for hackathon compliance.

Checks all required endpoints and functionality.
"""

import requests
import sys
import time

def validate_server(base_url="http://localhost:8000"):
    """Validate all hackathon requirements."""
    
    print("=" * 70)
    print("LLM Text2SQL Failure Gym - Hackathon Validation")
    print("=" * 70)
    print(f"Server: {base_url}\n")
    
    passed = 0
    failed = 0
    
    # Test 1: Health check
    print("1. Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✓ Server responds with 200")
            passed += 1
        else:
            print(f"   ✗ Server returned {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        failed += 1
    
    # Test 2: /tasks endpoint
    print("\n2. Testing /tasks endpoint...")
    try:
        response = requests.get(f"{base_url}/tasks", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "tasks" in data and "action_schema" in data:
                print(f"   ✓ Returns {len(data['tasks'])} tasks")
                print(f"   ✓ Action schema present")
                if len(data['tasks']) >= 3:
                    print(f"   ✓ Has 3+ tasks (requirement met)")
                    passed += 1
                else:
                    print(f"   ✗ Only {len(data['tasks'])} tasks (need 3+)")
                    failed += 1
            else:
                print("   ✗ Missing tasks or action_schema")
                failed += 1
        else:
            print(f"   ✗ Returned {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        failed += 1
    
    # Test 3: /grader endpoint
    print("\n3. Testing /grader endpoint...")
    try:
        test_data = {
            "final_time_ms": 50.0,
            "target_time_ms": 100.0,
            "steps_taken": 3,
            "max_steps": 10
        }
        response = requests.post(f"{base_url}/grader", json=test_data, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "score" in data and 0.0 <= data["score"] <= 1.0:
                print(f"   ✓ Returns score: {data['score']:.2f}")
                print(f"   ✓ Score in range [0.0, 1.0]")
                passed += 1
            else:
                print(f"   ✗ Invalid score format")
                failed += 1
        else:
            print(f"   ✗ Returned {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        failed += 1
    
    # Test 4: /baseline endpoint
    print("\n4. Testing /baseline endpoint...")
    try:
        response = requests.get(f"{base_url}/baseline", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Returns baseline scores")
            if "task_1" in data and "task_2" in data and "task_3" in data:
                print(f"   ✓ Has scores for all 3 tasks")
                passed += 1
            else:
                print(f"   ✗ Missing task scores")
                failed += 1
        else:
            print(f"   ✗ Returned {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        failed += 1
    
    # Test 5: OpenEnv reset
    print("\n5. Testing OpenEnv reset()...")
    try:
        response = requests.post(
            f"{base_url}/reset",
            json={"task_id": 1},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if "observation" in data:
                obs = data["observation"]
                if "slow_query" in obs and "execution_time_ms" in obs:
                    print(f"   ✓ Returns valid observation")
                    print(f"   ✓ Baseline time: {obs['execution_time_ms']:.2f}ms")
                    passed += 1
                else:
                    print(f"   ✗ Invalid observation format")
                    failed += 1
            else:
                print(f"   ✗ Missing observation")
                failed += 1
        else:
            print(f"   ✗ Returned {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        failed += 1
    
    # Test 6: OpenEnv step
    print("\n6. Testing OpenEnv step()...")
    try:
        # First reset
        requests.post(f"{base_url}/reset", json={"task_id": 1}, timeout=10)
        
        # Then step
        response = requests.post(
            f"{base_url}/step",
            json={"action": {"command": "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE user_id=42"}},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if "observation" in data and "reward" in data:
                print(f"   ✓ Returns observation and reward")
                print(f"   ✓ Reward: {data['reward']:.4f}")
                passed += 1
            else:
                print(f"   ✗ Invalid step response")
                failed += 1
        else:
            print(f"   ✗ Returned {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        failed += 1
    
    # Test 7: OpenEnv state
    print("\n7. Testing OpenEnv state()...")
    try:
        response = requests.get(f"{base_url}/state", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "state" in data:
                print(f"   ✓ Returns state")
                passed += 1
            else:
                print(f"   ✗ Invalid state response")
                failed += 1
        else:
            print(f"   ✗ Returned {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    print(f"Passed: {passed}/7")
    print(f"Failed: {failed}/7")
    
    if failed == 0:
        print("\n✓ All validation checks passed!")
        print("✓ Environment is hackathon-compliant")
        return 0
    else:
        print(f"\n✗ {failed} validation check(s) failed")
        print("✗ Fix issues before submission")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate hackathon compliance")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    
    args = parser.parse_args()
    
    # Wait a bit for server to start if just launched
    print("Waiting for server to start...")
    time.sleep(2)
    
    exit_code = validate_server(args.url)
    sys.exit(exit_code)
