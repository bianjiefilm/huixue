#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repair stage_11_object_tracking.json format issues
Extracts questions using regex patterns to handle unescaped content
"""
import re
import json
from pathlib import Path


def extract_questions_manually(content):
    """Extract questions by parsing object by object"""
    questions = []

    # Find all question objects using regex
    # Each question starts with "id": "q11-X" and ends with },
    question_pattern = r'"id":\s*"q11-(\d+)"[^}]+}(?=\s*[,}]|\s*"id":)'

    # More robust: find each { ... } block that contains "id": "q11-X"
    pos = 0
    while True:
        # Find next question object start
        start = content.find('"id": "q11-', pos)
        if start == -1:
            break

        # Find the opening brace for this object
        brace_start = start
        while brace_start > 0 and content[brace_start] != '{':
            brace_start -= 1

        # Find matching closing brace
        count = 0
        i = brace_start
        while i < len(content):
            if content[i] == '{':
                count += 1
            elif content[i] == '}':
                count -= 1
                if count == 0:
                    break
            i += 1

        end = i + 1
        question_text = content[brace_start:end]

        # Extract fields from this question object
        question_obj = parse_question_object(question_text)
        if question_obj:
            questions.append(question_obj)

        pos = end

    return questions


def parse_question_object(text):
    """Parse a single question object"""
    result = {}

    # Extract id
    id_match = re.search(r'"id":\s*"([^"]*)"', text)
    if id_match:
        result['id'] = id_match.group(1)

    # Extract difficulty
    diff_match = re.search(r'"difficulty":\s*"([^"]*)"', text)
    if diff_match:
        result['difficulty'] = diff_match.group(1)

    # Extract type
    type_match = re.search(r'"type":\s*"([^"]*)"', text)
    if type_match:
        result['type'] = type_match.group(1)

    # Extract question
    q_match = re.search(r'"question":\s*"([^"]*)"', text)
    if q_match:
        result['question'] = q_match.group(1)

    # Extract hint
    hint_match = re.search(r'"hint":\s*"([^"]*)"', text)
    if hint_match:
        result['hint'] = hint_match.group(1)

    # Extract options
    opts_match = re.search(r'"options":\s*(null|\[[^\]]*\])', text)
    if opts_match:
        if opts_match.group(1) == 'null':
            result['options'] = None
        else:
            result['options'] = json.loads(opts_match.group(1))

    # Extract answer - this is complex, may span multiple lines and contain special chars
    answer_match = re.search(r'"answer":\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
    if answer_match:
        result['answer'] = answer_match.group(1)
    else:
        # Try to find answer that ends with ",
        # Look for "answer": " then capture everything until a closing pattern
        answer_start = text.find('"answer": "')
        if answer_start != -1:
            content_start = answer_start + len('"answer": "')
            # Find the end - look for "\n    },"
            end_pattern = text.find('"\n    },', content_start)
            if end_pattern != -1:
                result['answer'] = text[content_start:end_pattern]

    return result


def repair_stage11():
    input_file = Path(__file__).parent.parent.parent / "output" / "stage_11_object_tracking.json"
    output_file = Path(__file__).parent.parent.parent / "output" / "stage_11_object_tracking_fixed.json"

    print(f"Reading file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"File length: {len(content)} characters")

    result = {}

    # Extract stage_id
    stage_id_match = re.search(r'"stage_id":\s*(\d+)', content)
    result['stage_id'] = int(stage_id_match.group(1)) if stage_id_match else 11

    # Extract stage_name
    stage_name_match = re.search(r'"stage_name":\s*"([^"]*)"', content)
    result['stage_name'] = stage_name_match.group(1) if stage_name_match else "object-tracking"

    print(f"\nStage: {result['stage_id']} - {result['stage_name']}")

    # Extract handbook
    handbook_match = re.search(r'"handbook":\s*"((?:[^"\\]|\\.)*)"', content, re.DOTALL)
    if handbook_match:
        result['handbook'] = handbook_match.group(1)
    else:
        result['handbook'] = ""

    print(f"handbook: {len(result['handbook'])} chars")

    # Extract questions
    result['questions'] = extract_questions_manually(content)
    print(f"questions: {len(result['questions'])} items")

    # Extract answer
    answer_match = re.search(r'"answer":\s*"((?:[^"\\]|\\.)*)"', content, re.DOTALL)
    if answer_match:
        result['answer'] = answer_match.group(1)
    else:
        result['answer'] = ""

    print(f"answer: {len(result['answer'])} chars")

    # Extract test_cases
    test_cases_pattern = r'"test_cases":\s*\[([\s\S]*?)\]\s*,\s*"baseline_code"'
    test_match = re.search(test_cases_pattern, content)
    if test_match:
        try:
            result['test_cases'] = json.loads('[' + test_match.group(1) + ']')
        except:
            result['test_cases'] = []
    else:
        result['test_cases'] = []

    print(f"test_cases: {len(result['test_cases'])} items")

    # Extract baseline_code
    baseline_pattern = r'"baseline_code":\s*"""\s*([\s\S]*?)"""'
    baseline_match = re.search(baseline_pattern, content)
    if baseline_match:
        result['baseline_code'] = baseline_match.group(1)
    else:
        result['baseline_code'] = ""

    print(f"baseline_code: {len(result['baseline_code'])} chars")

    # Extract summary
    summary_pattern = r'"summary":\s*"((?:[^"\\]|\\.)*)"'
    summary_match = re.search(summary_pattern, content)
    if summary_match:
        result['summary'] = summary_match.group(1)
    else:
        result['summary'] = ""

    print(f"summary: {len(result['summary'])} chars")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nWrote fixed file: {output_file}")

    # Verify JSON
    print("\nVerifying JSON format...")
    with open(output_file, 'r', encoding='utf-8') as f:
        try:
            verified = json.load(f)
            print(f"OK - JSON is valid!")
            print(f"  stage_id: {verified['stage_id']}")
            print(f"  stage_name: {verified['stage_name']}")
            print(f"  handbook: {len(verified.get('handbook', ''))} chars")
            print(f"  questions: {len(verified.get('questions', []))} items")
            print(f"  answer: {len(verified.get('answer', ''))} chars")
            print(f"  test_cases: {len(verified.get('test_cases', []))} items")
            print(f"  baseline_code: {len(verified.get('baseline_code', ''))} chars")
            print(f"  summary: {len(verified.get('summary', ''))} chars")
        except json.JSONDecodeError as e:
            print(f"FAIL - JSON validation failed: {e}")
            return False

    return True


if __name__ == "__main__":
    import sys
    success = repair_stage11()
    sys.exit(0 if success else 1)
