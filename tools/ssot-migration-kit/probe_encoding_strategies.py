#!/usr/bin/env python3
"""
乱码文件名恢复探针 — 多策略暴力测试
====================================
对残余的 178 个乱码文件名, 用 7 种不同策略尝试恢复,
打印每种策略的结果供人工比对选择最佳方案。
"""

import os
import sys
import time
import codecs

BASE_DIR = "/Users/jimfu/Work/huixue/ziyuan_normalized/B_Legacy_Materials/courses"

# 乱码特征字符
GARBLED_CHARS = set('鏁鎬瑙绗鍩鐨鏂杩涓鍒绠鎿鑳鎺灏渚锛瀹褰鏈缁鎸鍔缂閰嶇疆鎸囧崡绯荤粺')

print("=" * 70, flush=True)
print("乱码恢复探针 — 7 策略并行测试", flush=True)
print("=" * 70, flush=True)

# 收集残余乱码文件名 (只取文件名部分, 去掉扩展名)
samples = set()
for root, dirs, files in os.walk(BASE_DIR):
    for name in dirs + files:
        if any(c in name for c in GARBLED_CHARS):
            # 提取乱码片段 (去掉数字/字母/标点/已知中文)
            samples.add(name)

print(f"\n📊 残余乱码文件: {len(samples)} 个", flush=True)

# 提取所有独特的乱码片段
garbled_fragments = set()
for name in samples:
    fragment = ""
    for c in name:
        if c in GARBLED_CHARS or (ord(c) > 0x4e00 and c in name):
            fragment += c
        else:
            if fragment and len(fragment) >= 2:
                garbled_fragments.add(fragment)
            fragment = ""
    if fragment and len(fragment) >= 2:
        garbled_fragments.add(fragment)

# 取前 15 个独特片段做测试
test_fragments = sorted(garbled_fragments, key=len, reverse=True)[:15]

print(f"📎 提取独特乱码片段: {len(garbled_fragments)} 个, 测试前 15 个", flush=True)

# ====== 7 种恢复策略 ======

def strategy_1_utf8_to_gbk(s):
    """策略1: encode('utf-8') → decode('gbk')"""
    try:
        return s.encode('utf-8').decode('gbk')
    except: return None

def strategy_2_utf8_to_gb18030(s):
    """策略2: encode('utf-8') → decode('gb18030')"""
    try:
        return s.encode('utf-8').decode('gb18030')
    except: return None

def strategy_3_latin1_bridge(s):
    """策略3: encode('latin-1') → decode('gbk')"""
    try:
        return s.encode('latin-1').decode('gbk')
    except: return None

def strategy_4_raw_utf8_bytes_as_gbk(s):
    """策略4: 逐字符取 UTF-8 字节, 整体当 GBK 解"""
    try:
        raw = s.encode('utf-8')
        return raw.decode('gbk', errors='replace')
    except: return None

def strategy_5_double_utf8(s):
    """策略5: encode('utf-8') → decode('utf-8') 双重UTF-8"""
    try:
        raw = s.encode('raw_unicode_escape')
        return raw.decode('utf-8')
    except: return None

def strategy_6_cp437_bridge(s):
    """策略6: encode('cp437') → decode('gbk') (ZIP 解压典型路径)"""
    try:
        return s.encode('cp437', errors='replace').decode('gbk', errors='replace')
    except: return None

def strategy_7_shift_jis(s):
    """策略7: encode('utf-8') → decode('shift_jis') (排除日文编码)"""
    try:
        return s.encode('utf-8').decode('shift_jis', errors='replace')
    except: return None

# ====== 额外策略: 字节偏移测试 ======
def strategy_8_byte_shift(s):
    """策略8: UTF-8字节逐个偏移后当GBK解"""
    raw = s.encode('utf-8')
    results = []
    for offset in range(1, 4):
        try:
            shifted = raw[offset:]
            decoded = shifted.decode('gbk', errors='replace')
            if any('\u4e00' <= c <= '\u9fff' for c in decoded):
                results.append(f"offset={offset}: {decoded}")
        except: pass
    return '; '.join(results) if results else None

# ====== 策略9: 暴力全编码扫描 ======
ENCODINGS = ['gbk', 'gb2312', 'gb18030', 'big5', 'euc-kr', 'euc-jp',
             'shift_jis', 'iso-2022-jp', 'koi8-r', 'cp1252', 'cp1251']

def strategy_9_bruteforce(s):
    """策略9: 暴力测试所有 source→target 编码组合"""
    raw = s.encode('utf-8')
    best = []
    for src in ['utf-8', 'latin-1', 'cp437', 'mac_roman', 'cp1252']:
        try:
            raw_src = s.encode(src, errors='ignore')
        except: continue
        for tgt in ENCODINGS:
            try:
                decoded = raw_src.decode(tgt)
                # 评分: 含多少可读汉字
                cjk_count = sum(1 for c in decoded if '\u4e00' <= c <= '\u9fff')
                if cjk_count > len(decoded) * 0.3:
                    best.append((cjk_count, f"{src}→{tgt}: {decoded}"))
            except: pass
    best.sort(reverse=True)
    return best[0][1] if best else None

strategies = [
    ("1. utf8→gbk", strategy_1_utf8_to_gbk),
    ("2. utf8→gb18030", strategy_2_utf8_to_gb18030),
    ("3. latin1→gbk", strategy_3_latin1_bridge),
    ("4. raw_utf8→gbk", strategy_4_raw_utf8_bytes_as_gbk),
    ("5. double_utf8", strategy_5_double_utf8),
    ("6. cp437→gbk", strategy_6_cp437_bridge),
    ("7. utf8→shift_jis", strategy_7_shift_jis),
    ("8. byte_shift", strategy_8_byte_shift),
    ("9. bruteforce", strategy_9_bruteforce),
]

# ====== 执行测试 ======
print(f"\n{'='*70}", flush=True)
print("测试结果 (每个片段 × 9 种策略)", flush=True)
print(f"{'='*70}", flush=True)

for frag in test_fragments:
    print(f"\n🔍 原始片段: [{frag}]", flush=True)
    print(f"   UTF-8 hex: {frag.encode('utf-8').hex()}", flush=True)
    for name, func in strategies:
        result = func(frag)
        if result and result != frag:
            readable = sum(1 for c in result if '\u4e00' <= c <= '\u9fff')
            score = '★' * min(5, readable)
            print(f"   {name}: {result}  {score}", flush=True)
        else:
            print(f"   {name}: ✗ 无结果", flush=True)

# ====== 汇总: 哪种策略覆盖率最高？ ======
print(f"\n{'='*70}", flush=True)
print("策略覆盖率统计", flush=True)
print(f"{'='*70}", flush=True)

all_frags = list(garbled_fragments)
for name, func in strategies:
    successes = 0
    for frag in all_frags:
        result = func(frag)
        if result and result != frag:
            readable = sum(1 for c in result if '\u4e00' <= c <= '\u9fff')
            if readable > 0:
                successes += 1
    pct = successes / len(all_frags) * 100 if all_frags else 0
    print(f"  {name}: {successes}/{len(all_frags)} ({pct:.0f}%)", flush=True)

print(f"\n⏱️ 完成", flush=True)
