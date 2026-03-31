"""
Test script for CI/CD Pipeline Fixer Gym
Validates environment without requiring OpenAI API
"""
from cicd_pipeline_gym.server.pipeline_environment import PipelineFixerEnvironment
from cicd_pipeline_gym.models import PipelineFixAction
from cicd_pipeline_gym.tasks import TASKS
from cicd_pipeline_gym.grader import grade_pipeline_fix


def test_environment():
    """Test environment with ground truth solutions"""
    print("=" * 60)
    print("Testing CI/CD Pipeline Fixer Gym")
    print("=" * 60)
    
    env = PipelineFixerEnvironment()
    obs = env.reset()
    
    print(f"\n✅ Environment initialized")
    print(f"   Episode ID: {env.state.episode_id}")
    print(f"   Initial task: {obs.task_number}")
    
    # Test all 3 tasks with ground truth
    for task_num in range(1, 4):
        print(f"\n{'='*60}")
        print(f"Task {task_num}: {TASKS[task_num]['difficulty'].upper()}")
        print(f"{'='*60}")
        print(f"Description: {TASKS[task_num]['description'][:80]}...")
        
        # Submit ground truth solution
        action = PipelineFixAction(
            fix_type=f"task_{task_num}_fix",
            content=TASKS[task_num]["fixed"],
            explanation="Ground truth solution"
        )
        
        obs = env.step(action)
        
        print(f"✅ Reward: {obs.reward:.3f}")
        print(f"   Errors: {obs.errors}")
        print(f"   Warnings: {obs.warnings}")
        print(f"   Done: {obs.done}")
        
        # Verify grading
        score = grade_pipeline_fix(task_num, TASKS[task_num]["fixed"], TASKS[task_num]["fixed"])
        assert score >= 0.8, f"Ground truth should score >= 0.8, got {score}"
        print(f"✅ Grader validation passed (score: {score:.3f})")
    
    print(f"\n{'='*60}")
    print("✅ ALL TESTS PASSED")
    print(f"{'='*60}")
    print(f"Final state:")
    print(f"  - Episode ID: {env.state.episode_id}")
    print(f"  - Steps taken: {env.state.step_count}")
    print(f"  - Fixes applied: {len(env.state.fixes_applied)}")
    print(f"  - Episode done: {obs.done}")


def test_grader():
    """Test grader with various inputs"""
    print("\n" + "=" * 60)
    print("Testing Grader Functions")
    print("=" * 60)
    
    # Test Task 1 grader
    print("\n📋 Task 1 Grader:")
    score = grade_pipeline_fix(1, TASKS[1]["fixed"], TASKS[1]["fixed"])
    print(f"   Ground truth: {score:.3f} (expected: ~1.0)")
    assert score >= 0.95, f"Expected >= 0.95, got {score}"
    
    score = grade_pipeline_fix(1, TASKS[1]["broken"], TASKS[1]["fixed"])
    print(f"   Broken YAML: {score:.3f} (expected: <0.8)")
    
    # Test Task 2 grader
    print("\n📋 Task 2 Grader:")
    score = grade_pipeline_fix(2, TASKS[2]["fixed"], TASKS[2]["fixed"])
    print(f"   Ground truth: {score:.3f} (expected: 1.0)")
    assert score == 1.0, f"Expected 1.0, got {score}"
    
    score = grade_pipeline_fix(2, TASKS[2]["broken"], TASKS[2]["fixed"])
    print(f"   Missing deps: {score:.3f} (expected: <0.5)")
    
    # Test Task 3 grader
    print("\n📋 Task 3 Grader:")
    score = grade_pipeline_fix(3, TASKS[3]["fixed"], TASKS[3]["fixed"])
    print(f"   Ground truth: {score:.3f} (expected: 1.0)")
    assert score == 1.0, f"Expected 1.0, got {score}"
    
    score = grade_pipeline_fix(3, TASKS[3]["broken"], TASKS[3]["fixed"])
    print(f"   Unoptimized: {score:.3f} (expected: <0.6)")
    
    print("\n✅ All grader tests passed!")


if __name__ == "__main__":
    test_grader()
    test_environment()
    print("\n🎉 Environment is ready for deployment!")
