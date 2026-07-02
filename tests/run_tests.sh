#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Run test layers (L0 / L1 / L2 / E2E)
# Usage:  ./tests/run_tests.sh               # run L0+L1+L2
#         ./tests/run_tests.sh l0             # run only L0
#         ./tests/run_tests.sh l1 l2 e2e      # run L1, L2, E2E
#         ./tests/run_tests.sh all            # run all 4 layers
# 说明: E2E 需目标环境可达 (默认 100.74.141.3)。
# ─────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
E2E_DIR="$PROJECT_ROOT/deploy/tests/e2e"

# Default: run L0+L1+L2
if [ $# -eq 0 ]; then
    LAYERS="l0 l1 l2"
elif [ "${1:-}" = "all" ]; then
    LAYERS="l0 l1 l2 e2e"
else
    LAYERS="$*"
fi

TOTAL_RC=0

for layer in $LAYERS; do
    case "$layer" in
        l0)
            echo ""
            echo "=== L0: Pure Function Tests ==="
            PYTHONPATH="$PROJECT_ROOT/backend" python3 -m pytest "$SCRIPT_DIR/unit/" -q --tb=line 2>&1 | tail -3
            TOTAL_RC=$((TOTAL_RC + ${PIPESTATUS[0]}))
            ;;
        l1)
            echo ""
            echo "=== L1: API Contract Tests ==="
            python3 -m pytest "$SCRIPT_DIR/l1/" -q --tb=line 2>&1 | tail -3
            TOTAL_RC=$((TOTAL_RC + ${PIPESTATUS[0]}))
            ;;
        l2)
            echo ""
            echo "=== L2: Integration Workflow Tests ==="
            python3 -m pytest \
                "$SCRIPT_DIR/l2/test_bi_workflow.py" \
                "$SCRIPT_DIR/l2/test_teaching_workflow.py" \
                "$SCRIPT_DIR/l2/test_exam_workflow.py" \
                "$SCRIPT_DIR/l2/test_student_workflow.py" \
                "$SCRIPT_DIR/l2/test_resource_workflow.py" \
                -q --tb=line 2>&1 | tail -3
            TOTAL_RC=$((TOTAL_RC + ${PIPESTATUS[0]}))
            ;;
        e2e)
            echo ""
            echo "=== E2E: Full-Stack Tests (需 100.74.141.3 可达) ==="
            if [ ! -d "$E2E_DIR" ]; then
                echo "skip: $E2E_DIR 不存在"
            else
                ( cd "$E2E_DIR" && python3 -m pytest -q --tb=line 2>&1 | tail -5 )
                TOTAL_RC=$((TOTAL_RC + ${PIPESTATUS[0]}))
            fi
            ;;
        *)
            echo "Unknown layer: $layer (expected l0, l1, l2, e2e, or all)"
            TOTAL_RC=$((TOTAL_RC + 1))
            ;;
    esac
done

echo ""
if [ "$TOTAL_RC" -eq 0 ]; then
    echo "All layers passed."
else
    echo "Some layers had failures (exit code sum: $TOTAL_RC)."
fi

exit $TOTAL_RC
