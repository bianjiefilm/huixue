#!/usr/bin/env python3
"""根据配置为课程资源生成模块分组报告"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Course, CourseResource

CONFIG_PATH = BASE_DIR / "resource_module_rules.json"
DATABASE_URL = "sqlite:///./huixue_local.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def load_module_rules() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(text: str) -> str:
    if not text:
        return ""
    return text.lower()


def match_module(resource: CourseResource, rules) -> Dict[str, Any]:
    normalized_url = normalize(resource.url)
    normalized_title = normalize(resource.title)
    resource_type = normalize(resource.resource_type or "")

    for module in rules:
        for keyword in module.get("path_keywords", []):
            if keyword and keyword in normalized_url:
                return module
        for keyword in module.get("title_keywords", []):
            if keyword and keyword in normalized_title:
                return module
        if module.get("resource_types") and resource_type in module["resource_types"]:
            return module

    return None


def build_mapping(course_title: str):
    session = SessionLocal()
    try:
        course = session.query(Course).filter(Course.title == course_title).first()
        if not course:
            print(f"课程未找到: {course_title}")
            return

        rules_config = load_module_rules()
        rules = rules_config.get("modules", [])
        if not rules:
            print("模块规则为空，退出")
            return

        print(f"课程: {course.title} (ID: {course.id})")
        resources = session.query(CourseResource).filter(CourseResource.course_id == course.id).all()

        mapping = {}
        unmatched = []

        for resource in resources:
            module = match_module(resource, rules)
            if module:
                key = module["module_key"]
                mapping.setdefault(key, {"module": module, "resources": []})
                mapping[key]["resources"].append(resource)
            else:
                unmatched.append(resource)

        print(f"总资源数: {len(resources)}")
        for key, data in mapping.items():
            print(f"模块 {data['module']['chapter_title']} ({key}) -> {len(data['resources'])} 条")
        print(f"未匹配资源: {len(unmatched)}")
        if unmatched:
            print("未匹配资源示例:")
            for res in unmatched[:10]:
                print("-", res.title)

    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="生成课程资源模块映射报告")
    parser.add_argument("course", help="课程标题，例如 Spark编程基础")
    args = parser.parse_args()

    build_mapping(args.course)
