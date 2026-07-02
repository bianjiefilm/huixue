import os
import re
import json
import csv
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Union
from sqlalchemy.orm import Session
from app.models.models import Training, TrainingDataset
from app.core.config import settings
from app.utils.bi_helpers import (
    sanitize_mysql_to_sqlite as _sanitize_mysql_to_sqlite,
    classify_sql_files as _classify_sql_files,
    classify_dataset_sql_files as _classify_dataset_sql_files,
    convert_csv_value as _convert_csv_value,
    clean_csv_row as _clean_csv_row,
)

logger = logging.getLogger(__name__)


def _read_text_safe(path: Path) -> str:
    """读取文本文件，自动尝试多种编码"""
    for enc in ('utf-8-sig', 'gbk', 'latin-1'):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return path.read_text(encoding='latin-1')


def _open_text_safe(path, newline=None):
    """打开文本文件，自动尝试多种编码"""
    for enc in ('utf-8-sig', 'gbk', 'latin-1'):
        try:
            f = open(path, 'r', encoding=enc, newline=newline)
            f.read(1024)
            f.seek(0)
            return f
        except (UnicodeDecodeError, UnicodeError):
            continue
    return open(path, 'r', encoding='latin-1', newline=newline)

class BIDataLoader:
    """
    Utility class to load data from SQL files in ziyuan_data for BI training.
    Replaces the Docker/Superset approach with client-side Graphic Walker.
    """
    
    ZIYUAN_ROOT_CANDIDATES = [
        # Docker Swarm 挂载路径 (服务器实际数据路径)
        Path("/data/ziyuan_data_full"),
        Path("/data/huixue_storage/static/ziyuan_data_full"),
        # 学校生产容器中的静态资源挂载路径，包含 /实训资源/...
        Path("/app/static/resources"),
        # 生产环境：主机挂载的 ziyuan_data 目录（含实训资源/课程资源 symlink）
        Path("/data/huixue_storage/ziyuan_data"),
        # 优先检查上级目录的 ziyuan_data（项目根目录）
        Path("../ziyuan_data"),
        Path("../../ziyuan_data"),
        Path("/app/ziyuan_data"),
        Path("/app/ziyuan"),
        Path(os.environ.get("ZIYUAN_DATA_ROOT", "ziyuan_data")),
        # 最后才检查当前目录（避免空目录误判）
        Path("ziyuan_data"),
    ]

    @classmethod
    def get_ziyuan_root(cls) -> Path:
        for path in cls.ZIYUAN_ROOT_CANDIDATES:
            if path.exists() and path.is_dir():
                # 确保目录不是空的（包含实训资源子目录）
                training_resource_dir = path / "实训资源"
                if training_resource_dir.exists():
                    return path.absolute()
        
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[3] 
        ziyuan_path = project_root / "ziyuan_data"
        if ziyuan_path.exists():
            return ziyuan_path
            
        logger.warning("Could not locate ziyuan_data directory. Using default relative path.")
        return Path("ziyuan_data").absolute()

    @classmethod
    def load_data(cls, training_id: int, db: Session, limit: int = 10000) -> List[Dict[str, Any]]:
        training = db.query(Training).filter(Training.id == training_id).first()
        if not training:
            raise ValueError(f"Training with ID {training_id} not found.")

        # 首先尝试找SQL文件
        sql_files = cls._find_sql_files(training, db)
        if sql_files:
            logger.info(f"Loading BI data from SQL files: {[f.name for f in sql_files]}")
            return cls._load_from_sql_files(sql_files, limit)

        # 如果没有SQL文件，尝试找CSV文件
        csv_files = cls._find_csv_files(training, db)
        if csv_files:
            logger.info(f"Loading BI data from CSV files: {[f.name for f in csv_files]}")
            return cls._load_from_csv_files(csv_files, limit)

        raise FileNotFoundError(f"No data files (SQL/CSV) found for training {training_id} ({training.title})")

    @classmethod
    def _find_sql_files(cls, training: Training, db: Session) -> List[Path]:
        ziyuan_root = cls.get_ziyuan_root()
        found_files = []

        # 1. Try project_path first if available
        project_path = getattr(training, 'project_path', None)
        if project_path:
            proj_path = Path(project_path)
            # If relative, join with ziyuan_root (unless it already starts with ziyuan_data)
            if not proj_path.is_absolute():
                if str(proj_path).startswith("ziyuan_data"):
                    parts = list(proj_path.parts)
                    if parts[0] == "ziyuan_data":
                         full_path = ziyuan_root.joinpath(*parts[1:])
                    else:
                         full_path = ziyuan_root / proj_path
                else:
                    full_path = ziyuan_root / proj_path
            else:
                full_path = proj_path

            if full_path.exists():
                # Check datasets directory first
                datasets_dir = full_path / "datasets"
                if datasets_dir.exists():
                    found_files.extend(cls._scan_datasets_dir(datasets_dir))
                # Also check root training directory for SQL files
                if not found_files:
                    found_files.extend(cls._scan_sql_in_dir(full_path))

        if found_files:
            return found_files

        # 2. Try TrainingDataset
        datasets = db.query(TrainingDataset).filter(
            TrainingDataset.training_id == training.id
        ).all()

        for ds in datasets:
            if ds.file_type == 'sql_data' or (ds.file_url and ds.file_url.endswith('.sql')):
                rel_path = ds.relative_path or ds.file_url
                if rel_path.startswith("/"):
                    rel_path = rel_path[1:]
                candidate = ziyuan_root / rel_path
                if candidate.exists():
                    found_files.append(candidate)

        if found_files:
            return found_files

        # 3. Fallback: Search by naming convention
        training_resource_dir = ziyuan_root / "实训资源"
        if training_resource_dir.exists():
            for path in training_resource_dir.iterdir():
                if path.is_dir() and (training.title in path.name or path.name in training.title):
                    # Check datasets directory first
                    datasets_dir = path / "datasets"
                    if datasets_dir.exists():
                        found_files.extend(cls._scan_datasets_dir(datasets_dir))
                    # Also check root training directory for SQL files
                    if not found_files:
                        found_files.extend(cls._scan_sql_in_dir(path))
                    if found_files:
                        return found_files

        return []

    @classmethod
    def _scan_sql_in_dir(cls, directory: Path) -> List[Path]:
        """Scan for SQL files directly in a directory (not subdirectories)."""
        all_sqls = list(directory.glob("*.sql"))
        names = [f.name for f in all_sqls]
        name_to_path = {f.name: f for f in all_sqls}
        schema, other, insert = _classify_sql_files(names)
        return [name_to_path[n] for n in schema + other + insert]

    @classmethod
    def _scan_datasets_dir(cls, datasets_dir: Path) -> List[Path]:
        all_sqls = list(datasets_dir.glob("*.sql"))
        names = [f.name for f in all_sqls]
        name_to_path = {f.name: f for f in all_sqls}
        schema, other, insert = _classify_dataset_sql_files(names)
        return [name_to_path[n] for n in schema + other + insert]

    # Max file size to read fully (5MB); larger files get truncated to first N inserts
    MAX_SQL_FILE_SIZE = 5 * 1024 * 1024

    @classmethod
    def _read_sql_truncated(cls, file_path: Path, limit: int) -> str:
        """Read a large SQL file but only keep schema DDL + first `limit` INSERT statements."""
        lines_out = []
        insert_count = 0
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                upper = line.lstrip().upper()
                if upper.startswith('INSERT'):
                    insert_count += 1
                    if insert_count > limit:
                        continue
                lines_out.append(line)
        logger.info(f"Truncated {file_path.name}: kept {min(insert_count, limit)}/{insert_count} inserts")
        return ''.join(lines_out)

    @classmethod
    def _load_from_sql_files(cls, file_paths: List[Path], limit: int) -> List[Dict[str, Any]]:

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Execute all files in order
            for file_path in file_paths:
                file_size = file_path.stat().st_size
                if file_size > cls.MAX_SQL_FILE_SIZE:
                    # Large file: read only schema + first N inserts
                    logger.info(f"Large SQL file ({file_size/1024/1024:.1f}MB): {file_path.name}, truncating to ~{limit} inserts")
                    content = cls._read_sql_truncated(file_path, limit)
                else:
                    content = _read_text_safe(file_path)
                content = _sanitize_mysql_to_sqlite(content)

                logger.info(f"Executing SQL script: {file_path.name}")
                cursor.executescript(content)
            
            # Introspect to find tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("No tables found in SQLite after execution.")
                return []
                
            # Decide which table to query
            # If multiple files, e.g. retail_data.sql and retail_insert.sql
            # Table name likely matches file name or common prefix
            
            target_table = tables[0]['name']
            
            # Heuristic: Pick table with most rows? Or matching name?
            # If multiple tables, we return the one with data
            if len(tables) > 1:
                max_rows = -1
                best_table = target_table
                
                for t in tables:
                    t_name = t['name']
                    try:
                        cursor.execute(f'SELECT COUNT(*) as c FROM "{t_name}"')
                        count = cursor.fetchone()['c']
                        if count > max_rows:
                            max_rows = count
                            best_table = t_name
                    except:
                        pass
                target_table = best_table
            
            logger.info(f"Querying table: {target_table}")
            cursor.execute(f'SELECT * FROM "{target_table}" LIMIT ?', (limit,))
            rows = cursor.fetchall()
            
            result = [dict(row) for row in rows]
            return result
            
        except Exception as e:
            logger.error(f"Error processing SQL files: {e}")
            # Print to stdout as well for debugging in terminal
            print(f"CRITICAL ERROR in BIDataLoader: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            conn.close()

    @classmethod
    def _find_csv_files(cls, training: Training, db: Session) -> List[Path]:
        """查找CSV数据文件"""
        ziyuan_root = cls.get_ziyuan_root()
        found_files = []

        # 1. 尝试使用project_path
        project_path = getattr(training, 'project_path', None)
        if project_path:
            proj_path = Path(project_path)
            if not proj_path.is_absolute():
                if str(proj_path).startswith("ziyuan_data"):
                    parts = list(proj_path.parts)
                    if parts[0] == "ziyuan_data":
                        full_path = ziyuan_root.joinpath(*parts[1:])
                    else:
                        full_path = ziyuan_root / proj_path
                else:
                    full_path = ziyuan_root / proj_path
            else:
                full_path = proj_path

            if full_path.exists():
                datasets_dir = full_path / "datasets"
                if datasets_dir.exists():
                    found_files.extend(list(datasets_dir.glob("*.csv")))
                if not found_files:
                    found_files.extend(list(full_path.glob("*.csv")))

        if found_files:
            return found_files

        # 2. 按命名约定搜索
        training_resource_dir = ziyuan_root / "实训资源"
        if training_resource_dir.exists():
            for path in training_resource_dir.iterdir():
                if path.is_dir() and (training.title in path.name or path.name in training.title):
                    datasets_dir = path / "datasets"
                    if datasets_dir.exists():
                        found_files.extend(list(datasets_dir.glob("*.csv")))
                    if not found_files:
                        found_files.extend(list(path.glob("*.csv")))
                    if found_files:
                        return found_files

        return found_files

    @classmethod
    def _load_from_csv_files(cls, file_paths: List[Path], limit: int) -> List[Dict[str, Any]]:
        """从CSV文件加载数据"""
        all_data = []

        for file_path in file_paths:
            try:
                with _open_text_safe(file_path) as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        if i >= limit:
                            break
                        all_data.append(_clean_csv_row(row))

                logger.info(f"Loaded {len(all_data)} rows from {file_path.name}")

                # 只加载第一个CSV文件，或直到达到limit
                if len(all_data) >= limit:
                    break

            except Exception as e:
                logger.error(f"Error loading CSV file {file_path}: {e}")
                continue

        return all_data[:limit]
