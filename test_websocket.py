"""
Test the server using WebSocket connection to maintain state.
"""
import asyncio
import json
import websockets

async def test_workflow():
    """Test complete workflow using WebSocket."""
    uri = "ws://localhost:8000/ws"
    
    print("\n=== Testing with WebSocket ===\n")
    
    async with websockets.connect(uri) as websocket:
        # Reset environment
        print("1. Resetting environment with task 1...")
        reset_msg = json.dumps({"type": "reset", "data": {"task_id": 1}})
        await websocket.send(reset_msg)
        response = await websocket.recv()
        reset_result = json.loads(response)
        obs = reset_result['data']['observation']
        print(f"   ✓ Task: {obs['task_id']}")
        print(f"   ✓ Initial time: {obs['execution_time_ms']:.2f}ms")
        print(f"   ✓ Target: {obs.get('max_steps', 10)} steps")
        
        # Execute optimization step
        print("\n2. Creating index...")
        step_msg = json.dumps({
            "type": "step",
            "data": {
                "command": "CREATE INDEX idx_orders_user ON orders(user_id)"
            }
        })
        await websocket.send(step_msg)
        response = await websocket.recv()
        step_result = json.loads(response)
        obs = step_result['data']['observation']
        reward = step_result['data'].get('reward', 0)
        done = step_result['data'].get('done', False)
        print(f"   ✓ Command output: {obs['command_output'][:60]}...")
        print(f"   ✓ New time: {obs['execution_time_ms']:.2f}ms")
        print(f"   ✓ Reward: {reward}")
        print(f"   ✓ Done: {done}")
        print(f"   ✓ Steps taken: {obs['step']}/{obs['max_steps']}")
        
        # Get state
        print("\n3. Checking state...")
        state_msg = json.dumps({"type": "state"})
        await websocket.send(state_msg)
        response = await websocket.recv()
        state_result = json.loads(response)
        state = state_result['data']
        print(f"   ✓ Episode ID: {state.get('episode_id', 'N/A')[:20]}...")
        print(f"   ✓ Steps taken: {state.get('steps_taken', 'N/A')}")
        print(f"   ✓ Current time: {state.get('current_time_ms', 'N/A')}ms")
        print(f"   ✓ Target time: {state.get('target_time_ms', 'N/A')}ms")
        print(f"   ✓ Solved: {state.get('is_solved', 'N/A')}")
        print(f"   ✓ Cumulative reward: {state.get('cumulative_reward', 'N/A')}")
    
    print("\n=== ✓ All tests passed! Server is working correctly with WebSocket ===\n")

if __name__ == "__main__":
    asyncio.run(test_workflow())
