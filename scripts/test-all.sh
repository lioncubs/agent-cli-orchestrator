#!/bin/bash
# Unified test runner for Agent CLI Orchestrator
# Runs backend pytest, frontend vitest, and Playwright E2E tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Agent CLI Orchestrator Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"

# Parse arguments
RUN_BACKEND=true
RUN_FRONTEND=true
RUN_E2E=true
HEADED=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --backend-only) RUN_FRONTEND=false; RUN_E2E=false ;;
        --frontend-only) RUN_BACKEND=false; RUN_E2E=false ;;
        --e2e-only) RUN_BACKEND=false; RUN_FRONTEND=false ;;
        --no-e2e) RUN_E2E=false ;;
        --headed) HEADED=true ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --backend-only   Run only backend tests"
            echo "  --frontend-only  Run only frontend unit tests"
            echo "  --e2e-only       Run only E2E tests"
            echo "  --no-e2e         Skip E2E tests"
            echo "  --headed         Run E2E tests in headed mode"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

cd "$PROJECT_DIR"

# Track test results
BACKEND_RESULT=0
FRONTEND_RESULT=0
E2E_RESULT=0

# Create test directories
echo -e "\n${YELLOW}Creating test directories...${NC}"
mkdir -p test-data test-logs/copilot test-worktrees

# Export test config
export CONFIG_FILE=config.test.yaml

# Run backend tests
if [ "$RUN_BACKEND" = true ]; then
    echo -e "\n${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}  Running Backend Tests (pytest)${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"
    
    if python -m pytest tests/ -v --tb=short -n auto 2>&1; then
        echo -e "${GREEN}✓ Backend tests passed${NC}"
    else
        BACKEND_RESULT=1
        echo -e "${RED}✗ Backend tests failed${NC}"
    fi
fi

# Run frontend unit tests
if [ "$RUN_FRONTEND" = true ]; then
    echo -e "\n${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}  Running Frontend Unit Tests (vitest)${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"
    
    cd frontend
    if npm run test -- --run 2>&1; then
        echo -e "${GREEN}✓ Frontend unit tests passed${NC}"
    else
        FRONTEND_RESULT=1
        echo -e "${RED}✗ Frontend unit tests failed${NC}"
    fi
    cd "$PROJECT_DIR"
fi

# Run E2E tests
if [ "$RUN_E2E" = true ]; then
    echo -e "\n${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}  Running E2E Tests (Playwright)${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"
    
    cd frontend
    
    E2E_CMD="npm run test:e2e:chromium"
    if [ "$HEADED" = true ]; then
        E2E_CMD="npm run test:e2e:headed"
    fi
    
    if $E2E_CMD 2>&1; then
        echo -e "${GREEN}✓ E2E tests passed${NC}"
    else
        E2E_RESULT=1
        echo -e "${RED}✗ E2E tests failed${NC}"
    fi
    cd "$PROJECT_DIR"
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"

TOTAL_RESULT=0

if [ "$RUN_BACKEND" = true ]; then
    if [ $BACKEND_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Backend tests: PASSED${NC}"
    else
        echo -e "${RED}✗ Backend tests: FAILED${NC}"
        TOTAL_RESULT=1
    fi
fi

if [ "$RUN_FRONTEND" = true ]; then
    if [ $FRONTEND_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend unit tests: PASSED${NC}"
    else
        echo -e "${RED}✗ Frontend unit tests: FAILED${NC}"
        TOTAL_RESULT=1
    fi
fi

if [ "$RUN_E2E" = true ]; then
    if [ $E2E_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ E2E tests: PASSED${NC}"
    else
        echo -e "${RED}✗ E2E tests: FAILED${NC}"
        TOTAL_RESULT=1
    fi
fi

echo -e "${BLUE}========================================${NC}"

if [ $TOTAL_RESULT -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed!${NC}"
fi

exit $TOTAL_RESULT
