#!/bin/bash
# ─────────────────────────────────────────────────────────────
# 全栈回归：L0 + L1 + L2 + E2E
# 产出 pass/skip/xfail 汇总，用作合并门禁基线
# 用法：  ./run_regression.sh
# ─────────────────────────────────────────────────────────────
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LOG=$(mktemp /tmp/regression.XXXXXX.log)
echo "log → $LOG"
echo

bash tests/run_tests.sh all 2>&1 | tee "$LOG"
RC=$?

echo ""
echo "════════════════════════════════════════════════════════════"
echo "回归汇总"
echo "════════════════════════════════════════════════════════════"
grep -E "^===|passed|failed|error|xfailed|xpassed|skipped" "$LOG" \
  | grep -v "warnings summary" \
  | awk '/^===/ {print} /passed|failed|error|xfailed|xpassed|skipped/ {print "  " $0}'

if [ $RC -eq 0 ]; then
    echo "✅ 全栈绿"
else
    echo "⛔ 回归失败 (rc=$RC)"
fi

exit $RC
