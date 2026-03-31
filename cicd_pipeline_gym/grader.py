"""
Grader for CI/CD Pipeline Fixer Gym
Deterministic scoring from 0.0 to 1.0
"""
import yaml
from typing import Dict, Tuple
from difflib import SequenceMatcher


def parse_yaml_safe(yaml_str: str) -> Tuple[bool, Dict]:
    """
    Safely parse YAML string.
    Returns (success, parsed_dict)
    """
    try:
        parsed = yaml.safe_load(yaml_str)
        return True, parsed if parsed else {}
    except yaml.YAMLError:
        return False, {}


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)"""
    return SequenceMatcher(None, str1.strip(), str2.strip()).ratio()


def grade_task_1(submitted: str, ground_truth: str) -> float:
    """
    Grade Task 1 (Easy): YAML syntax fix
    - 0.3 points: Valid YAML syntax
    - 0.7 points: Correct indentation and structure
    """
    score = 0.0
    
    # Check if YAML is valid
    is_valid, parsed = parse_yaml_safe(submitted)
    if is_valid:
        score += 0.3
    
    # Check similarity to ground truth
    similarity = calculate_similarity(submitted, ground_truth)
    score += 0.7 * similarity
    
    return min(1.0, score)


def grade_task_2(submitted: str, ground_truth: str) -> float:
    """
    Grade Task 2 (Medium): Add missing dependencies
    - 0.2 points: Valid YAML
    - 0.4 points: Has setup-node action
    - 0.4 points: Has npm ci or npm install step
    """
    score = 0.0
    
    is_valid, parsed = parse_yaml_safe(submitted)
    if not is_valid:
        return 0.0
    
    score += 0.2  # Valid YAML
    
    submitted_lower = submitted.lower()
    
    # Check for setup-node
    if 'actions/setup-node' in submitted:
        score += 0.4
    
    # Check for dependency installation
    if 'npm ci' in submitted or 'npm install' in submitted:
        score += 0.4
    
    return min(1.0, score)


def grade_task_3(submitted: str, ground_truth: str) -> float:
    """
    Grade Task 3 (Hard): Pipeline optimization
    - 0.2 points: Valid YAML
    - 0.2 points: Has caching (cache: 'npm')
    - 0.2 points: Has multiple jobs (parallelization)
    - 0.2 points: Has job dependencies (needs:)
    - 0.2 points: Has matrix strategy or artifact sharing
    """
    score = 0.0
    
    is_valid, parsed = parse_yaml_safe(submitted)
    if not is_valid:
        return 0.0
    
    score += 0.2  # Valid YAML
    
    # Check for caching
    if "cache:" in submitted or "cache: 'npm'" in submitted:
        score += 0.2
    
    # Check for multiple jobs (parallelization)
    if parsed and 'jobs' in parsed:
        num_jobs = len(parsed['jobs'])
        if num_jobs >= 3:
            score += 0.2
    
    # Check for job dependencies
    if 'needs:' in submitted or 'needs :' in submitted:
        score += 0.2
    
    # Check for matrix strategy or artifacts
    if 'matrix:' in submitted or 'upload-artifact' in submitted:
        score += 0.2
    
    return min(1.0, score)


def grade_pipeline_fix(task_number: int, submitted: str, ground_truth: str) -> float:
    """
    Main grading function.
    Returns score from 0.0 to 1.0 based on task number.
    """
    if task_number == 1:
        return grade_task_1(submitted, ground_truth)
    elif task_number == 2:
        return grade_task_2(submitted, ground_truth)
    elif task_number == 3:
        return grade_task_3(submitted, ground_truth)
    else:
        return 0.0
