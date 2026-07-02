#!/usr/bin/env python3
"""
Generate mv commands for PUA-bearing filenames.
Writes to /tmp/rename_pua.sh — no stdout interaction with PUA chars.
"""
import os, sys

BASE = "/Users/jimfu/Work/huixue/ziyuan_normalized/B_Legacy_Materials/courses"
OUT = "/tmp/rename_pua.sh"

# Build exact chapter markers using chr()
E0FF = chr(0xE0FF)
E100 = chr(0xE100)
E11F = chr(0xE11F)
E50D = chr(0xE50D)
E190 = chr(0xE190)

REPLACEMENTS = [
    # Chapter markers (longest first)
    (f"\u7ed7{E0FF}\u7af4\u7ed4\u72c5\u7d30", "\u7b2c\u4e00\u7ae0\uff1a"),
    (f"\u7ed7{E0FF}\u7c29\u7ed4\u72c5\u7d30", "\u7b2c\u4e8c\u7ae0\uff1a"),
    (f"\u7ed7{E0FF}\u7b01\u7ed4\u72c5\u7d30", "\u7b2c\u4e09\u7ae0\uff1a"),
    (f"\u7ed7{E100}\u6d13\u7ed4\u72c5\u7d30", "\u7b2c\u56db\u7ae0\uff1a"),
    (f"\u7ed7{E0FF}\u7c32\u7ed4\u72c5\u7d30", "\u7b2c\u4e94\u7ae0\uff1a"),
    (f"\u7ed7{E100}\u53da\u7ed4\u72c5\u7d30", "\u7b2c\u516d\u7ae0\uff1a"),
    (f"\u7ed7{E0FF}\u7af7\u7ed4\u72c5\u7d30", "\u7b2c\u4e03\u7ae0\uff1a"),
    (f"\u7ed7{E100}\u53d3\u7ed4\u72c5\u7d30", "\u7b2c\u516b\u7ae0\uff1a"),
    (f"\u7ed7{E0FF}\u7bc0\u7ed4\u72c5\u7d30", "\u7b2c\u4e5d\u7ae0\uff1a"),
    (f"\u7ed7{E100}\u5d04\u7ed4\u72c5\u7d30", "\u7b2c\u5341\u7ae0\uff1a"),
    # Stray PUA removal
    (E0FF, ""), (E100, ""), (E11F, ""), (E50D, ""), (E190, ""),
]

def shell_escape(s):
    """Escape for shell single quotes"""
    return s.replace("'", "'\\''")

renames = []
for root, dirs, files in os.walk(BASE, topdown=False):
    for name in list(files) + list(dirs):
        new_name = name
        for old_frag, new_frag in REPLACEMENTS:
            new_name = new_name.replace(old_frag, new_frag)
        if new_name != name:
            old_path = os.path.join(root, name)
            new_path = os.path.join(root, new_name)
            if os.path.exists(old_path) and not os.path.exists(new_path):
                renames.append((old_path, new_path))

with open(OUT, "w") as f:
    f.write("#!/bin/bash\n")
    f.write(f"# Auto-generated: {len(renames)} renames\n")
    f.write("OK=0; FAIL=0\n")
    for old_p, new_p in renames:
        f.write(f"mv '{shell_escape(old_p)}' '{shell_escape(new_p)}' 2>/dev/null && ((OK++)) || ((FAIL++))\n")
    f.write('echo "Done: $OK ok, $FAIL fail"\n')

sys.stdout.write(f"Generated {len(renames)} mv commands to {OUT}\n")
sys.stdout.flush()
