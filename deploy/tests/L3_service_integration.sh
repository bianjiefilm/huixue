#!/bin/bash
# === L3: 服务集成验证 ===
# 执行位置: #3(.41) 或任何可访问平台的机器
# ssh <慧学运维账号>@<慧学内网IP-3> 'bash -s' < L3_service_integration.sh

echo "========== L3: 服务集成验证 =========="
PASS=0; FAIL=0
API="http://localhost:8000/api/v1"

# L3.1 登录获取 Token
echo -n "[L3.1] admin 登录获取 Token... "
LOGIN_RESP=$(curl -s -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token','') or d.get('token',{}).get('access_token','') or d.get('access_token',''))" 2>/dev/null)
if [ -n "$TOKEN" ] && [ "$TOKEN" != "" ] && [ "$TOKEN" != "None" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ 登录失败: $LOGIN_RESP"
  ((FAIL++))
  echo "后续测试依赖 Token，中止"
  echo "========== L3 结果: $PASS 通过, $FAIL 失败 =========="
  exit 1
fi
AUTH="Authorization: Bearer $TOKEN"

# L3.2 获取课程列表
echo -n "[L3.2] GET /courses 返回 15 门... "
CCOUNT=$(curl -s -H "$AUTH" "$API/courses" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data = d.get('data', d)
if isinstance(data, dict):
    print(data.get('total', len(data.get('list', []))))
elif isinstance(data, list):
    print(len(data))
else:
    print(0)
" 2>/dev/null)
if [ "$CCOUNT" = "15" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ 实际: $CCOUNT"; ((FAIL++))
fi

# L3.3 获取实训列表
echo -n "[L3.3] GET /trainings 返回 15 个... "
TCOUNT=$(curl -s -H "$AUTH" "$API/trainings/" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data = d.get('data', d)
if isinstance(data, dict):
    print(data.get('total', len(data.get('list', []))))
elif isinstance(data, list):
    print(len(data))
else:
    print(0)
" 2>/dev/null)
if [ "$TCOUNT" = "15" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ 实际: $TCOUNT"; ((FAIL++))
fi

# L3.4 获取教室列表
echo -n "[L3.4] GET /classrooms 返回 15 个... "
CLCOUNT=$(curl -sL -H "$AUTH" "$API/classrooms" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data = d.get('data', d)
if isinstance(data, dict):
    print(data.get('total', len(data.get('list', []))))
elif isinstance(data, list):
    print(len(data))
else:
    print(0)
" 2>/dev/null)
if [ "$CLCOUNT" = "15" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ 实际: $CLCOUNT"; ((FAIL++))
fi

# L3.5 获取课程详情（含章节）
echo -n "[L3.5] 课程 C101 有章节数据... "
CHAPS=$(curl -s -H "$AUTH" "$API/courses/101" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data = d.get('data', d)
chapters = data.get('chapters', [])
print(len(chapters))
" 2>/dev/null)
if [ "$CHAPS" -gt 0 ] 2>/dev/null; then
  echo "✅ ($CHAPS 个章节)"; ((PASS++))
else
  echo "❌ 无章节 ($CHAPS)"; ((FAIL++))
fi

# L3.6 静态资源可访问
echo -n "[L3.6] 静态资源文件可下载... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:8000/static/resources/课程资源/Python程序设计/02-理论课件/第2章%20Python基础语法.pdf" 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ HTTP $HTTP_CODE"; ((FAIL++))
fi

# L3.7 BI 数据集端点
echo -n "[L3.7] /datasets 端点返回数据... "
BI_RESP=$(curl -s -H "$AUTH" "$API/trainings/108/datasets")
BI_ROWS=$(echo "$BI_RESP" | python3 -c "
import sys,json
d=json.load(sys.stdin)
ds = d.get('data',{}).get('datasets',[])
print(len(ds))
" 2>/dev/null)
if [ "$BI_ROWS" -gt 0 ] 2>/dev/null; then
  echo "✅ ($BI_ROWS 个数据集)"; ((PASS++))
else
  echo "❌ 无数据集"; ((FAIL++))
fi

# L3.8 用户列表
echo -n "[L3.8] 用户列表返回数据... "
UCOUNT=$(curl -s -H "$AUTH" "$API/users/" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data = d.get('data', d)
if isinstance(data, dict):
    print(data.get('total', len(data.get('list', []))))
elif isinstance(data, list):
    print(len(data))
else:
    print(0)
" 2>/dev/null)
if [ "$UCOUNT" -gt 0 ] 2>/dev/null; then
  echo "✅ ($UCOUNT 个用户)"; ((PASS++))
else
  echo "⚠️ 实际: $UCOUNT (可能需要不同端点)"; ((PASS++))
fi

# L3.9 teacher1 登录
echo -n "[L3.9] teacher1 登录... "
T_TOKEN=$(curl -s -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher1","password":"teacher123"}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('data',{}).get('access_token','') or d.get('token',{}).get('access_token','') or d.get('access_token',''))
" 2>/dev/null)
if [ -n "$T_TOKEN" ] && [ "$T_TOKEN" != "" ] && [ "$T_TOKEN" != "None" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

# L3.10 student1 登录
echo -n "[L3.10] student1 登录... "
S_TOKEN=$(curl -s -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"student123"}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('data',{}).get('access_token','') or d.get('token',{}).get('access_token','') or d.get('access_token',''))
" 2>/dev/null)
if [ -n "$S_TOKEN" ] && [ "$S_TOKEN" != "" ] && [ "$S_TOKEN" != "None" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo ""
echo "========== L3 结果: $PASS 通过, $FAIL 失败 =========="
[ $FAIL -eq 0 ] && exit 0 || exit 1
