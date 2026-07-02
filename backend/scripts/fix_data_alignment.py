#!/usr/bin/env python3
"""
数据正确性修复脚本 — P0 批量修复
覆盖任务: #3(已在代码中修复), #4, #5, #6, #10

运行方式:
  cd backend && python3 scripts/fix_data_alignment.py
"""
import sys
import os
import json
from pathlib import Path

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import models
from app.core.enums import TrainingTypeEnum, DifficultyLevelEnum, TrainingPublishStatusEnum, TrainingVisibilityEnum

# The real resource base: backend/static/resources or ziyuan_data (project root)
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
# Prefer backend/static/resources, then ziyuan_data at project root
_backend_static = BACKEND_DIR / "static" / "resources"
_ziyuan_data = PROJECT_ROOT / "ziyuan_data"
RESOURCE_BASE = _backend_static if _backend_static.exists() else _ziyuan_data

def get_db():
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise


def fix_dataset_names_and_paths(db):
    """#4 + #5: 修正 dataset name 映射 + 填充 relative_path"""
    print("\n=== #4/#5: 修正 Dataset name + relative_path ===")

    # Build mapping: training_id -> (title, project_path, actual CSV files)
    trainings = db.query(models.Training).all()
    training_map = {}
    for t in trainings:
        project_dir = None
        if t.project_path:
            project_dir = RESOURCE_BASE / t.project_path
            if not project_dir.exists():
                # Try prepending 实训资源/
                project_dir = RESOURCE_BASE / "实训资源" / t.project_path

        csvs = []
        sqls = []
        if project_dir and project_dir.exists():
            ds_dir = project_dir / "datasets"
            if ds_dir.exists():
                csvs = sorted(ds_dir.glob("*.csv"))
                sqls = sorted(ds_dir.glob("*.sql"))

        training_map[t.id] = {
            "title": t.title,
            "project_path": t.project_path,
            "project_dir": project_dir,
            "csvs": csvs,
            "sqls": sqls,
        }

    datasets = db.query(models.TrainingDataset).order_by(
        models.TrainingDataset.training_id, models.TrainingDataset.id
    ).all()

    fixed = 0
    for ds in datasets:
        info = training_map.get(ds.training_id)
        if not info:
            print(f"  ⚠️  DS#{ds.id} T#{ds.training_id} — 无对应 Training 记录")
            continue

        # Fix name: should reference the parent training title
        old_name = ds.name
        # Extract dataset number from existing name (e.g., "数据集 1 - ...")
        idx = old_name.split(" - ")[0] if " - " in old_name else old_name
        new_name = f"{idx} - {info['title']}"

        # Fix relative_path: point to actual CSV file
        all_files = info["csvs"] + info["sqls"]
        ds_index = 0
        # Find this dataset's index among all datasets for this training
        sibling_datasets = [d for d in datasets if d.training_id == ds.training_id]
        for i, sib in enumerate(sibling_datasets):
            if sib.id == ds.id:
                ds_index = i
                break

        new_relative_path = None
        if ds_index < len(all_files):
            # Make path relative to RESOURCE_BASE
            new_relative_path = str(all_files[ds_index].relative_to(RESOURCE_BASE))

        # Determine file_type from extension
        new_file_type = ds.file_type
        if new_relative_path:
            ext = Path(new_relative_path).suffix.lower().lstrip(".")
            new_file_type = ext if ext else ds.file_type

        changes = []
        if ds.name != new_name:
            ds.name = new_name
            changes.append(f"name: {old_name!r} → {new_name!r}")
        if ds.relative_path != new_relative_path:
            ds.relative_path = new_relative_path
            changes.append(f"relative_path: {ds.relative_path}")
        if ds.file_type != new_file_type:
            ds.file_type = new_file_type
            changes.append(f"file_type: {new_file_type}")

        if changes:
            fixed += 1
            print(f"  ✓ DS#{ds.id} T#{ds.training_id}: {', '.join(changes)}")

    db.commit()
    print(f"  → 修复了 {fixed} 条 dataset 记录")


