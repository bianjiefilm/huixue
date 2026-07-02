#!/usr/bin/env python3
"""
PPTX 全文下载端到端测试
遵循 AI Agent 闭环验证铁律 v1.1

闭环三要素：
  1. 输入可构造：teacher1 凭证 + classroom_id + file_id → 独立发起合法请求
  2. 结果可观测：HTTP 200 + Content-Length + ZIP PK header + EOCD 签名
  3. 同源原则：走 /static/resources/* (nginx proxy → backend StaticFiles)，与前端完全一致

覆盖范围：
  - 前端教学资源页面中注册的所有 19 个真实 PPTX 文件
  - 链路: nginx(/static) → backend(StaticFiles) → ziyuan_data/*.pptx
  - 验证: 状态码 + Content-Type + 文件大小 + ZIP 结构完整性
"""

import urllib.request
import urllib.parse
import json
import sys
import os

# ── 配置 ────────────────────────────────────────────────────────────────────
BACKEND_BASE = "http://localhost:3000"   # 前端 nginx（Docker），触发完整链路
TOKEN = None

# 19 个真实 PPTX 文件（从数据库 resource_files 表中查询得到，classroom_id 100-117）
# 格式: (file_id, name, url, classroom_id, expected_min_size)
PPTX_FILES = [
    # 数据清洗 (8个)
    (7151, "数据清洗课程_视频1_缺失值处理.pptx",
     "/static/resources/课程资源/数据清洗/视频和课件/数据清洗课程_视频1_缺失值处理.pptx",
     100, 290_000),
    (7152, "数据清洗课程_视频5_文本清洗.pptx",
     "/static/resources/课程资源/数据清洗/视频和课件/数据清洗课程_视频5_文本清洗.pptx",
     101, 1_000_000),
    (7153, "数据清洗课程_视频2_异常值检测.pptx",
     "/static/resources/课程资源/数据清洗/视频和课件/数据清洗课程_视频2_异常值检测.pptx",
     102, 240_000),
    (7154, "神经网络课程_视频3_深度神经网络架构.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频3_深度神经网络架构.pptx",
     103, 320_000),
    (7155, "神经网络课程_视频9_迁移学习.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频9_迁移学习.pptx",
     104, 380_000),
    (7156, "神经网络课程_视频7_图像分类实战CIFAR10.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频7_图像分类实战CIFAR10.pptx",
     105, 390_000),
    (7157, "神经网络课程_视频1_感知机与激活函数.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频1_感知机与激活函数.pptx",
     106, 310_000),
    (7158, "神经网络课程_视频6_PyTorch框架实战.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频6_PyTorch框架实战.pptx",
     107, 430_000),
    (7159, "数据清洗课程_视频4_数据类型转换.pptx",
     "/static/resources/课程资源/数据清洗/视频和课件/数据清洗课程_视频4_数据类型转换.pptx",
     108, 210_000),
    (7160, "神经网络课程_视频10_模型部署.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频10_模型部署.pptx",
     109, 260_000),
    (7161, "神经网络课程_视频4_卷积神经网络.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频4_卷积神经网络.pptx",
     110, 330_000),
    (7162, "神经网络课程_视频2_反向传播算法.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频2_反向传播算法.pptx",
     111, 300_000),
    (7163, "神经网络课程_视频5_循环神经网络与LSTM.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频5_循环神经网络与LSTM.pptx",
     112, 310_000),
    (7164, "数据清洗课程_视频6_数据标准化与归一化.pptx",
     "/static/resources/课程资源/数据清洗/视频和课件/数据清洗课程_视频6_数据标准化与归一化.pptx",
     113, 230_000),
    (7165, "数据清洗课程_视频7_数据一致性校验.pptx",
     "/static/resources/课程资源/数据清洗/视频和课件/数据清洗课程_视频7_数据一致性校验.pptx",
     114, 200_000),
    (7166, "数据清洗课程_视频3_重复值处理.pptx",
     "/static/resources/课程资源/数据清洗/视频和课件/数据清洗课程_视频3_重复值处理.pptx",
     115, 180_000),
    (7167, "数据清洗课程_视频8_端到端清洗流水线.pptx",
     "/static/resources/课程资源/数据清洗/视频和课件/数据清洗课程_视频8_端到端清洗流水线.pptx",
     116, 320_000),
    (7168, "神经网络课程_视频8_文本分类实战.pptx",
     "/static/resources/课程资源/神经网络与深度学习/视频和课件/神经网络课程_视频8_文本分类实战.pptx",
     117, 390_000),
    # 根目录测试文件
    (4, "E2E_Test_Dummy.pptx",
     "/static/resources/E2E_Test_Dummy.pptx",
     100, 1_000_000),
]


