#!/usr/bin/env python3
"""
课程环境自检脚本 - 配合 tempo-course-auditor Skill 使用
用法: python check_course_env.py <course_type> [data_dir]

课程类型:
  - data_collection: 数据采集与预处理
  - data_cleaning: 数据清洗
  - machine_learning: 机器学习/数据挖掘
  - deep_learning: 深度学习/神经网络
  - spark: Spark编程
  - visualization: 数据可视化
  - python_basic: Python基础
  - computer_vision: 计算机视觉
"""

import importlib
import sys
import os
import json
from pathlib import Path

# 各课程类型所需的依赖包
COURSE_PACKAGES = {
    'data_collection': {
        'required': ['requests', 'beautifulsoup4', 'lxml'],
        'optional': ['scrapy', 'selenium', 'pymysql', 'pymongo'],
        'description': '数据采集与预处理'
    },
    'data_cleaning': {
        'required': ['pandas', 'numpy'],
        'optional': ['openpyxl', 'xlrd', 'chardet', 'regex'],
        'description': '数据清洗'
    },
    'machine_learning': {
        'required': ['pandas', 'numpy', 'sklearn'],
        'optional': ['xgboost', 'lightgbm', 'scipy', 'statsmodels'],
        'description': '机器学习/数据挖掘'
    },
    'deep_learning': {
        'required': ['numpy', 'tensorflow'],
        'optional': ['keras', 'torch', 'torchvision'],
        'description': '深度学习/神经网络'
    },
    'spark': {
        'required': ['pyspark'],
        'optional': ['findspark', 'py4j'],
        'description': 'Spark编程'
    },
    'visualization': {
        'required': ['matplotlib', 'pandas'],
        'optional': ['seaborn', 'plotly', 'pyecharts', 'bokeh'],
        'description': '数据可视化'
    },
    'python_basic': {
        'required': [],
        'optional': ['ipython', 'jupyter'],
        'description': 'Python基础'
    },
    'computer_vision': {
        'required': ['numpy', 'opencv-python'],
        'optional': ['pillow', 'torch', 'torchvision', 'tensorflow'],
        'description': '计算机视觉'
    }
}

# 包名到import名的映射
IMPORT_NAME_MAP = {
    'beautifulsoup4': 'bs4',
    'opencv-python': 'cv2',
    'pillow': 'PIL',
    'scikit-learn': 'sklearn',
}


def get_import_name(package_name):
    """获取包的import名称"""
    return IMPORT_NAME_MAP.get(package_name, package_name.replace('-', '_'))


def check_package(package_name):
    """检查单个包是否安装"""
    import_name = get_import_name(package_name)
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, None


def check_packages(course_type):
    """检查课程所需的所有包"""
    if course_type not in COURSE_PACKAGES:
        return {'error': f"未知的课程类型: {course_type}"}

    config = COURSE_PACKAGES[course_type]
    results = {
        'course_type': course_type,
        'description': config['description'],
        'required': [],
        'optional': [],
        'summary': {'required_ok': 0, 'required_fail': 0, 'optional_ok': 0, 'optional_fail': 0}
    }

    # 检查必需包
    for pkg in config['required']:
        installed, version = check_package(pkg)
        status = {
            'package': pkg,
            'installed': installed,
            'version': version
        }
        results['required'].append(status)
        if installed:
            results['summary']['required_ok'] += 1
        else:
            results['summary']['required_fail'] += 1

    # 检查可选包
    for pkg in config['optional']:
        installed, version = check_package(pkg)
        status = {
            'package': pkg,
            'installed': installed,
            'version': version
        }
        results['optional'].append(status)
        if installed:
            results['summary']['optional_ok'] += 1
        else:
            results['summary']['optional_fail'] += 1

    return results


def check_data_files(data_dir='./data'):
    """检查数据文件目录"""
    results = {
        'data_dir': data_dir,
        'exists': False,
        'files': [],
        'total_size': 0,
        'warnings': []
    }

    data_path = Path(data_dir)
    if not data_path.exists():
        results['warnings'].append(f"数据目录不存在: {data_dir}")
        return results

    results['exists'] = True

    # 支持的数据文件扩展名
    data_extensions = {'.csv', '.xlsx', '.xls', '.json', '.txt', '.parquet', '.h5', '.pkl'}

    for file_path in data_path.rglob('*'):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            size = file_path.stat().st_size

            file_info = {
                'name': str(file_path.relative_to(data_path)),
                'size': size,
                'size_human': format_size(size),
                'is_data_file': ext in data_extensions
            }
            results['files'].append(file_info)
            results['total_size'] += size

            # 检查空文件
            if size == 0:
                results['warnings'].append(f"空文件: {file_info['name']}")

    if not results['files']:
        results['warnings'].append("数据目录为空")

    results['total_size_human'] = format_size(results['total_size'])
    return results


