import re

with open('.gemini/antigravity/brain/scratch/test_plan.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
current_module = []
has_frontend = False

for line in lines:
    if line.startswith('模块'):
        if current_module and has_frontend:
            output.extend(current_module)
            output.append('-'*40 + '\n')
        current_module = [line]
        has_frontend = False
    elif current_module is not None:
        current_module.append(line)
        if '前端' in line or 'UI' in line or '前端预览' in line or '前端 (Frontend)' in line:
            has_frontend = True

if current_module and has_frontend:
    output.extend(current_module)

with open('.gemini/antigravity/brain/scratch/frontend_tests.txt', 'w', encoding='utf-8') as f:
    f.writelines(output)
print(f"Extracted {len(output)} lines to frontend_tests.txt")
