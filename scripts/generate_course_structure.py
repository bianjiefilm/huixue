#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成 Spark 编程课程代码目录结构

功能:
- 创建 12 个章节的标准化目录
- 生成 .ipynb Jupyter Notebook 模板
- 生成 .py Python 脚本模板
- 创建 README.md 说明文档

使用方法:
    python scripts/generate_course_structure.py
"""

import os
import json
from pathlib import Path


# 课程章节配置 (与 PDF 大纲对应)
CHAPTERS = [
    {"id": "01", "name": "Spark概述", "description": "Spark 基础概念、安装与 hello world"},
    {"id": "02", "name": "RDD编程", "description": "RDD 创建、转换与行动操作"},
    {"id": "03", "name": "SparkSQL", "description": "DataFrame、Spark SQL 查询"},
    {"id": "04", "name": "SparkStreaming", "description": "Spark Streaming 流计算入门"},
    {"id": "05", "name": "StructuredStreaming", "description": "Structured Streaming 高级流处理"},
    {"id": "06", "name": "SparkMLlib", "description": "机器学习库与实战"},
    {"id": "07", "name": "SparkGraphX", "description": "图计算入门"},
    {"id": "08", "name": "Spark调优", "description": "性能优化与调试技巧"},
    {"id": "09", "name": "PySpark核心原理", "description": "PySpark 架构与底层机制"},
    {"id": "10", "name": "数据读写", "description": "文件、数据库、HBase 数据读写"},
    {"id": "11", "name": "综合案例实战", "description": "完整项目实战演练"},
    {"id": "12", "name": "云端部署", "description": "集群环境部署与运维"},
]

BASE_DIR = Path(__file__).parent.parent / "ziyuan_data" / "notebooks"


def create_notebook_template(chapter_id: str, chapter_name: str, description: str) -> dict:
    """创建 Jupyter Notebook 模板"""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# {chapter_id} {chapter_name} - 实战练习\n",
                    "\n",
                    f"**章节说明**: {description}\n",
                    "\n",
                    "本章节将通过代码演示核心概念和操作方法。\n",
                    "\n",
                    "---",
                    "\n",
                    "## 实验目标\n",
                    "\n",
                    "1. 理解本章节的核心概念\n",
                    "2. 掌握关键 API 的使用方法\n",
                    "3. 完成课后练习题\n",
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 引入通用环境配置\n",
                    "import sys\n",
                    "sys.path.append('../../utils')\n",
                    "from spark_init import init_spark_env\n",
                    "\n",
                    "# 初始化 Spark 会话\n",
                    f"spark = init_spark_env('{chapter_id} {chapter_name}')\n",
                    "sc = spark.sparkContext\n",
                    "\n",
                    "print('✅ Spark 环境初始化成功!')\n",
                    "print(f'Spark 版本: {spark.version}')\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. 基础示例代码\n",
                    "\n",
                    "以下是本章节的核心代码示例:"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# TODO: 在此处添加本章节的核心代码\n",
                    "\n",
                    "# 示例: 创建测试数据\n",
                    "# data = [\"hello spark\", \"hello python\"]\n",
                    "# rdd = sc.parallelize(data)\n",
                    "\n",
                    "print('请在此处编写并运行你的代码...')\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. 练习题\n",
                    "\n",
                    "请完成以下练习:"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 练习: 尝试修改上述代码，实现以下功能:\n",
                    "# 1. 读取本地文件并统计词频\n",
                    "# 2. 使用 DataFrame 替代 RDD 实现相同功能\n",
                    "# 3. 对比两种方式的性能差异\n",
                    "\n",
                    "pass\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. 清理资源\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 停止 Spark 会话\n",
                    "spark.stop()\n",
                    "print('✅ Spark 会话已停止')\n"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (PySpark)",
                "language": "python",
                "name": "pyspark"
            },
            "language_info": {
                "name": "python",
                "version": "3.9+"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }


def create_python_template(chapter_id: str, chapter_name: str, description: str) -> str:
    """创建 Python 脚本模板"""
    return f'''# -*- coding: utf-8 -*-
"""
{chapter_id} {chapter_name} - 实战代码