def check_notebook_structure(notebook_dir='.'):
    """检查Jupyter Notebook结构"""
    results = {
        'notebooks': [],
        'has_solution': False,
        'warnings': []
    }

    nb_path = Path(notebook_dir)

    for nb_file in nb_path.rglob('*.ipynb'):
        nb_info = {
            'name': str(nb_file.relative_to(nb_path)),
            'size': nb_file.stat().st_size,
            'is_solution': any(kw in nb_file.name.lower() for kw in ['solution', 'answer', 'complete', '答案', '参考'])
        }
        results['notebooks'].append(nb_info)

        if nb_info['is_solution']:
            results['has_solution'] = True

    if not results['notebooks']:
        results['warnings'].append("未找到Jupyter Notebook文件")
    elif not results['has_solution']:
        results['warnings'].append("未找到参考答案/解决方案Notebook")

    return results


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def print_report(results, data_results=None, notebook_results=None):
    """打印检查报告"""
    print("=" * 60)
    print(f"课程环境检查报告")
    print(f"课程类型: {results.get('description', results.get('course_type', 'unknown'))}")
    print("=" * 60)

    # 依赖包检查
    print("\n[必需依赖包]")
    for pkg in results.get('required', []):
        status = "[OK]" if pkg['installed'] else "[ERROR]"
        version = f"(v{pkg['version']})" if pkg['version'] else ""
        print(f"  {status} {pkg['package']} {version}")

    print("\n[可选依赖包]")
    for pkg in results.get('optional', []):
        status = "[OK]" if pkg['installed'] else "[WARN]"
        version = f"(v{pkg['version']})" if pkg['version'] else ""
        print(f"  {status} {pkg['package']} {version}")

    # 汇总
    summary = results.get('summary', {})
    print(f"\n[依赖汇总]")
    print(f"  必需包: {summary.get('required_ok', 0)}/{summary.get('required_ok', 0) + summary.get('required_fail', 0)} 已安装")
    print(f"  可选包: {summary.get('optional_ok', 0)}/{summary.get('optional_ok', 0) + summary.get('optional_fail', 0)} 已安装")

    # 数据文件检查
    if data_results:
        print("\n[数据文件检查]")
        if data_results['exists']:
            print(f"  目录: {data_results['data_dir']}")
            print(f"  文件数: {len(data_results['files'])}")
            print(f"  总大小: {data_results['total_size_human']}")

            data_files = [f for f in data_results['files'] if f['is_data_file']]
            if data_files:
                print(f"  数据文件:")
                for f in data_files[:10]:  # 最多显示10个
                    print(f"    - {f['name']} ({f['size_human']})")
                if len(data_files) > 10:
                    print(f"    ... 还有 {len(data_files) - 10} 个文件")

        for warn in data_results.get('warnings', []):
            print(f"  [WARN] {warn}")

    # Notebook检查
    if notebook_results:
        print("\n[Notebook检查]")
        print(f"  Notebook数量: {len(notebook_results['notebooks'])}")
        print(f"  包含参考答案: {'是' if notebook_results['has_solution'] else '否'}")

        for warn in notebook_results.get('warnings', []):
            print(f"  [WARN] {warn}")

    # 总体判断
    print("\n" + "=" * 60)
    if summary.get('required_fail', 0) > 0:
        print("[FAIL] 存在未安装的必需依赖包，请先安装后再使用课程")
    elif data_results and data_results.get('warnings'):
        print("[WARN] 数据文件存在问题，请检查")
    else:
        print("[PASS] 环境检查通过")
    print("=" * 60)


def main():
    # 解析参数
    course_type = sys.argv[1] if len(sys.argv) > 1 else 'data_cleaning'
    data_dir = sys.argv[2] if len(sys.argv) > 2 else './data'

    # 显示帮助
    if course_type in ['-h', '--help', 'help']:
        print(__doc__)
        print("\n可用的课程类型:")
        for ct, config in COURSE_PACKAGES.items():
            print(f"  {ct}: {config['description']}")
        return

    # 执行检查
    pkg_results = check_packages(course_type)
    data_results = check_data_files(data_dir)
    notebook_results = check_notebook_structure('.')

    # 输出报告
    if '--json' in sys.argv:
        # JSON格式输出
        output = {
            'packages': pkg_results,
            'data': data_results,
            'notebooks': notebook_results
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 文本格式输出
        print_report(pkg_results, data_results, notebook_results)


if __name__ == '__main__':
    main()
