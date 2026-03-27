"""
Baseline script for LLM Text2SQL Failure Gym.

Uses OpenAI API to optimize SQL queries and establish baseline scores.
"""

import os
import sys
from openai import OpenAI

# Import environment client
sys.path.insert(0, os.path.dirname(__file__))
from models import QueryAction
from client import LLMQueryOptimizerClient


def run_baseline(env_url: str = "http://localhost:8000", model: str = "gpt-4o-mini"):
    """
    Run baseline evaluation using OpenAI API.
    
    Args:
        env_url: URL of the OpenEnv server
        model: OpenAI model to use
    """
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your-key-here")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    print("=" * 70)
    print("LLM Text2SQL Failure Gym - Baseline Evaluation")
    print("=" * 70)
    print(f"Environment: {env_url}")
    print(f"Model: {model}")
    print()
    
    # Connect to environment
    env = LLMQueryOptimizerClient(base_url=env_url)
    
    # Run each task
    task_scores = {}
    
    for task_id in [1, 2, 3]:
        print(f"\n{'=' * 70}")
        print(f"Task {task_id}")
        print(f"{'=' * 70}")
        
        # Reset environment
        obs = env.reset(task_id=task_id)
        
        print(f"Description: {obs.task_description}")
        print(f"Slow Query: {obs.slow_query}")
        print(f"Baseline Time: {obs.execution_time_ms:.2f}ms")
        print(f"Target Time: 100ms")  # Fixed target time
        print()
        
        episode_reward = 0.0
        done = False
        
        while not done:
            # Build prompt for LLM
            history_str = "\n".join([f"  {i+1}. {cmd}" for i, cmd in enumerate(obs.history)])
            
            prompt = f"""You are a SQL query optimization expert. Fix this slow query.

Task: {obs.task_description}

Slow Query:
{obs.slow_query}

Current Execution Time: {obs.execution_time_ms:.2f}ms
Target Time: 100ms

Query Plan:
{obs.query_plan}

Commands executed so far:
{history_str if history_str else "  (none)"}

Step {obs.step}/{obs.max_steps}

Provide ONE SQL command to optimize this query. Options:
1. CREATE INDEX idx_name ON table(column) - Add an index
2. SELECT ... - Rewrite the query more efficiently
3. ANALYZE table - Update statistics
4. EXPLAIN QUERY PLAN SELECT ... - Analyze query plan

Respond with ONLY the SQL command, no explanation."""

            # Get LLM response
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a SQL optimization expert. Respond with only SQL commands."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,  # Deterministic
                    max_tokens=200
                )
                
                command = response.choices[0].message.content.strip()
                
                # Clean up markdown code blocks if present
                if command.startswith("```"):
                    lines = command.split("\n")
                    command = "\n".join([l for l in lines if not l.startswith("```")])
                    command = command.strip()
                
                print(f"Step {obs.step + 1}: {command[:80]}...")
                
                # Execute action
                obs = env.step(QueryAction(command=command))
                
                episode_reward += obs.reward
                done = obs.done
                
                print(f"  Time: {obs.execution_time_ms:.2f}ms, Reward: {obs.reward:.4f}")
                
                if done:
                    target_times = {1: 100, 2: 200, 3: 150}
                    if obs.execution_time_ms <= target_times.get(task_id, 100):
                        print(f"  ✓ Task solved!")
                    else:
                        print(f"  ✗ Task not solved (max steps reached)")
                
            except Exception as e:
                print(f"  Error: {e}")
                break
        
        # Compute final score
        final_score = episode_reward / obs.max_steps if obs.max_steps > 0 else 0.0
        task_scores[task_id] = final_score
        
        print(f"\nTask {task_id} Results:")
        print(f"  Final Time: {obs.execution_time_ms:.2f}ms")
        print(f"  Total Reward: {episode_reward:.4f}")
        print(f"  Score: {final_score:.4f}")
    
    # Summary
    print(f"\n{'=' * 70}")
    print("Baseline Summary")
    print(f"{'=' * 70}")
    for task_id, score in task_scores.items():
        print(f"Task {task_id}: {score:.4f}")
    
    avg_score = sum(task_scores.values()) / len(task_scores)
    print(f"\nAverage Score: {avg_score:.4f}")
    print()
    
    env.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run baseline evaluation")
    parser.add_argument("--env-url", default="http://localhost:8000", help="Environment URL")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model")
    
    args = parser.parse_args()
    
    run_baseline(env_url=args.env_url, model=args.model)
