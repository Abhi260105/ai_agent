#!/bin/bash
# Comprehensive test runner script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_MIN=80
PYTEST_ARGS=""
TEST_PATH="tests/"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_PATH="tests/unit/"
            shift
            ;;
        --integration)
            TEST_PATH="tests/integration/"
            shift
            ;;
        --e2e)
            TEST_PATH="tests/e2e/"
            shift
            ;;
        --performance)
            TEST_PATH="tests/performance/"
            shift
            ;;
        --fast)
            PYTEST_ARGS="-x --ff"
            shift
            ;;
        --verbose)
            PYTEST_ARGS="$PYTEST_ARGS -v"
            shift
            ;;
        --coverage)
            PYTEST_ARGS="$PYTEST_ARGS --cov=. --cov-report=html --cov-report=term"
            shift
            ;;
        --parallel)
            PYTEST_ARGS="$PYTEST_ARGS -n auto"
            shift
            ;;
        *)
            TEST_PATH="$1"
            shift
            ;;
    esac
done

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Comprehensive Test Suite${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest not found. Install with: pip install pytest${NC}"
    exit 1
fi

# Setup test environment
echo -e "${YELLOW}Setting up test environment...${NC}"
export TESTING=1
export DATABASE_PATH=":memory:"

# Run linting
echo -e "${BLUE}\nRunning code quality checks...${NC}"
if command -v flake8 &> /dev/null; then
    echo -e "${YELLOW}  - flake8${NC}"
    flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__,*.pyc || true
fi

if command -v black &> /dev/null; then
    echo -e "${YELLOW}  - black (check only)${NC}"
    black --check src/ tests/ || true
fi

if command -v mypy &> /dev/null; then
    echo -e "${YELLOW}  - mypy${NC}"
    mypy src/ --ignore-missing-imports || true
fi

# Run tests
echo -e "${BLUE}\nRunning tests: $TEST_PATH${NC}"
echo -e "${YELLOW}Arguments: pytest $PYTEST_ARGS $TEST_PATH${NC}"
echo ""

if pytest $PYTEST_ARGS $TEST_PATH; then
    echo -e "${GREEN}\n✓ All tests passed!${NC}"
    TEST_RESULT=0
else
    echo -e "${RED}\n✗ Some tests failed${NC}"
    TEST_RESULT=1
fi

# Coverage report
if [[ $PYTEST_ARGS == *"--cov"* ]]; then
    echo -e "${BLUE}\nCoverage Report:${NC}"
    echo -e "${YELLOW}HTML report: htmlcov/index.html${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}================================${NC}"

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}Status: PASSED ✓${NC}"
else
    echo -e "${RED}Status: FAILED ✗${NC}"
fi

exit $TEST_RESULT