def login() -> str:
    """获取 teacher1 JWT token（同前端 userLogin 走同一路径 /api/login）"""
    data = json.dumps({"username": "teacher1", "password": "teacher123"}).encode()
    req = urllib.request.Request(
        f"{BACKEND_BASE}/api/login",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    token = result["token"]["access_token"]
    print(f"  [登录] teacher1 ✓ (role=teacher, id={result['user']['id']})")
    return token


def check_zip_integrity(data: bytes, name: str) -> tuple[bool, str]:
    """
    验证 ZIP 文件完整性（PPTX 是 ZIP 格式）。
    闭环判据 2: 结果可观测
    """
    if len(data) < 4:
        return False, f"文件太短({len(data)}B)，不是有效 ZIP"

    # 1. 检查 ZIP Local File Header 签名: PK\x03\x04
    if data[:4] != b"PK\x03\x04":
        return False, f"缺少 ZIP 头签名 PK\\x03\\x04，实际: {data[:4].hex()}"

    # 2. 检查 ZIP End of Central Directory 签名: PK\x05\x06
    #    EOCD 在文件末尾，前 4 字节为签名
    if len(data) < 22:
        return False, f"文件太短({len(data)}B)，无法包含 EOCD"
    eocd_sig = data[-22:-18]
    if eocd_sig != b"PK\x05\x06":
        return False, (
            f"缺少 ZIP Central Directory End 签名 PK\\x05\\x06，"
            f"文件被截断！实际末尾4字节: {eocd_sig.hex()} "
            f"(这是黑屏根因：JSZip 解析不完整 ZIP → 静默崩溃)"
        )

    return True, "ZIP 结构完整 (PK\\x03\\x04 header + PK\\x05\\x06 EOCD)"


def test_pptx_download(file_id: int, name: str, url: str,
                       classroom_id: int, min_size: int) -> dict:
    """
    闭环验证单个 PPTX 文件下载。
    遵循铁律三要素：
      1. 输入可构造：{classroom_id, file_id, url, token}
      2. 结果可观测：状态码 + Content-Length + ZIP 完整性
      3. 同源原则：走 /static/resources/* 与前端 previewFile() 完全一致
    """
    # 构造 URL：中文路径需要 URL 编码（与前端 axios.get(getPreviewUrl()) 行为一致）
    encoded_path = urllib.parse.quote(url, safe="/:")
    full_url = BACKEND_BASE + encoded_path

    req = urllib.request.Request(full_url)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")

    errors = []
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        status = resp.status
        headers = dict(resp.headers)

        # ── 断言 1: HTTP 200 ──────────────────────────────────────────────
        if status != 200:
            errors.append(f"HTTP {status} != 200")

        # ── 断言 2: Content-Type 是 PPTX ──────────────────────────────────
        ct = headers.get("Content-Type", "")
        if "presentation" not in ct and "octet-stream" not in ct:
            errors.append(f"Content-Type={ct}（期望含 presentation 或 octet-stream）")

        # ── 断言 3: Content-Length 存在且合理 ───────────────────────────────
        cl_str = headers.get("Content-Length") or headers.get("content-length", "")
        try:
            cl = int(cl_str)
        except (ValueError, TypeError):
            errors.append(f"无法解析 Content-Length: {cl_str!r}")
            cl = 0

        if cl < min_size:
            errors.append(
                f"Content-Length={cl} < 预期最小值 {min_size}，文件被截断！"
            )

        # ── 断言 4: 文件内容完整（读取全部 body） ──────────────────────────
        data = resp.read()
        actual_size = len(data)

        if actual_size != cl and cl > 0:
            errors.append(
                f"下载 size={actual_size} != Content-Length={cl}，数据不完整"
            )

        if actual_size < min_size:
            errors.append(
                f"实际下载 {actual_size}B < 预期最小值 {min_size}B，文件被截断！"
            )

        # ── 断言 5: ZIP 结构完整性 ────────────────────────────────────────
        zip_ok, zip_msg = check_zip_integrity(data, name)
        if not zip_ok:
            errors.append(f"ZIP 完整性: {zip_msg}")

        passed = len(errors) == 0
        return {
            "file_id": file_id,
            "name": name,
            "classroom_id": classroom_id,
            "url": url,
            "status": status,
            "content_length": cl,
            "actual_size": actual_size,
            "content_type": ct,
            "zip_check": zip_msg,
            "passed": passed,
            "errors": errors,
        }

    except urllib.error.HTTPError as e:
        return {
            "file_id": file_id,
            "name": name,
            "classroom_id": classroom_id,
            "url": url,
            "status": e.code,
            "error": f"HTTP {e.code}: {e.reason}",
            "passed": False,
            "errors": [f"HTTP {e.code} {e.reason}"],
        }
    except Exception as e:
        return {
            "file_id": file_id,
            "name": name,
            "classroom_id": classroom_id,
            "url": url,
            "status": 0,
            "error": str(e),
            "passed": False,
            "errors": [str(e)],
        }


def main():
    global TOKEN
    print("=" * 80)
    print("PPTX 全文下载端到端测试 — 闭环验证铁律 v1.1")
    print("=" * 80)

    # ── Step 1: 登录（获取凭证）─────────────────────────────────────────
    print("\n[Step 1] 登录 teacher1（构造输入）")
    try:
        TOKEN = login()
    except Exception as e:
        print(f"  [登录失败] {e}")
        sys.exit(1)

    # ── Step 2: 遍历 19 个 PPTX 文件 ───────────────────────────────────
    print(f"\n[Step 2] 下载 {len(PPTX_FILES)} 个 PPTX 文件（验证输出）")
    results = []
    for i, (file_id, name, url, classroom_id, min_size) in enumerate(PPTX_FILES):
        print(f"\n  [{i+1:02d}/{len(PPTX_FILES)}] {name}", end=" ... ", flush=True)
        r = test_pptx_download(file_id, name, url, classroom_id, min_size)
        results.append(r)
        if r["passed"]:
            print(f"✓ {r['actual_size']:,}B | {r['content_type'][:40]}")
            print(f"            ZIP: {r['zip_check']}")
        else:
            print(f"✗ FAIL")
            for err in r.get("errors", []):
                print(f"            ! {err}")

    # ── Step 3: 汇总报告 ─────────────────────────────────────────────────
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    print("\n" + "=" * 80)
    print(f"结果汇总: {passed}/{len(results)} 通过", end="")
    if failed == 0:
        print(" ✅")
    else:
        print(f" ❌ ({failed} 个失败)")

    # 找出失败项
    failed_results = [r for r in results if not r["passed"]]
    if failed_results:
        print("\n失败详情:")
        for r in failed_results:
            print(f"  - [{r['classroom_id']}] {r['name']} (id={r['file_id']})")
            for err in r.get("errors", []):
                print(f"      {err}")

    print("=" * 80)

    # ── Step 4: 写验证清单文件（信源原则）───────────────────────────────
    checklist_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", ".verify-checklist.md"
    )
    checklist_path = os.path.normpath(checklist_path)

    with open(checklist_path, "w") as f:
        f.write("# 视觉验证清单 — PPTX 全文下载修复\n\n")
        f.write("**验证时间**: 2026-03-27\n")
        f.write("**测试工具**: `backend/tests/test_pptx_download_e2e.py`\n")
        f.write("**链路**: 浏览器 → nginx(/static) → backend(StaticFiles) → ziyuan_data/*.pptx\n\n")
        f.write("## API 层验证结果\n\n")
        f.write(f"| # | 文件名 | 课堂 | 文件ID | 状态 | 大小 | ZIP完整性 | 通过 |\n")
        f.write(f"|---|--------|------|--------|------|------|-----------|------|\n")
        for r in results:
            status_str = str(r.get("status", "?"))
            size_str = f"{r.get('actual_size', 0):,}" if r.get("actual_size") else r.get("content_length", "?")
            zip_str = r.get("zip_check", "N/A")[:30]
            pass_str = "✅" if r["passed"] else "❌"
            fname = r["name"][:30]
            f.write(f"| {r['file_id']} | {fname} | {r['classroom_id']} | {r['file_id']} "
                    f"| {status_str} | {size_str} | {zip_str} | {pass_str} |\n")

        f.write("\n## 预期（外化的闭环判据）\n\n")
        f.write("- [ ] 所有 19 个 PPTX 文件 HTTP 200\n")
        f.write("- [ ] 所有 Content-Type 含 presentation 或 octet-stream\n")
        f.write("- [ ] 所有 Content-Length ≥ 预期最小值（无截断）\n")
        f.write("- [ ] 所有文件 ZIP header (PK\\x03\\x04) + EOCD (PK\\x05\\x06) 完整\n")
        f.write("  - 这是修复的核心目标：确保 ZIP 尾部不被截断，JSZip 不崩溃\n")
        f.write("- [ ] 浏览器教学资源页面可正常预览 PPTX（无黑屏）\n\n")
        f.write("## 修复内容\n\n")
        f.write("1. `frontend/nginx.conf`: 新增 `location /static` 代理到 `huixue-backend:8000`\n")
        f.write("2. `frontend/vite.config.ts`: `/static` 代理 rewrite 从 environments proxy 改为直接 StaticFiles 路径\n")
        f.write("3. Docker nginx 配置已同步更新并 reload\n")
        f.write("4. 根因: nginx 缺少 `/static` location，`try_files` fallback 到前端 HTML，PPTX 被替换为 HTML → JSZip 崩溃\n\n")

    print(f"\n[Step 4] 验证清单已写入: {checklist_path}")

    # ── Step 5: exit code ───────────────────────────────────────────────
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
