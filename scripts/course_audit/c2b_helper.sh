#!/usr/bin/env bash
set -euo pipefail

SCHOOL_HOST="${SCHOOL_HOST:-<慧学运维账号>@<慧学服务器1-IP>}"
SCHOOL_API_BASE="${SCHOOL_API_BASE:-http://localhost:3000/api}"
STUDENT_USERNAME="${STUDENT_USERNAME:-student1}"
STUDENT_PASSWORD="${STUDENT_PASSWORD:-student123}"
STUDENT_USER_ID="${STUDENT_USER_ID:-5}"

student_token_via_ssh() {
  ssh "$SCHOOL_HOST" "python3 - <<'PY'
import json
import urllib.request

payload = json.dumps({'username': '$STUDENT_USERNAME', 'password': '$STUDENT_PASSWORD'}).encode()
req = urllib.request.Request(
    '$SCHOOL_API_BASE/login',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read().decode())
print(data['token']['access_token'])
PY"
}

evaluate_via_ssh() {
  local task_id="$1"
  local code_file="$2"
  local user_id="${3:-$STUDENT_USER_ID}"

  if [[ ! -f "$code_file" ]]; then
    echo "code file not found: $code_file" >&2
    return 2
  fi

  local code_b64
  code_b64="$(base64 < "$code_file" | tr -d '\n')"

  ssh "$SCHOOL_HOST" "CODE_B64='$code_b64' TASK_ID='$task_id' USER_ID='$user_id' API_BASE='$SCHOOL_API_BASE' python3 - <<'PY'
import base64
import json
import os
import urllib.request

login_payload = json.dumps({'username': '$STUDENT_USERNAME', 'password': '$STUDENT_PASSWORD'}).encode()
login_req = urllib.request.Request(
    os.environ['API_BASE'] + '/login',
    data=login_payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(login_req, timeout=20) as resp:
    token = json.loads(resp.read().decode())['token']['access_token']

code = base64.b64decode(os.environ['CODE_B64']).decode()
payload = json.dumps({'code': code}).encode()
url = f\"{os.environ['API_BASE']}/v1/tasks/{os.environ['TASK_ID']}/evaluate?user_id={os.environ['USER_ID']}\"
req = urllib.request.Request(
    url,
    data=payload,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    },
    method='POST',
)
with urllib.request.urlopen(req, timeout=90) as resp:
    print(resp.read().decode())
PY"
}

audit_ui_via_browser_use() {
  cat <<'EOF'
Browser Use UI check template:
1. Navigate to http://<慧学服务器1-IP>:3000/#/course/challenge/<practice_id>/<task_id>
2. Wait for the task title or challenge page DOM.
3. Capture DOM snapshot.
4. Look for score/result/history signals: "评测结果", "提交记录", "得分", "score", "passed_tests", or route-specific visible result text.
5. Compare the visible result against the SSH POST result (stub fail / ref pass).
EOF
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  case "${1:-}" in
    token)
      student_token_via_ssh
      ;;
    eval)
      evaluate_via_ssh "$2" "$3" "${4:-$STUDENT_USER_ID}"
      ;;
    ui-template)
      audit_ui_via_browser_use
      ;;
    *)
      echo "Usage:"
      echo "  $0 token"
      echo "  $0 eval <task_id> <code_file> [user_id]"
      echo "  $0 ui-template"
      exit 2
      ;;
  esac
fi