章节说明: {description}
"""

import sys
import os

# 确保能导入 utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from spark_init import init_spark_env, get_sc


def main():
    """主函数"""
    print("=" * 50)
    print(f"实验: {chapter_id} {chapter_name}")
    print("=" * 50)

    # 初始化 Spark
    spark = init_spark_env("{chapter_name}")
    sc = spark.sparkContext

    try:
        # ============ 在此处添加实验代码 ============

        # 示例: 创建测试 RDD
        # data = ["hello spark", "hello python", "hello world"]
        # rdd = sc.parallelize(data)

        # 示例: 简单的词频统计
        # result = rdd.flatMap(lambda x: x.split(" ")) \\
        #             .map(lambda x: (x, 1)) \\
        #             .reduceByKey(lambda a, b: a + b) \\
        #             .collect()

        # ===========================================

        print("\\n✅ 实验完成!")

    except Exception as e:
        print(f"\\n❌ 错误: {{e}}")
        raise
    finally:
        spark.stop()
        print("\\n✅ Spark 会话已释放")


if __name__ == "__main__":
    main()
'''


def create_readme(chapter_id: str, chapter_name: str, description: str) -> str:
    """创建 README 文档"""
    return f'''# {chapter_id} {chapter_name}

> {description}

## 目录结构

```
{chapter_id}-{chapter_name}/
├── 01-基础演示.ipynb      # Jupyter Notebook 交互式教程
├── 02-核心代码.py         # Python 脚本版本
└── README.md             # 本说明文档
```

## 内容说明

本章节包含:

- **01-基础演示.ipynb**: 适合 Jupyter 环境交互式学习
- **02-核心代码.py**: 适合命令行运行和自动化测试

## 运行方式

### Jupyter Notebook

```bash
jupyter lab
# 打开 01-基础演示.ipynb
```

### Python 脚本

```bash
python 02-核心代码.py
```

## 学习目标

1. 理解 {chapter_name} 的核心概念
2. 掌握相关 API 的使用方法
3. 能够独立完成实验习题

## 参考资料

- 配套 PDF 文档: `../../课程资源/Spark编程基础/{chapter_id}*.pdf`
- Spark 官方文档: https://spark.apache.org/docs/latest/
- PySpark 文档: https://spark.apache.org/docs/latest/api/python/index.html
'''


def generate_course_structure():
    """生成课程结构"""
    print("🚀 开始生成 Spark 编程课程代码结构...")
    print(f"📁 目标目录: {BASE_DIR}")
    print("-" * 50)

    # 创建基础目录
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # 统计
    created_dirs = 0
    created_notebooks = 0
    created_python = 0
    created_readme = 0

    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        chapter_name = chapter["name"]
        description = chapter["description"]

        # 创建章节目录
        chapter_dir = BASE_DIR / f"{chapter_id}-{chapter_name}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        created_dirs += 1

        # 创建 01-基础演示.ipynb
        notebook_path = chapter_dir / "01-基础演示.ipynb"
        notebook_data = create_notebook_template(chapter_id, chapter_name, description)
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook_data, f, ensure_ascii=False, indent=2)
        created_notebooks += 1

        # 创建 02-核心代码.py
        python_path = chapter_dir / "02-核心代码.py"
        with open(python_path, 'w', encoding='utf-8') as f:
            f.write(create_python_template(chapter_id, chapter_name, description))
        created_python += 1

        # 创建 README.md
        readme_path = chapter_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(create_readme(chapter_id, chapter_name, description))
        created_readme += 1

        print(f"  ✅ {chapter_id}-{chapter_name}")

    # 创建主 README
    main_readme = BASE_DIR / "README.md"
    main_readme_content = f'''# Spark 编程实战代码库

>慧学 平台课程实训结构生成脚本 - Spark 编程基础课程配套代码

## 课程结构

本代码库包含 12 个章节的 PySpark 实战代码:

| 章节 | 名称 | 状态 |
|------|------|------|
| 01 | Spark概述 | ✅ |
| 02 | RDD编程 | ✅ |
| 03 | SparkSQL | ✅ |
| 04 | SparkStreaming | ✅ |
| 05 | StructuredStreaming | ✅ |
| 06 | SparkMLlib | ✅ |
| 07 | SparkGraphX | ✅ |
| 08 | Spark调优 | ✅ |
| 09 | PySpark核心原理 | ✅ |
| 10 | 数据读写 | ✅ |
| 11 | 综合案例实战 | ✅ |
| 12 | 云端部署 | ✅ |

## 环境配置

1. 安装依赖: `pip install -r ../requirements.txt`
2. 运行冒烟测试: `python ../utils/spark_init.py`
3. 开始学习: 选择章节并打开对应的 `.ipynb` 文件

## 快速开始

```bash
# 进入章节目录
cd 01-Spark概述

# Jupyter 方式
jupyter lab 01-基础演示.ipynb

# 脚本方式
python 02-核心代码.py
```

## 目录结构

```
notebooks/
├── 01-Spark概述/
├── 02-RDD编程/
├── 03-SparkSQL/
├── 04-SparkStreaming/
├── 05-StructuredStreaming/
├── 06-SparkMLlib/
├── 07-SparkGraphX/
├── 08-Spark调优/
├── 09-PySpark核心原理/
├── 10-数据读写/
├── 11-综合案例实战/
├── 12-云端部署/
└── README.md
```

## 配套资源

- PDF 文档: `../课程资源/Spark编程基础/`
- 环境配置: `../ENV_GUIDE.md`
- 工具模块: `../utils/spark_init.py`

## 联系

如有疑问，请联系课程教师或平台管理员。
'''
    with open(main_readme, 'w', encoding='utf-8') as f:
        f.write(main_readme_content)

    print("-" * 50)
    print("📊 生成统计:")
    print(f"   - 章节目录: {created_dirs} 个")
    print(f"   - Jupyter Notebook: {created_notebooks} 个")
    print(f"   - Python 脚本: {created_python} 个")
    print(f"   - README 文档: {created_readme + 1} 个")
    print("-" * 50)
    print("✅ 课程代码结构生成完成!")
    print(f"📁 目录: {BASE_DIR}")


if __name__ == "__main__":
    generate_course_structure()
