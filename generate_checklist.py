import re

with open('.gemini/antigravity/brain/scratch/test_plan.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Regular expression to find modules and their acceptance criteria
modules = re.finditer(r'(模块[一二三四五六七八九十百]+[：:](.+?))\s*覆盖章节.*?(?:3\.\s*验证标准\s*\(Acceptance Criteria\))(.*?)(?=模块[一二三四五六七八九十百]+[：:]|$)', text, re.DOTALL)

checklist = ["# 视觉验证清单\n\n## 本次改动：全量前端验收测试\n"]

for m in modules:
    module_name = m.group(1).strip()
    criteria = m.group(3).strip()
    
    # Check if there's any mention of UI/frontend/interaction
    # We will just extract all criteria as they are testing standards
    checklist.append(f"\n### {module_name}")
    
    # Split criteria by lines and format as checklist
    lines = criteria.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        # Ignore numbering lines or pure headers if they don't contain much info
        if len(line) < 3 and not line.endswith('：'):
            continue
            
        if line.endswith('：'):
            # Group header
            checklist.append(f"\n**{line}**")
        else:
            # Checkable item
            checklist.append(f"- [ ] {line}")

with open('.verify-checklist.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(checklist))

print("Created .verify-checklist.md")
