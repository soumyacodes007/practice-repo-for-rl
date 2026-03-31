"""
CI/CD Pipeline Tasks - 3 difficulty levels
"""

# Task 1: Easy - Fix YAML syntax errors
TASK_1_BROKEN = """name: CI Pipeline
on:
  push:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: npm test
      - name: Build
      run: npm run build
"""

TASK_1_FIXED = """name: CI Pipeline
on:
  push:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: npm test
      - name: Build
        run: npm run build
"""

TASK_1_DESCRIPTION = """Fix the YAML syntax error in this GitHub Actions pipeline. 
There is an indentation issue that will prevent the pipeline from running."""


# Task 2: Medium - Add missing dependencies
TASK_2_BROKEN = """name: Node.js CI
on:
  push:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: npm test
      - name: Build
        run: npm run build
"""

TASK_2_FIXED = """name: Node.js CI
on:
  push:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
      - name: Build
        run: npm run build
"""

TASK_2_DESCRIPTION = """This pipeline is missing critical setup steps. Add the necessary 
Node.js setup and dependency installation steps before running tests."""


# Task 3: Hard - Optimize pipeline with caching and parallelization
TASK_3_BROKEN = """name: Full CI/CD
on:
  push:
    branches: [ main ]
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run linter
        run: npm run lint
      - name: Run unit tests
        run: npm run test:unit
      - name: Run integration tests
        run: npm run test:integration
      - name: Build
        run: npm run build
      - name: Deploy
        run: echo "Deploying..."
"""

TASK_3_FIXED = """name: Full CI/CD
on:
  push:
    branches: [ main ]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Run linter
        run: npm run lint
  
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-type: [unit, integration]
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm run test:${{ matrix.test-type }}
  
  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Build
        run: npm run build
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: build
          path: dist/
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v3
        with:
          name: build
      - name: Deploy
        run: echo "Deploying..."
"""

TASK_3_DESCRIPTION = """Optimize this pipeline for speed and efficiency. Add:
1. npm caching to speed up dependency installation
2. Parallel job execution (lint and tests should run in parallel)
3. Matrix strategy for running different test types
4. Proper job dependencies (build should wait for tests, deploy should wait for build)
5. Artifact sharing between jobs"""


TASKS = {
    1: {
        "broken": TASK_1_BROKEN,
        "fixed": TASK_1_FIXED,
        "description": TASK_1_DESCRIPTION,
        "difficulty": "easy"
    },
    2: {
        "broken": TASK_2_BROKEN,
        "fixed": TASK_2_FIXED,
        "description": TASK_2_DESCRIPTION,
        "difficulty": "medium"
    },
    3: {
        "broken": TASK_3_BROKEN,
        "fixed": TASK_3_FIXED,
        "description": TASK_3_DESCRIPTION,
        "difficulty": "hard"
    }
}