def add_missing_trainings(db):
    """#6: 补建缺失 Training 记录"""
    print("\n=== #6: 补建缺失 Training 记录 ===")

    # Disk directories that should have Training records
    disk_trainings = {
        "07-某高校校情管理分析案例": {
            "title": "某高校校情管理分析案例",
            "type": TrainingTypeEnum.DATA_ANALYSIS,
            "intro": "基于高校数据进行校情管理与统计分析",
        },
        "09-某公司人力薪酬分析": {
            "title": "某公司人力薪酬分析",
            "type": TrainingTypeEnum.DATA_ANALYSIS,
            "intro": "人力资源薪酬数据分析与可视化",
        },
        "10-某公司财务报表分析案例": {
            "title": "某公司财务报表分析案例",
            "type": TrainingTypeEnum.DATA_ANALYSIS,
            "intro": "财务报表数据分析与财务健康评估",
        },
        "11-风电齿轮箱预警分析": {
            "title": "风电齿轮箱预警分析",
            "type": TrainingTypeEnum.DATA_ANALYSIS,
            "intro": "风电设备齿轮箱故障预警分析",
        },
        "12-分布式光伏出力预测": {
            "title": "分布式光伏出力预测",
            "type": TrainingTypeEnum.DATA_ANALYSIS,
            "intro": "光伏发电出力预测与分析",
        },
        "05-某电商货品销售分析案例": {
            "title": "某电商货品销售分析案例",
            "type": TrainingTypeEnum.DATA_ANALYSIS,
            "intro": "电商平台商品销售数据分析",
        },
    }

    existing_paths = {t.project_path for t in db.query(models.Training).all()}

    created = 0
    for dir_name, info in disk_trainings.items():
        project_path = f"实训资源/{dir_name}"
        if project_path in existing_paths:
            print(f"  ⏭ {info['title']} — 已存在")
            continue

        resource_dir = RESOURCE_BASE / project_path
        if not resource_dir.exists():
            print(f"  ⚠️ {dir_name} — 磁盘目录不存在")
            continue

        # Read metadata.json if available
        meta_path = resource_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
                info["title"] = meta.get("title", info["title"])
                info["intro"] = meta.get("intro", info.get("intro", ""))

        training = models.Training(
            title=info["title"],
            training_type=info["type"],
            intro=info["intro"],
            difficulty=DifficultyLevelEnum.beginner,
            project_path=project_path,
            publish_status=TrainingPublishStatusEnum.PUBLISHED,
            visibility=TrainingVisibilityEnum.PUBLIC,
            is_published=True,
            creator_id=1,
            course_hours=2,
        )
        db.add(training)
        db.flush()  # Get the ID

        # Create dataset records for CSV/SQL files
        ds_dir = resource_dir / "datasets"
        if ds_dir.exists():
            idx = 0
            for f in sorted(ds_dir.iterdir()):
                if f.suffix.lower() in (".csv", ".sql", ".xlsx"):
                    idx += 1
                    ds = models.TrainingDataset(
                        training_id=training.id,
                        name=f"数据集 {idx} - {info['title']}",
                        file_url=f"/static/datasets/{training.id}_data_{idx}{f.suffix}",
                        relative_path=str(f.relative_to(RESOURCE_BASE)),
                        file_type=f.suffix.lower().lstrip("."),
                        uploader_id=1,
                    )
                    db.add(ds)

        created += 1
        print(f"  ✓ 创建 T#{training.id} — {info['title']} (path={project_path})")

    # Fix orphaned datasets (T#109, T#110) — re-point to new trainings
    orphan_map = {
        109: "11-风电齿轮箱预警分析",
        110: "12-分布式光伏出力预测",
    }
    for old_tid, dir_name in orphan_map.items():
        project_path = f"实训资源/{dir_name}"
        new_training = db.query(models.Training).filter(
            models.Training.project_path == project_path
        ).first()
        if new_training:
            orphans = db.query(models.TrainingDataset).filter(
                models.TrainingDataset.training_id == old_tid
            ).all()
            if orphans:
                # Delete orphans — new datasets were already created above
                for o in orphans:
                    db.delete(o)
                print(f"  🗑 删除 {len(orphans)} 条孤立数据集 (原 T#{old_tid})")

    db.commit()
    print(f"  → 创建了 {created} 条 Training 记录")


def fill_training_environments(db):
    """#10: 填充 training_environments 默认配置"""
    print("\n=== #10: 填充 training_environments 默认配置 ===")

    existing = db.query(models.TrainingEnvironment).count()
    if existing > 0:
        print(f"  ⏭ 已有 {existing} 条记录, 跳过")
        return

    envs = [
        models.TrainingEnvironment(
            name="Jupyter Notebook",
            environment_type="JUPYTER",
            docker_image="huixue/jupyter-lab:latest",
            description="Python Jupyter Notebook 编程环境",
            default_memory="2Gi",
            default_cpu="1",
            is_active=True,
        ),
        models.TrainingEnvironment(
            name="慧学 BI",
            environment_type="HUIXUE_BI",
            docker_image="huixue/superset:latest",
            description="BI 数据可视化分析环境 (Apache Superset)",
            default_memory="4Gi",
            default_cpu="2",
            is_active=True,
        ),
        models.TrainingEnvironment(
            name="AI Pipeline",
            environment_type="AI_PIPELINE",
            docker_image="huixue/ai-pipeline:latest",
            description="AI 模型训练与推理流水线环境",
            default_memory="4Gi",
            default_cpu="2",
            is_active=True,
        ),
    ]

    for env in envs:
        db.add(env)
        print(f"  ✓ 创建环境: {env.name} ({env.environment_type})")

    db.commit()
    print(f"  → 创建了 {len(envs)} 条环境配置")


def verify_results(db):
    """验证修复结果"""
    print("\n=== 验证结果 ===")

    trainings = db.query(models.Training).all()
    print(f"Trainings: {len(trainings)}")

    datasets = db.query(models.TrainingDataset).all()
    with_path = sum(1 for d in datasets if d.relative_path)
    print(f"Datasets: {len(datasets)} (有 relative_path: {with_path})")

    # Check file existence
    found = 0
    missing = 0
    for ds in datasets:
        if ds.relative_path:
            full = RESOURCE_BASE / ds.relative_path
            if full.exists():
                found += 1
            else:
                missing += 1
                print(f"  ✗ 文件不存在: {ds.relative_path}")
    print(f"文件验证: {found} 存在, {missing} 缺失")

    envs = db.query(models.TrainingEnvironment).count()
    print(f"Environments: {envs}")

    # Check orphans
    orphans = db.query(models.TrainingDataset).filter(
        ~models.TrainingDataset.training_id.in_(
            db.query(models.Training.id)
        )
    ).count()
    print(f"孤立 Datasets: {orphans}")


def main():
    print(f"RESOURCE_BASE: {RESOURCE_BASE}")
    print(f"exists: {RESOURCE_BASE.exists()}")

    db = get_db()
    try:
        fix_dataset_names_and_paths(db)
        add_missing_trainings(db)
        fill_training_environments(db)
        verify_results(db)
        print("\n✅ 所有 P0/P1 修复完成")
    except Exception as e:
        db.rollback()
        print(f"\n❌ 修复失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
