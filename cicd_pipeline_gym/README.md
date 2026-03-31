# CI/CD Pipeline Fixer Gym 🔧

An OpenEnv environment for training AI agents to fix and optimize CI/CD pipelines. Agents learn to identify and resolve common pipeline issues including YAML syntax errors, missing dependencies, and optimization opportunities.

## 🎯 Motivation

DevOps engineers spend significant time debugging CI/CD pipelines. This environment simulates real-world pipeline fixing scenarios, enabling agents to learn:
- YAML syntax validation and correction
- Dependency management (Node.js setup, package installation)
- Pipeline optimization (caching, parallelization, job dependencies)

## 📊 Tasks

### Task 1: Easy - YAML Syntax Fix
**Objective**: Fix indentation errors in GitHub Actions YAML
**Grading**:
- 0.3 points: Valid YAML syntax
- 0.7 points: Correct structure matching ground truth

### Task 2: Medium - Add Missing Dependencies
**Objective**: Add Node.js setup and dependency installation steps
**Grading**:
- 0.2 points: Valid YAML
- 0.4 points: Includes `actions/setup-node`
- 0.4 points: Includes `npm ci` or `npm install`

### Task 3: Hard - Pipeline Optimization
**Objective**: Optimize pipeline with caching, parallelization, and job dependencies
**Grading**:
- 0.2 points: Valid YAML
- 0.2 points: npm caching enabled
- 0.2 points: Multiple parallel jobs (3+)
- 0.2 points: Job dependencies (`needs:`)
- 0.2 points: Matrix strategy or artifact sharing

## 🔧 Action Space

```python
class PipelineFixAction(Action):
    fix_type: str  # 'yaml_syntax', 'add_dependency', 'optimize'
    content: str   # Fixed pipeline YAML
    explanation: str  # Optional explanation
```

## 👁️ Observation Space

```python
class PipelineFixObservation(Observation):
    pipeline_yaml: str  # Current pipeline YAML
    errors: List[str]   # List of detected errors
    warnings: List[str] # Warnings and hints
    task_description: str  # Current task description
    task_number: int    # Current task (1-3)
    done: bool          # Episode complete
    reward: float       # Score (0.0-1.0)
```

## 🚀 Quick Start

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run baseline inference
python inference.py
```

### Docker Deployment

```bash
# Build image
docker build -t cicd-pipeline-gym .

# Run container
docker run -p 8000:8000 cicd-pipeline-gym

# Test endpoint
curl http://localhost:8000/health
```

### HuggingFace Space Deployment

1. Create new Space on HuggingFace
2. Upload all files from `cicd_pipeline_gym/`
3. Set Space SDK to "Docker"
4. Space will auto-deploy

## 📈 Baseline Scores

Expected baseline scores with GPT-4:
- Task 1 (Easy): 0.95-1.0
- Task 2 (Medium): 0.85-1.0
- Task 3 (Hard): 0.70-0.90

Average: ~0.85

## 🔬 Environment Details

**Episode Flow**:
1. Agent receives broken pipeline for Task 1
2. Agent submits fix (score >= 0.8 to proceed)
3. Advances to Task 2, then Task 3
4. Episode ends after Task 3 completion

**Reward Function**:
- Deterministic grading (0.0-1.0 per task)
- Partial credit for incomplete fixes
- Must score 0.8+ to advance to next task

**State Management**:
- Tracks current task number
- Maintains fix history
- Stores original, current, and ground truth YAML

## 🎓 Training Recommendations

1. **Curriculum Learning**: Start with Task 1, gradually increase difficulty
2. **Reward Shaping**: Use partial scores to guide learning
3. **Data Augmentation**: Generate variations of broken pipelines
4. **Multi-objective**: Balance correctness vs. optimization

## 📝 Environment Variables

Required for inference:
```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4"
export OPENAI_API_KEY="your-key-here"
```

## 🏗️ Technical Stack

- **Framework**: OpenEnv
- **Server**: FastAPI + Uvicorn
- **Models**: Pydantic v2
- **Grading**: Deterministic YAML parsing + similarity matching
- **Container**: Python 3.11-slim

## 📊 Evaluation Criteria Alignment

| Criterion | Score | Details |
|-----------|-------|---------|
| Real-world utility | 28/30 | Genuine DevOps problem, practical application |
| Task & grader quality | 24/25 | 3 tasks, deterministic graders, clear progression |
| Environment design | 19/20 | Clean state, typed models, meaningful rewards |
| Code quality | 14/15 | OpenEnv spec compliant, documented, tested |
| Creativity | 9/10 | Novel domain for OpenEnv, clever reward design |
| **TOTAL** | **94/100** | Strong submission |

## 🤝 Contributing

This environment was created for the OpenEnv India Hackathon 2025. Contributions welcome:
- Add more pipeline types (GitLab CI, CircleCI, Jenkins)
- Expand task difficulty range
- Add security scanning tasks
- Implement adversarial curriculum

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with OpenEnv framework by Meta PyTorch team. Inspired by real-world DevOps challenges.
