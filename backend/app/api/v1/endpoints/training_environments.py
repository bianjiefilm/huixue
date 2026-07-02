"""
实训环境相关API端点
包括BI、AI、Jupyter等实训环境的管理
"""
import os
import sys

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path, BackgroundTasks, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import asyncio
import re
import uuid
import logging
from datetime import datetime, timezone, timedelta
import json
import base64
import httpx
from pathlib import Path as FilePath

from app.core.database import get_db
from app.core.config import settings
from app.core.permissions import get_current_user
from app.core.identity import resolve_scoped_id, require_owner_or_admin
from app.models import models as db_models
from app.models import models
from app.crud import crud
from app.schemas import schemas
from app.services.container_manager import container_manager

logger = logging.getLogger(__name__)


def _open_text_file(path, newline=None):
    """打开文本文件，自动尝试 utf-8-sig → gbk → latin-1 编码"""
    for enc in ('utf-8-sig', 'gbk', 'latin-1'):
        try:
            f = open(path, 'r', encoding=enc, newline=newline)
            f.read(1024)
            f.seek(0)
            return f
        except (UnicodeDecodeError, UnicodeError):
            continue
    return open(path, 'r', encoding='latin-1', newline=newline)


def _json_safe(value: Any) -> Any:
    """Convert common numpy/pandas values into JSON-safe primitives."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool, list, tuple, dict)):
        if isinstance(value, tuple):
            return [_json_safe(v) for v in value]
        if isinstance(value, list):
            return [_json_safe(v) for v in value]
        if isinstance(value, dict):
            return {str(k): _json_safe(v) for k, v in value.items()}
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def _training_dataset_file_path(dataset: db_models.TrainingDataset) -> str:
    """Resolve a training dataset DB row to a readable file path in the backend container."""
    candidates = []
    for raw_path in (dataset.relative_path, dataset.file_url, dataset.access_path, dataset.access_path_in_env):
        if not raw_path:
            continue
        raw = str(raw_path)
        if raw.startswith("/static/resources/"):
            candidates.append(FilePath("/app/static/resources") / raw[len("/static/resources/"):])
        elif raw.startswith("static/resources/"):
            candidates.append(FilePath("/app") / raw)
        elif raw.startswith("/app/"):
            candidates.append(FilePath(raw))
        else:
            candidates.append(FilePath("/app/static/resources") / raw)
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(f"数据集文件不存在: dataset_id={dataset.id}, path={dataset.relative_path or dataset.file_url}")


def _topological_order(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    node_map = {node.get("id"): node for node in nodes if node.get("id")}
    indegree = {node_id: 0 for node_id in node_map}
    outgoing: Dict[str, List[str]] = {node_id: [] for node_id in node_map}
    for edge in edges or []:
        source = _edge_source(edge)
        target = _edge_target(edge)
        if source in node_map and target in node_map:
            outgoing[source].append(target)
            indegree[target] += 1
    queue = [node_id for node_id in node_map if indegree[node_id] == 0]
    ordered_ids = []
    while queue:
        node_id = queue.pop(0)
        ordered_ids.append(node_id)
        for target in outgoing.get(node_id, []):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(ordered_ids) != len(node_map):
        raise ValueError("DAG 存在环或无效连线,无法拓扑排序")
    return [node_map[node_id] for node_id in ordered_ids]


def _auc_score(y_true, y_score) -> float:
    import numpy as np

    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    pos = y_true == 1
    neg = y_true == 0
    pos_count = int(pos.sum())
    neg_count = int(neg.sum())
    if pos_count == 0 or neg_count == 0:
        return 0.0
    order = np.argsort(y_score)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(y_score) + 1)
    pos_rank_sum = ranks[pos].sum()
    auc = (pos_rank_sum - pos_count * (pos_count + 1) / 2) / (pos_count * neg_count)
    return float(auc)


def _normalise_target_name(target: Any) -> Optional[str]:
    if target is None:
        return None
    target_name = str(target).strip()
    return target_name or None


def _resolve_ai_target(previous_output: Any, config: Dict[str, Any], df=None) -> Optional[str]:
    """Resolve the supervised-learning target from setRole/config/legacy columns."""
    target = _normalise_target_name(config.get("target"))
    if not target and isinstance(previous_output, dict):
        target = _normalise_target_name(previous_output.get("target"))
    if not target and df is not None:
        if "churn" in df.columns:
            target = "churn"
        elif "subscribed" in df.columns:
            target = "subscribed"
    return target


def _normalise_feature_names(features: Any) -> List[str]:
    """Resolve explicit feature columns from setRole config."""
    if features is None:
        return []
    if isinstance(features, str):
        raw_values = features.split(",")
    elif isinstance(features, (list, tuple, set)):
        raw_values = list(features)
    else:
        return []
    normalized: List[str] = []
    for value in raw_values:
        name = str(value).strip()
        if name and name not in normalized:
            normalized.append(name)
    return normalized


def _resolve_ai_features(previous_output: Any, config: Dict[str, Any]) -> List[str]:
    """Resolve explicit feature columns from current config or upstream setRole."""
    features = _normalise_feature_names(config.get("features"))
    if not features and isinstance(previous_output, dict):
        features = _normalise_feature_names(previous_output.get("features"))
    return features


def _binary_target_series(series):
    """Map common binary/multiclass labels into 0/1 for the pilot classifiers."""
    import pandas as pd

    cleaned = series.copy()
    if pd.api.types.is_bool_dtype(cleaned):
        return cleaned.astype(int)
    if pd.api.types.is_numeric_dtype(cleaned):
        unique_values = sorted(pd.Series(cleaned.dropna().unique()).tolist())
        if set(unique_values).issubset({0, 1}):
            return cleaned.astype(int)
        if len(unique_values) == 2:
            return cleaned.map({unique_values[0]: 0, unique_values[1]: 1}).astype(int)
        median_value = cleaned.median()
        return (cleaned > median_value).astype(int)

    text = cleaned.astype(str).str.strip()
    lowered = text.str.lower()
    positive_values = {"true", "1", "yes", "y", "pass", "passed", "风险", "异常", "故障", "退学", "休学"}
    negative_values = {"false", "0", "no", "n", "normal", "正常", "在读"}
    if lowered.isin(positive_values | negative_values).all():
        return lowered.map(lambda value: 0 if value in negative_values else 1).astype(int)

    # Wind SCADA uses normal/fault-kind labels. Treat normal as healthy and every
    # other label as the positive risk class.
    if lowered.eq("normal").any():
        return (~lowered.eq("normal")).astype(int)

    value_counts = lowered.value_counts()
    if len(value_counts) == 2:
        negative_label = value_counts.idxmax()
        return lowered.map(lambda value: 0 if value == negative_label else 1).astype(int)

    raise ValueError(f"目标列 {series.name} 不是可映射的二分类标签")


def _drop_non_feature_columns(df, target: Optional[str]):
    """Remove identifier/time/high-cardinality object columns before one-hot."""
    drop_columns = []
    row_count = max(1, len(df))
    for column in list(df.columns):
        if column == target:
            continue
        lower_name = column.lower()
        if (
            lower_name.endswith("_id")
            or lower_name in {"id", "customer_id", "trans_id"}
            or "timestamp" in lower_name
            or lower_name.endswith("_date")
            or lower_name.endswith("_time")
        ):
            drop_columns.append(column)
            continue
        if df[column].dtype == "object":
            unique_ratio = df[column].nunique(dropna=False) / row_count
            if unique_ratio > 0.3:
                drop_columns.append(column)
    if drop_columns:
        return df.drop(columns=drop_columns)
    return df


def _execute_ai_node(
    node: Dict[str, Any],
    previous_output: Any,
    db: Session,
    pipeline_id: str,
) -> Any:
    """Execute one AI designer node synchronously for the R6 pilot workflow."""
    import numpy as np
    import pandas as pd

    node_type = node.get("type")
    config = node.get("config") or {}

    if node_type == "readData":
        dataset_id = config.get("dataset")
        if not dataset_id:
            training_id = int(pipeline_id)
            dataset = db.query(db_models.TrainingDataset).filter(
                db_models.TrainingDataset.training_id == training_id
            ).order_by(db_models.TrainingDataset.id.asc()).first()
        else:
            dataset = db.query(db_models.TrainingDataset).filter(
                db_models.TrainingDataset.id == int(dataset_id)
            ).first()
        if not dataset:
            raise ValueError(f"读取数据失败: dataset={dataset_id} 不存在")
        file_path = _training_dataset_file_path(dataset)
        if dataset.file_type and str(dataset.file_type).lower() not in ("csv", "txt"):
            raise ValueError(f"暂不支持的数据集类型: {dataset.file_type}")
        frame = pd.read_csv(file_path)
        return {
            "_kind": "dataframe",
            "df": frame,
            "summary": {
                "dataset_id": dataset.id,
                "dataset_name": dataset.name,
                "rows": int(len(frame)),
                "columns": list(frame.columns)[:50],
            },
        }

    if node_type == "setRole":
        if not isinstance(previous_output, dict) or "df" not in previous_output:
            raise ValueError("设置角色节点缺少上游 DataFrame")
        target = _resolve_ai_target(previous_output, config, previous_output["df"])
        if not target:
            raise ValueError("设置角色失败: 请配置目标列 target")
        df = previous_output["df"]
        if target not in df.columns:
            raise ValueError(f"设置角色失败: 目标列 {target} 不存在")
        features = _normalise_feature_names(config.get("features"))
        missing_features = [feature for feature in features if feature not in df.columns]
        if missing_features:
            raise ValueError(f"设置角色失败: 特征列不存在: {', '.join(missing_features)}")
        return {
            "_kind": "dataframe",
            "df": df,
            "target": target,
            "features": features,
            "summary": {
                "rows": int(len(df)),
                "columns": list(df.columns)[:50],
                "target": target,
                "features": features,
            },
        }

    if node_type in ("featureExtract", "featureSelect"):
        if not isinstance(previous_output, dict) or "df" not in previous_output:
            raise ValueError("特征工程节点缺少上游 DataFrame")
        df = previous_output["df"].copy()
        target = _resolve_ai_target(previous_output, config, df)
        if not target and "subscribed" in df.columns and "churn" not in df.columns:
            df["churn"] = 1 - df["subscribed"].astype(int)
            target = "churn"
        if target and target not in df.columns:
            raise ValueError(f"特征工程失败: 目标列 {target} 不存在")
        explicit_features = _resolve_ai_features(previous_output, config)
        if explicit_features:
            missing_features = [feature for feature in explicit_features if feature not in df.columns]
            if missing_features:
                raise ValueError(f"特征工程失败: 特征列不存在: {', '.join(missing_features)}")
            features = [feature for feature in explicit_features if feature != target]
            selected_columns = features + ([target] if target else [])
            df = df[selected_columns]
        else:
            df = _drop_non_feature_columns(df, target)
            excluded_columns = {target} if target else set()
            if target == "churn" and "subscribed" in df.columns:
                excluded_columns.add("subscribed")
            features = [c for c in df.columns if c not in excluded_columns]
        encoded = pd.get_dummies(df[features], dummy_na=True)
        if target:
            encoded[target] = _binary_target_series(df[target])
        return {
            "_kind": "dataframe",
            "df": encoded,
            "target": target,
            "summary": {
                "rows": int(len(encoded)),
                "feature_count": int(len(encoded.columns) - (1 if target else 0)),
                "target": target,
                "features": features,
                "explicit_features": bool(explicit_features),
            },
        }

    if node_type in ("standardize", "normalize"):
        if not isinstance(previous_output, dict) or "df" not in previous_output:
            raise ValueError("标准化节点缺少上游 DataFrame")
        df = previous_output["df"].copy()
        target = _resolve_ai_target(previous_output, config, df)
        feature_columns = [c for c in df.columns if c != target]
        numeric_cols = [c for c in feature_columns if pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            means = df[numeric_cols].mean()
            stds = df[numeric_cols].std(ddof=0).replace(0, 1)
            df[numeric_cols] = (df[numeric_cols] - means) / stds
        return {
            "_kind": "dataframe",
            "df": df,
            "target": target,
            "summary": {
                "standardized_columns": len(numeric_cols),
                "rows": int(len(df)),
            },
        }

    if node_type == "dataSplit":
        if not isinstance(previous_output, dict) or "df" not in previous_output:
            raise ValueError("数据拆分节点缺少上游 DataFrame")
        df = previous_output["df"].copy()
        target = _resolve_ai_target(previous_output, config, df)
        if not target or target not in df.columns:
            target_label = target or "<未配置>"
            raise ValueError(f"数据拆分失败: 缺少目标列 {target_label}, 请检查 setRole 配置")
        rng = np.random.default_rng(int(config.get("randomState") or 42))
        indices = np.arange(len(df))
        rng.shuffle(indices)
        test_size = float(config.get("testSize") or 0.2)
        split_at = max(1, min(len(indices) - 1, int(len(indices) * (1 - test_size))))
        train_idx = indices[:split_at]
        test_idx = indices[split_at:]
        feature_columns = [c for c in df.columns if c != target]
        return {
            "_kind": "split",
            "x_train": df.iloc[train_idx][feature_columns].to_numpy(dtype=float),
            "x_test": df.iloc[test_idx][feature_columns].to_numpy(dtype=float),
            "y_train": df.iloc[train_idx][target].to_numpy(dtype=int),
            "y_test": df.iloc[test_idx][target].to_numpy(dtype=int),
            "feature_columns": feature_columns,
            "target": target,
            "summary": {
                "train_rows": int(len(train_idx)),
                "test_rows": int(len(test_idx)),
                "feature_count": len(feature_columns),
            },
        }

    if node_type in ("logisticReg", "randomForest", "decisionTree", "svm"):
        if not isinstance(previous_output, dict) or previous_output.get("_kind") != "split":
            raise ValueError("模型训练节点缺少上游 train/test split")
        x_train = previous_output["x_train"]
        y_train = previous_output["y_train"]
        x_test = previous_output["x_test"]
        y_test = previous_output["y_test"]
        if x_train.size == 0 or x_test.size == 0:
            raise ValueError("模型训练失败: 训练集或测试集为空")
        # Lightweight logistic regression implemented with numpy to avoid adding sklearn.
        x_train = np.nan_to_num(x_train.astype(float))
        x_test = np.nan_to_num(x_test.astype(float))
        x_train_b = np.c_[np.ones(len(x_train)), x_train]
        x_test_b = np.c_[np.ones(len(x_test)), x_test]
        weights = np.zeros(x_train_b.shape[1])
        lr = 0.1
        iterations = int(config.get("maxIter") or 120)
        for _ in range(max(20, min(iterations, 250))):
            logits = np.clip(x_train_b @ weights, -35, 35)
            probs = 1 / (1 + np.exp(-logits))
            grad = x_train_b.T @ (probs - y_train) / len(y_train)
            weights -= lr * grad
        test_probs = 1 / (1 + np.exp(-np.clip(x_test_b @ weights, -35, 35)))
        predictions = (test_probs >= 0.5).astype(int)
        return {
            "_kind": "model",
            "y_test": y_test,
            "predictions": predictions,
            "probabilities": test_probs,
            "summary": {
                "algorithm": "logistic_regression_numpy",
                "train_rows": int(len(y_train)),
                "test_rows": int(len(y_test)),
                "feature_count": int(x_train.shape[1]),
            },
        }

    if node_type == "modelEval":
        if not isinstance(previous_output, dict) or previous_output.get("_kind") != "model":
            raise ValueError("模型评估节点缺少上游模型输出")
        y_true = previous_output["y_test"]
        y_pred = previous_output["predictions"]
        y_prob = previous_output["probabilities"]
        tp = int(((y_true == 1) & (y_pred == 1)).sum())
        tn = int(((y_true == 0) & (y_pred == 0)).sum())
        fp = int(((y_true == 0) & (y_pred == 1)).sum())
        fn = int(((y_true == 1) & (y_pred == 0)).sum())
        accuracy = (tp + tn) / max(1, len(y_true))
        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)
        f1 = 2 * precision * recall / max(1e-12, precision + recall)
        auc = _auc_score(y_true, y_prob)
        return {
            "_kind": "metrics",
            "metrics": {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "auc": float(auc),
            },
            "summary": {
                "samples": int(len(y_true)),
                "tp": tp,
                "tn": tn,
                "fp": fp,
                "fn": fn,
            },
        }

    # Unknown nodes are treated as transparent transforms with a visible audit trail.
    if previous_output is None:
        return {"_kind": "noop", "summary": {"node_type": node_type, "message": "无上游输入,跳过"}}
    return previous_output


def _node_public_output(output: Any) -> Dict[str, Any]:
    if isinstance(output, dict):
        public = {
            key: value
            for key, value in output.items()
            if key in {"_kind", "summary", "target", "metrics"}
        }
        return _json_safe(public)
    return {"value": _json_safe(output)}


def _latest_saved_ai_dag(
    db: Session,
    pipeline_id: str,
    user_id: int,
) -> Dict[str, Any]:
    """Return the latest persisted AI designer DAG for a pipeline/user."""
    runs = db.query(db_models.PipelineRun).filter(
        db_models.PipelineRun.pipeline_id == pipeline_id,
        db_models.PipelineRun.user_id == user_id,
        db_models.PipelineRun.status == "saved",
    ).order_by(db_models.PipelineRun.created_at.desc()).limit(20).all()

    for run in runs:
        outputs = run.node_outputs or {}
        nodes = outputs.get("nodes") or []
        if nodes:
            return {
                "nodes": nodes,
                "edges": outputs.get("edges") or [],
                "source_run_id": str(run.id),
            }
    return {"nodes": [], "edges": []}


def _edge_source(edge: Dict[str, Any]) -> Optional[str]:
    return edge.get("source") or edge.get("sourceNodeId")


def _edge_target(edge: Dict[str, Any]) -> Optional[str]:
    return edge.get("target") or edge.get("targetNodeId")

router = APIRouter(
    tags=['training-environments']
)


def _resolve_training_env_type(training: db_models.Training, db: Session) -> str:
    """根据训练记录解析环境类型"""
    env_type: Optional[str] = None
    env_id_value = getattr(training, "environment_id", None)
    
    if env_id_value is not None:
        env_id_str = str(env_id_value).strip()
        if env_id_str.isdigit():
            env = db.query(db_models.TrainingEnvironment).filter(
                db_models.TrainingEnvironment.id == int(env_id_str)
            ).first()
            if env:
                env_type = env.environment_type
        elif env_id_str:
            env_type = env_id_str.upper()
    
    if not env_type and getattr(training, "training_type", None):
        training_type_str = str(training.training_type).upper()
        logger.info(f"[环境类型解析] training_type原始值: {training.training_type}, 转换后: {training_type_str}")
        if training_type_str == 'CODING':
            env_type = 'JUPYTER'
        elif training_type_str == 'DRAG_DROP' or training_type_str == 'DRAG-DROP' or 'DRAG' in training_type_str:
            env_type = 'TEMPO_BI'  # BI实训使用TEMPO_BI环境类型
            logger.info(f"[环境类型解析] 识别为BI实训，设置env_type=TEMPO_BI")
    
    if not env_type:
        env_type = "JUPYTER"
        logger.warning("实训 %s 未明确配置环境类型，使用默认 JUPYTER", training.id)
    
    return env_type


def _build_training_metadata(training: db_models.Training) -> Dict[str, Any]:
    """构建传递给容器管理器的实训元数据"""
    dataset_refs_raw = getattr(training, "superset_dataset_refs", None)
    dataset_refs: Optional[List[str]] = None
    if dataset_refs_raw:
        if isinstance(dataset_refs_raw, list):
            dataset_refs = dataset_refs_raw
        elif isinstance(dataset_refs_raw, str):
            try:
                parsed = json.loads(dataset_refs_raw)
                if isinstance(parsed, list):
                    dataset_refs = parsed
            except json.JSONDecodeError:
                logger.warning(
                    "superset_dataset_refs 字段解析失败(训练ID=%s): %s",
                    getattr(training, "id", None),
                    dataset_refs_raw[:200],
                )

    return {
        "training_id": getattr(training, "id", None),
        "training_name": getattr(training, "title", None),
        "bi_template_path": getattr(training, "bi_template_path", None),
        "superset_dashboard_id": getattr(training, "superset_dashboard_id", None),
        "superset_dataset_refs": dataset_refs,
    }


def _parse_allowed_domains(raw_value: Optional[str]) -> List[str]:
    if not raw_value:
        return ["*"]
    tokens = re.split(r"[,\s]+", raw_value)
    allowed = [token.strip() for token in tokens if token.strip()]
    return allowed or ["*"]

@router.post("/environments/superset/session")
async def ensure_superset_session(
    training_id: int = Body(...),
    user_id: int = Body(...),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """确保 Superset session 已准备就绪"""
    import httpx

    user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"), forbidden_detail="无权访问该用户的实训环境")

    guest_data: Dict[str, Any] = {}
    try:
        logger.info(f"[Superset会话] 准备会话: training_id={training_id}, user_id={user_id}")
        
        # 获取容器状态
        status_info = container_manager.get_container_status_by_training(training_id, user_id, db)
        host_port = status_info.get("host_port")
        
        if status_info.get("status") != "running" or not host_port:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Superset 环境尚未就绪，请先启动实训环境"
            )
        
        superset_domain = f"http://localhost:{host_port}"
        
        # 调用 Superset 登录 API 建立 session
        login_payload = {
            "username": settings.SUPERSET_EMBED_USERNAME,
            "password": settings.SUPERSET_EMBED_PASSWORD,
            "provider": "db",
            "refresh": True,
        }
        
        async with httpx.AsyncClient(timeout=20) as client:
            login_resp = await client.post(
                f"{superset_domain}/api/v1/security/login",
                json=login_payload,
            )
            
            if login_resp.status_code != 200:
                logger.error(
                    "[Superset会话] 登录失败 status=%s body=%s",
                    login_resp.status_code,
                    login_resp.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Superset 登录失败: {login_resp.status_code}",
                )
            
            login_data = login_resp.json()
            access_token = login_data.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Superset 登录响应缺少 access_token",
                )
            
            logger.info("[Superset会话] ✅ Session 已建立")
            
            return {
                "code": "0000",
                "message": "Superset session 已就绪",
                "data": {
                    "training_id": training_id,
                    "user_id": user_id,
                    "superset_domain": superset_domain,
                    "has_token": bool(access_token)
                }
            }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Superset会话] 准备失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Superset session 准备失败: {str(e)}"
        )

# ==================== Superset Embed ====================

@router.post("/environments/superset/embed-token")
async def create_superset_embed_token(
    training_id: int = Body(..., embed=True),
    user_id: int = Body(..., embed=True),
    viewer_role: str = Body("student", embed=True),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    颁发 Superset 嵌入用 guest token，并返回嵌入地址
    """
    user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"), forbidden_detail="无权访问该用户的实训环境")

    training = db.query(db_models.Training).filter(
        db_models.Training.id == training_id
    ).first()
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"实训ID {training_id} 不存在"
        )
    logger.info(f"[Superset嵌入] 查询到Training: id={training.id}, title={training.title}, training_type={training.training_type}")
    
    env_type = _resolve_training_env_type(training, db)
    logger.info(f"[Superset嵌入] 解析环境类型: training_type={training.training_type}, env_type={env_type}")
    if env_type.upper() != "TEMPO_BI":
        logger.warning(f"[Superset嵌入] 环境类型不匹配: env_type={env_type}, 期望=TEMPO_BI")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"仅BI实训支持 Superset 嵌入，当前环境类型: {env_type}"
        )
    
    # 明确查找 TEMPO_BI 类型的容器
    status_info = container_manager.get_container_status_by_training(
        training_id, user_id, db, env_type="TEMPO_BI"
    )
    logger.info(f"[Superset嵌入] 容器状态信息: {status_info}")
    host_port = status_info.get("host_port")
    container_status = status_info.get("status")
    logger.info(f"[Superset嵌入] 容器状态: status={container_status}, host_port={host_port}")
    if container_status != "running" or not host_port:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Superset 环境尚未就绪，状态: {container_status}, 端口: {host_port}"
        )

    dashboard_id = training.superset_dashboard_id or settings.SUPERSET_EMBED_DASHBOARD_ID
    if not dashboard_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前实训未配置 Superset 仪表盘 ID，无法生成嵌入内容",
        )
    
    superset_domain = f"http://localhost:{host_port}"
    proxy_base = "/api/v1/environments/proxy" if settings.BI_PROXY_ENABLED else None
    allowed_domains = _parse_allowed_domains(settings.BI_PARENT_ORIGIN)
    
    login_payload = {
        "username": settings.SUPERSET_EMBED_USERNAME,
        "password": settings.SUPERSET_EMBED_PASSWORD,
        "provider": "db",
        "refresh": True,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            # Resolves identifier (ID or slug) to UUID string
            async def resolve_dashboard_uuid(identifier: str, headers: Dict[str, str]) -> str:
                if not identifier:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="未提供有效的 Superset 仪表盘 ID 或 slug",
                    )

                # Use rison format for filtering
                # If numeric, check both ID and slug (though usually ID)
                # For robustness, we always query Superset to get the full record including UUID
                
                # First try filtering by ID if numeric
                filters = []
                if identifier.isdigit():
                    filters.append(f"(col:id,opr:eq,value:{identifier})")
                
                # Also allow matching by slug
                filters.append(f"(col:slug,opr:eq,value:'{identifier}')")
                
                # Construct query to try finding by ID first
                if identifier.isdigit():
                    q = f"(filters:!((col:id,opr:eq,value:{identifier})),columns:!(id,slug,uuid))"
                else:
                    q = f"(filters:!((col:slug,opr:eq,value:'{identifier}')),columns:!(id,slug,uuid))"

                resp = await client.get(
                    f"{superset_domain}/api/v1/dashboard/",
                    params={"q": q},
                    headers=headers,
                )
                
                if resp.status_code != 200:
                    logger.error(
                        "[Superset嵌入] 查询仪表盘失败 status=%s body=%s",
                        resp.status_code,
                        resp.text,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Superset 仪表盘查询失败: {resp.status_code}",
                    )

                result = resp.json().get("result") or []
                if not result:
                    # If no result by ID, try slug if it was numeric (unlikely but possible)
                    # Or just return 404
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"未找到标识符为 {identifier} 的 Superset 仪表盘",
                    )

                dashboard_record = result[0]
                uuid_val = dashboard_record.get("uuid")
                if not uuid_val:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Superset 仪表盘查询结果缺少 uuid 字段",
                    )
                return str(uuid_val)

            login_resp = await client.post(
                f"{superset_domain}/api/v1/security/login",
                json=login_payload,
            )
            if login_resp.status_code != 200:
                logger.error(
                    "[Superset嵌入] 登录失败 status=%s body=%s",
                    login_resp.status_code,
                    login_resp.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"登录 Superset 失败: {login_resp.status_code}",
                )

            login_data = login_resp.json()
            access_token = login_data.get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Superset 登录响应缺少 access_token",
                )
            
            csrf_resp = await client.get(
                f"{superset_domain}/api/v1/security/csrf_token/",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if csrf_resp.status_code != 200:
                logger.error(
                    "[Superset嵌入] 获取 CSRF token 失败 status=%s body=%s",
                    csrf_resp.status_code,
                    csrf_resp.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Superset CSRF token 获取失败",
                )
            csrf_payload = csrf_resp.json()
            csrf_token = csrf_payload.get("result") or csrf_payload.get("csrf_token")
            if not csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Superset CSRF 响应缺少 token",
                )

            auth_headers = {"Authorization": f"Bearer {access_token}"}
            
            # Resolve UUID instead of ID
            dashboard_uuid = await resolve_dashboard_uuid(dashboard_id, auth_headers)
            logger.info(f"[Superset嵌入] 解析 Dashboard ID: {dashboard_id} -> UUID: {dashboard_uuid}")

            async def ensure_embed_uuid(
                identifier: str,
            ) -> str:
                # identifier passed here is now UUID
                endpoint = (
                    f"{superset_domain}/api/v1/dashboard/{identifier}/embedded"
                )
                check_resp = await client.get(endpoint, headers=auth_headers)
                if check_resp.status_code == 200:
                    result = check_resp.json().get("result")
                    if result and result.get("uuid"):
                        return result["uuid"]
                
                # Only try creating if not found
                create_resp = await client.post(
                    endpoint,
                    headers={
                        **auth_headers,
                        "X-CSRFToken": csrf_token,
                    },
                    cookies={"csrf_token": csrf_token},
                    json={"allowed_domains": allowed_domains},
                )
                if create_resp.status_code != 200:
                    logger.error(
                        "[Superset嵌入] 创建嵌入配置失败 status=%s body=%s",
                        create_resp.status_code,
                        create_resp.text,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Superset 嵌入配置创建失败",
                    )
                created = create_resp.json().get("result")
                embed_uuid = (created or {}).get("uuid")
                if not embed_uuid:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Superset 嵌入配置响应缺少 uuid",
                    )
                return embed_uuid

            embed_uuid = await ensure_embed_uuid(dashboard_uuid)

            guest_username = f"student_{user_id}"
            guest_first_name = "Student"
            
            if viewer_role == "teacher":
                guest_username = f"teacher_viewing_{user_id}"
                guest_first_name = "Teacher"

            guest_payload = {
                "resources": [
                    {"type": "dashboard", "id": embed_uuid},
                    # We can include the dashboard UUID too, but embed_uuid is primary for embedded
                    # Include dashboard UUID just in case RLS needs it, but definitely NOT the integer ID!
                    {"type": "dashboard", "id": dashboard_uuid} 
                ],
                "rls": [],
                "user": {
                    "username": guest_username,
                    "first_name": guest_first_name,
                    "last_name": str(user_id),
                },
            }
            guest_resp = await client.post(
                f"{superset_domain}/api/v1/security/guest_token/",
                json=guest_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-CSRFToken": csrf_token,
                },
                cookies={"csrf_token": csrf_token},
            )
            
            if guest_resp.status_code != 200:
                logger.error(
                    "[Superset嵌入] guest_token 颁发失败 status=%s body=%s",
                    guest_resp.status_code,
                    guest_resp.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Superset guest_token 颁发失败: {guest_resp.status_code}",
                )

            guest_data = guest_resp.json()
            guest_token = guest_data.get("token")
            if not guest_token:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Superset guest_token 响应缺少 token 字段",
                )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[Superset嵌入] 获取 guest token 失败: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Superset 嵌入 token 获取失败",
        ) from exc

    return {
        "code": "0000",
        "message": "Superset embed token issued",
        "data": {
            "token": guest_token,
            "superset_domain": superset_domain,
            "dashboard_id": dashboard_id,
            "dashboard_numeric_id": dashboard_id, # Keep numeric ID for compatibility if needed
            "dashboard_uuid": dashboard_uuid, # Add UUID
            "embedded_dashboard_uuid": embed_uuid,
            "access_method": "embedded_sdk",
            "proxy_enabled": settings.BI_PROXY_ENABLED,
            "superset_proxy_base": proxy_base,
            "expires_at": guest_data.get("expires_at"),
        },
    }

# ==================== BI相关接口 ====================

@router.post("/bi/{scene_id}/save")
async def save_bi_scene(
    scene_id: str = Path(..., description="场景ID"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """保存可视化大屏/报表配置，持久化到 TrainingBiDraft"""
    try:
        body = await request.json() if request else {}
        user_id = current_user.get("id") or current_user.get("user_id")
        training_id = body.get("training_id")
        classroom_id = body.get("classroom_id")

        if not training_id or not classroom_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="training_id 和 classroom_id 是必需的"
            )

        draft = db.query(db_models.TrainingBiDraft).filter(
            db_models.TrainingBiDraft.training_id == int(training_id),
            db_models.TrainingBiDraft.classroom_id == int(classroom_id),
            db_models.TrainingBiDraft.student_id == int(user_id),
        ).first()

        snapshot_json = json.dumps(body.get("config", body), ensure_ascii=False)

        if draft:
            draft.draft_snapshot = snapshot_json
            draft.schema_version = body.get("schema_version")
            draft.platform_version = body.get("platform_version")
        else:
            draft = db_models.TrainingBiDraft(
                training_id=int(training_id),
                classroom_id=int(classroom_id),
                student_id=int(user_id),
                draft_snapshot=snapshot_json,
                schema_version=body.get("schema_version"),
                platform_version=body.get("platform_version"),
            )
            db.add(draft)

        db.commit()
        db.refresh(draft)

        return {
            "code": "0000",
            "message": "场景配置保存成功",
            "data": {
                "draft_id": draft.id,
                "updated_at": draft.updated_at.isoformat() if draft.updated_at else draft.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"保存场景配置错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bi/{scene_id}/preview-url")
async def get_bi_preview_url(
    scene_id: str = Path(..., description="场景ID"),
    db: Session = Depends(get_db)
):
    """获取BI场景预览URL"""
    try:
        # 生成预览URL
        preview_url = f"/preview/bi/{scene_id}?token={uuid.uuid4().hex[:8]}"
        return {
            "code": "0000",
            "message": "获取预览URL成功",
            "data": {
                "url": preview_url,
                "expires_in": 3600  # 1小时有效期
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取BI预览URL失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预览URL失败: {str(e)}"
        )

@router.get("/bi/datasets/{dataset_id}/preview")
async def get_dataset_preview(
    dataset_id: str = Path(..., description="数据集ID"),
    limit: int = Query(100, description="返回行数限制"),
    db: Session = Depends(get_db)
):
    """获取数据集预览（前N行数据）"""
    try:
        # 从数据库查询
        db_dataset = db.query(db_models.TrainingDataset).filter(
            db_models.TrainingDataset.id == int(dataset_id)
        ).first()

        if db_dataset:
            fields: List[Dict[str, str]] = []
            rows: List[Dict[str, Any]] = []
            total = 0

            file_path = db_dataset.file_url or db_dataset.relative_path
            if file_path:
                import pathlib
                abs_path = pathlib.Path(file_path)
                if not abs_path.is_absolute():
                    abs_path = pathlib.Path(settings.STATIC_FILES_PATH) / file_path
                if abs_path.exists() and abs_path.suffix.lower() in ('.csv', '.tsv'):
                    import csv
                    with _open_text_file(abs_path, newline='') as f:
                        reader = csv.DictReader(f, delimiter='\t' if abs_path.suffix.lower() == '.tsv' else ',')
                        if reader.fieldnames:
                            fields = [{"name": fn, "type": "string"} for fn in reader.fieldnames]
                        for i, row in enumerate(reader):
                            if i >= limit:
                                break
                            rows.append(dict(row))
                        total = i + 1 if rows else 0

            return {
                "code": "0000",
                "message": "获取成功",
                "data": {
                    "dataset_id": dataset_id,
                    "name": db_dataset.name,
                    "file_type": db_dataset.file_type,
                    "fields": fields,
                    "rows": rows,
                    "total": total,
                }
            }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据集 {dataset_id} 不存在"
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集预览失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预览失败: {str(e)}"
        )

@router.post("/bi/{scene_id}/snapshot")
async def export_bi_snapshot(
    scene_id: str = Path(..., description="场景ID"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """生成大屏快照 — 将当前配置 JSON 存入 TrainingBiDraft 的 draft_snapshot"""
    try:
        body = await request.json() if request else {}
        user_id = current_user.get("id") or current_user.get("user_id")
        training_id = body.get("training_id")
        classroom_id = body.get("classroom_id")

        if not training_id or not classroom_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="training_id 和 classroom_id 是必需的"
            )

        draft = db.query(db_models.TrainingBiDraft).filter(
            db_models.TrainingBiDraft.training_id == int(training_id),
            db_models.TrainingBiDraft.classroom_id == int(classroom_id),
            db_models.TrainingBiDraft.student_id == int(user_id),
        ).first()

        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到对应的 BI 草稿，请先保存场景配置"
            )

        snapshot_id = f"snapshot_{scene_id}_{uuid.uuid4().hex[:8]}"
        return {
            "code": "0000",
            "message": "快照已基于当前草稿生成",
            "data": {
                "snapshot_id": snapshot_id,
                "draft_id": draft.id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成快照错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bi/{scene_id}/snapshot/download")
async def download_bi_snapshot(
    scene_id: str = Path(..., description="场景ID"),
    training_id: int = Query(..., description="实训ID"),
    classroom_id: int = Query(..., description="课堂ID"),
    student_id: int = Query(..., description="学生ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """下载大屏快照 — 返回 draft_snapshot JSON"""
    student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student", "teacher"), forbidden_detail="无权下载该学生的快照")
    draft = db.query(db_models.TrainingBiDraft).filter(
        db_models.TrainingBiDraft.training_id == training_id,
        db_models.TrainingBiDraft.classroom_id == classroom_id,
        db_models.TrainingBiDraft.student_id == student_id,
    ).first()

    if not draft or not draft.draft_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到快照数据"
        )

    return JSONResponse(content=json.loads(draft.draft_snapshot))

@router.get("/bi/{scene_id}/detail")
async def get_bi_scene_detail(
    scene_id: str = Path(..., description="场景ID"),
    training_id: int = Query(None, description="实训ID"),
    classroom_id: int = Query(None, description="课堂ID"),
    student_id: int = Query(None, description="学生ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """获取BI场景详情（用于还原现场）— 从 TrainingBiDraft 读取"""
    try:
        if not training_id or not classroom_id or not student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="training_id, classroom_id, student_id 均为必填"
            )

        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student", "teacher"), forbidden_detail="无权访问该学生场景")

        draft = db.query(db_models.TrainingBiDraft).filter(
            db_models.TrainingBiDraft.training_id == training_id,
            db_models.TrainingBiDraft.classroom_id == classroom_id,
            db_models.TrainingBiDraft.student_id == student_id,
        ).first()

        if not draft:
            return {
                "code": "0000",
                "message": "暂无保存的场景配置",
                "data": None
            }

        config = json.loads(draft.draft_snapshot) if draft.draft_snapshot else None
        return {
            "code": "0000",
            "message": "获取场景详情成功",
            "data": {
                "draft_id": draft.id,
                "config": config,
                "schema_version": draft.schema_version,
                "platform_version": draft.platform_version,
                "updated_at": (draft.updated_at or draft.created_at).isoformat() if (draft.updated_at or draft.created_at) else None
            }
        }

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取场景详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取详情失败: {str(e)}"
        )

# ==================== AI相关接口 ====================

@router.post("/ai/{pipeline_id}/run")
async def run_ai_pipeline(
    pipeline_id: str = Path(..., description="Pipeline ID"),
    dag: Dict[str, Any] = Body(..., description="DAG配置"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """运行AI Pipeline — 同步执行已保存 DAG 并写入节点执行记录"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        user_id_int = int(user_id)

        nodes = (dag or {}).get("nodes") or []
        edges = (dag or {}).get("edges") or []
        source_run_id = None
        if not nodes:
            saved_dag = _latest_saved_ai_dag(db, pipeline_id, user_id_int)
            nodes = saved_dag.get("nodes") or []
            edges = saved_dag.get("edges") or []
            source_run_id = saved_dag.get("source_run_id")
        if not nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline DAG 为空,请先保存画布后再运行"
            )

        ordered_nodes = _topological_order(nodes, edges)
        predecessor_map: Dict[str, List[str]] = {node.get("id"): [] for node in nodes if node.get("id")}
        for edge in edges or []:
            source = _edge_source(edge)
            target = _edge_target(edge)
            if source and target and target in predecessor_map:
                predecessor_map[target].append(source)

        pipeline_run = db_models.PipelineRun(
            pipeline_id=pipeline_id,
            user_id=user_id_int,
            status="running",
            started_at=datetime.now(timezone.utc),
            node_outputs={
                "nodes": nodes,
                "edges": edges,
                "source_run_id": source_run_id,
                "outputs": {},
            },
            metrics={},
        )
        db.add(pipeline_run)
        db.commit()
        db.refresh(pipeline_run)

        outputs_by_node: Dict[str, Any] = {}
        public_outputs: Dict[str, Any] = {}
        final_output: Any = None

        try:
            for node in ordered_nodes:
                node_id = str(node.get("id"))
                node_type = str(node.get("type") or "unknown")
                predecessor_ids = predecessor_map.get(node_id) or []
                input_output = outputs_by_node.get(predecessor_ids[0]) if predecessor_ids else final_output

                started_at = datetime.now(timezone.utc)
                node_execution = db_models.NodeExecution(
                    run_id=pipeline_run.id,
                    node_id=node_id,
                    node_type=node_type,
                    status="running",
                    input_data={
                        "predecessors": predecessor_ids,
                        "config": _json_safe(node.get("config") or {}),
                    },
                    output_data={},
                    started_at=started_at,
                )
                db.add(node_execution)
                db.commit()
                db.refresh(node_execution)

                node_output = _execute_ai_node(node, input_output, db, pipeline_id)
                public_output = _node_public_output(node_output)
                completed_at = datetime.now(timezone.utc)
                node_execution.status = "completed"
                node_execution.output_data = public_output
                node_execution.execution_time = round((completed_at - started_at).total_seconds(), 4)
                node_execution.completed_at = completed_at

                outputs_by_node[node_id] = node_output
                public_outputs[node_id] = public_output
                final_output = node_output
                pipeline_run.node_outputs = {
                    "nodes": nodes,
                    "edges": edges,
                    "source_run_id": source_run_id,
                    "outputs": public_outputs,
                }
                db.commit()

            metrics = {}
            if isinstance(final_output, dict):
                metrics = _json_safe(final_output.get("metrics") or {})
            pipeline_run.status = "success"
            pipeline_run.completed_at = datetime.now(timezone.utc)
            pipeline_run.metrics = metrics
            pipeline_run.node_outputs = {
                "nodes": nodes,
                "edges": edges,
                "source_run_id": source_run_id,
                "outputs": public_outputs,
            }
            db.commit()
            db.refresh(pipeline_run)
        except HTTPException:
            raise
        except Exception as exc:
            db.rollback()
            pipeline_run.status = "failed"
            pipeline_run.error_message = str(exc)
            pipeline_run.completed_at = datetime.now(timezone.utc)
            db.add(pipeline_run)
            db.commit()
            logger.exception("AI Pipeline DAG 执行失败: %s", exc)
            raise

        return {
            "code": "0000",
            "message": "Pipeline 运行完成",
            "data": {
                "run_id": pipeline_run.id,
                "pipeline_id": pipeline_id,
                "status": pipeline_run.status,
                "node_count": len(ordered_nodes),
                "metrics": pipeline_run.metrics or {},
                "started_at": pipeline_run.started_at.isoformat() if pipeline_run.started_at else None,
                "completed_at": pipeline_run.completed_at.isoformat() if pipeline_run.completed_at else None,
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"运行AI Pipeline失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"运行失败: {str(e)}"
        )

@router.get("/ai/{run_id}/logs")
async def get_ai_run_logs(
    run_id: str = Path(..., description="运行ID"),
    offset: int = Query(0, description="日志偏移量"),
    limit: int = Query(100, description="返回条数"),
    db: Session = Depends(get_db)
):
    """获取AI运行日志 — 从 PipelineRun + NodeExecution 读取"""
    try:
        pipeline_run = db.query(db_models.PipelineRun).filter(
            db_models.PipelineRun.id == run_id
        ).first()
        if not pipeline_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"运行记录 {run_id} 不存在"
            )

        executions = db.query(db_models.NodeExecution).filter(
            db_models.NodeExecution.run_id == run_id
        ).order_by(db_models.NodeExecution.started_at).offset(offset).limit(limit).all()

        total = db.query(db_models.NodeExecution).filter(
            db_models.NodeExecution.run_id == run_id
        ).count()

        logs = [
            {
                "node_id": ex.node_id,
                "node_type": ex.node_type,
                "status": ex.status,
                "level": "success" if ex.status == "completed" else ("error" if ex.status == "failed" else "info"),
                "message": f"{ex.node_type} {ex.status}",
                "started_at": ex.started_at.isoformat() if ex.started_at else None,
                "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
                "execution_time": ex.execution_time,
                "error_message": ex.error_message,
                "output_data": ex.output_data,
            }
            for ex in executions
        ]

        return {
            "code": "0000",
            "message": "获取日志成功",
            "data": {
                "run_id": run_id,
                "run_status": pipeline_run.status,
                "logs": logs,
                "total": total,
                "has_more": (offset + limit) < total
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI运行日志失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日志失败: {str(e)}"
        )

@router.get("/ai/{pipeline_id}/pipeline")
async def get_saved_ai_pipeline(
    pipeline_id: str = Path(..., description="Pipeline ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取最近一次已保存的 AI Pipeline 配置"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        saved_dag = _latest_saved_ai_dag(db, pipeline_id, int(user_id))
        nodes = saved_dag.get("nodes") or []
        edges = saved_dag.get("edges") or []

        return {
            "code": "0000",
            "message": "获取 Pipeline 配置成功" if nodes else "暂无已保存的 Pipeline 配置",
            "data": {
                "pipeline_id": pipeline_id,
                "run_id": saved_dag.get("source_run_id"),
                "nodes": nodes,
                "edges": edges,
                "nodes_count": len(nodes),
                "edges_count": len(edges),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI Pipeline配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Pipeline配置失败: {str(e)}"
        )

@router.post("/ai/{pipeline_id}/save")
async def save_ai_pipeline(
    pipeline_id: str = Path(..., description="Pipeline ID"),
    dag: Dict[str, Any] = Body(..., description="DAG配置"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """保存AI Pipeline配置 — 写入一条独立 saved PipelineRun"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")

        pipeline_run = db_models.PipelineRun(
            pipeline_id=pipeline_id,
            user_id=int(user_id),
            status="saved",
            node_outputs=dag,
            metrics={},
        )
        db.add(pipeline_run)

        db.commit()
        db.refresh(pipeline_run)

        return {
            "code": "0000",
            "message": "Pipeline 配置保存成功",
            "data": {
                "run_id": pipeline_run.id,
                "pipeline_id": pipeline_id,
                "saved_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"保存AI Pipeline失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存失败: {str(e)}"
        )

# ==================== AI模型库接口 ====================

@router.get("/ai/models")
async def get_ai_models(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取用户保存的AI模型列表
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id")

        # 从数据库获取模型列表
        models_list = db.query(models.AIModel).filter(
            models.AIModel.user_id == user_id
        ).order_by(models.AIModel.created_at.desc()).all()

        return {
            "code": "0000",
            "message": "获取模型列表成功",
            "data": {
                "models": [
                    {
                        "id": model.id,
                        "name": model.name,
                        "type": model.model_type,
                        "description": model.description,
                        "tags": model.tags if isinstance(model.tags, list) else [],
                        "version": model.version,
                        "created_at": model.created_at.isoformat() if model.created_at else None,
                        "updated_at": model.updated_at.isoformat() if model.updated_at else None
                    }
                    for model in models_list
                ],
                "total": len(models_list)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI模型列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型列表失败: {str(e)}"
        )

@router.post("/ai/models")
async def save_ai_model(
    model_data: Dict[str, Any] = Body(..., description="模型数据"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    保存AI模型到模型库
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        model_name = model_data.get("name", "未命名模型")
        model_type = model_data.get("type", "custom")
        description = model_data.get("description", "")
        tags = model_data.get("tags", [])
        config = model_data.get("config", {})

        # 创建新模型记录
        new_model = models.AIModel(
            user_id=user_id,
            name=model_name,
            model_type=model_type,
            description=description,
            tags=tags,
            config=config,
            version=1
        )
        db.add(new_model)
        db.commit()
        db.refresh(new_model)

        return {
            "code": "0000",
            "message": "模型保存成功",
            "data": {
                "model_id": new_model.id,
                "name": new_model.name,
                "type": new_model.model_type,
                "created_at": new_model.created_at.isoformat() if new_model.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存AI模型失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存模型失败: {str(e)}"
        )

@router.delete("/ai/models/{model_id}")
async def delete_ai_model(
    model_id: str = Path(..., description="模型ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    从模型库删除AI模型
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id")

        # 查找并删除模型
        model = db.query(models.AIModel).filter(
            models.AIModel.id == model_id,
            models.AIModel.user_id == user_id
        ).first()

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在或无权限删除"
            )

        db.delete(model)
        db.commit()

        return {
            "code": "0000",
            "message": "模型删除成功",
            "data": {
                "model_id": model_id,
                "deleted_at": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除AI模型失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除模型失败: {str(e)}"
        )

@router.get("/ai/models/{model_id}")
async def get_ai_model_detail(
    model_id: str = Path(..., description="模型ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取AI模型详情
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id")

        # 查找模型
        model = db.query(models.AIModel).filter(
            models.AIModel.id == model_id
        ).first()

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )

        # 检查权限（用户自己的模型或公开模型）
        if model.user_id != user_id and not model.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此模型"
            )

        return {
            "code": "0000",
            "message": "获取成功",
            "data": {
                "id": model.id,
                "name": model.name,
                "model_type": model.model_type,
                "description": model.description,
                "tags": model.tags or [],
                "config": model.config or {},
                "version": model.version,
                "is_published": model.is_published,
                "user_id": model.user_id,
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI模型详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型详情失败: {str(e)}"
        )

@router.put("/ai/models/{model_id}")
async def update_ai_model(
    model_id: str = Path(..., description="模型ID"),
    model_data: Dict[str, Any] = Body(..., description="模型更新数据"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    更新AI模型
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id")

        # 查找模型
        model = db.query(models.AIModel).filter(
            models.AIModel.id == model_id,
            models.AIModel.user_id == user_id
        ).first()

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在或无权限修改"
            )

        # 更新字段
        if "name" in model_data and model_data["name"]:
            model.name = model_data["name"]

        if "description" in model_data:
            model.description = model_data["description"]

        if "model_type" in model_data and model_data["model_type"]:
            model.model_type = model_data["model_type"]

        if "tags" in model_data:
            model.tags = model_data["tags"]

        if "config" in model_data:
            model.config = model_data["config"]

        if "is_published" in model_data:
            model.is_published = model_data["is_published"]

        # 版本号递增
        model.version = model.version + 1 if model.version else 1
        model.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(model)

        logger.info(f"AI模型更新成功: model_id={model_id}, version={model.version}")

        return {
            "code": "0000",
            "message": "模型更新成功",
            "data": {
                "id": model.id,
                "name": model.name,
                "model_type": model.model_type,
                "version": model.version,
                "updated_at": model.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新AI模型失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新模型失败: {str(e)}"
        )

@router.post("/ai/{pipeline_id}/single-step")
async def execute_single_step(
    pipeline_id: str = Path(..., description="Pipeline ID"),
    step_data: Dict[str, Any] = Body(..., description="单步执行参数"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    单步执行Pipeline中的某个节点
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        node_id = step_data.get("node_id")

        if not node_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="node_id为必填参数"
            )

        # 查找最近的 PipelineRun 并创建 NodeExecution 记录
        pipeline_run = db.query(db_models.PipelineRun).filter(
            db_models.PipelineRun.pipeline_id == pipeline_id,
            db_models.PipelineRun.user_id == int(user_id),
        ).order_by(db_models.PipelineRun.created_at.desc()).first()

        if not pipeline_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到对应的 Pipeline 运行记录，请先运行 Pipeline"
            )

        node_execution = db_models.NodeExecution(
            run_id=pipeline_run.id,
            node_id=node_id,
            node_type=step_data.get("node_type", "unknown"),
            status="pending",
            input_data=step_data.get("input_data"),
        )
        db.add(node_execution)
        db.commit()
        db.refresh(node_execution)

        return {
            "code": "0000",
            "message": "单步执行已提交",
            "data": {
                "execution_id": node_execution.id,
                "status": node_execution.status,
                "node_id": node_id
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"单步执行失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"单步执行逻辑崩溃: {str(e)}"
        )

@router.get("/ai/{run_id}/insights")
async def get_pipeline_insights(
    run_id: str = Path(..., description="运行ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取Pipeline执行洞察数据
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id")

        pipeline_run = db.query(db_models.PipelineRun).filter(
            db_models.PipelineRun.id == run_id
        ).first()

        if not pipeline_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"运行记录 {run_id} 不存在"
            )

        executions = db.query(db_models.NodeExecution).filter(
            db_models.NodeExecution.run_id == run_id
        ).all()

        return {
            "code": "0000",
            "message": "获取洞察数据成功",
            "data": {
                "run_id": run_id,
                "status": pipeline_run.status,
                "metrics": pipeline_run.metrics or {},
                "node_count": len(executions),
                "completed_nodes": sum(1 for e in executions if e.status == "completed"),
                "failed_nodes": sum(1 for e in executions if e.status == "failed"),
                "total_execution_time": sum(e.execution_time or 0 for e in executions),
                "started_at": pipeline_run.started_at.isoformat() if pipeline_run.started_at else None,
                "completed_at": pipeline_run.completed_at.isoformat() if pipeline_run.completed_at else None,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Pipeline洞察数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取洞察数据失败: {str(e)}"
        )

# ==================== 通用环境启动接口 ====================

@router.get("/environments/active")
async def get_active_environment(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取当前用户的活跃环境
    用于检测环境冲突 (2.7)
    """
    try:
        # 从数据库读取并发实验设置
        concurrent_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == 'concurrent_experiment_enabled'
        ).first()

        # 检查是否允许多环境（默认为False，即不允许）
        allow_multiple = concurrent_setting and concurrent_setting.value == 'true'
        if allow_multiple:
            # 如果允许多环境，返回null表示没有冲突
            return schemas.ApiResponse(
                code="0000",
                message="允许多环境，无需检查",
                data=None
            )
        
        user_id = current_user.get("id") or current_user.get("user_id")
        
        # 查询用户活跃环境
        active_env = db.query(models.EnvironmentSession).filter(
            models.EnvironmentSession.user_id == user_id,
            models.EnvironmentSession.status == 'active'
        ).first()
        
        if not active_env:
            return schemas.ApiResponse(
                code="0000",
                message="无活跃环境",
                data=None
            )
        
        # 获取实践信息
        practice = db.query(models.Practice).filter(
            models.Practice.id == active_env.practice_id
        ).first()
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "id": active_env.id,
                "practiceId": str(active_env.practice_id),
                "practiceName": practice.title if practice else "未知实践",
                "environmentType": active_env.environment_type,
                "startTime": active_env.created_at.isoformat() if active_env.created_at else None,
                "url": active_env.url
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取活跃环境失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取活跃环境失败: {str(e)}"
        )


@router.post("/environments/launch")
async def launch_environment(
    request: Dict[str, Any] = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    启动环境（通用接口，支持Jupyter、BI、AI等所有环境类型）
    
    请求体格式1（实训）：
    {
        "training_id": int,
        "user_id": int
    }
    
    请求体格式2（实践课程）：
    {
        "practiceId": str,
        "environmentType": str
    }
    """
    try:
        # 支持两种参数格式
        training_id = request.get("training_id")
        user_id = request.get("user_id") or current_user.get("id") or current_user.get("user_id")
        practice_id = request.get("practiceId")
        environment_type = request.get("environmentType")
        
        # 如果是实践课程格式，创建环境会话并返回
        if practice_id and environment_type:
            # 创建环境会话
            from app.crud.crud import create_environment_session
            env_session = create_environment_session(
                db=db,
                practice_id=int(practice_id),
                user_id=int(user_id),
                environment_type=environment_type
            )
            
            # 根据环境类型返回对应的访问URL
            access_url = None
            if environment_type == 'desktop':
                # VDI云桌面环境 - 使用noVNC
                access_url = "http://localhost:6080/vnc.html?autoconnect=true&password=huixue123"
            elif environment_type == 'shell':
                # Shell终端环境 - 使用前端模拟终端
                access_url = None  # 前端已内置终端
            
            return schemas.ApiResponse(
                code="0000",
                message="环境会话创建成功",
                data={
                    "id": env_session.id,
                    "practice_id": env_session.practice_id,
                    "environment_type": env_session.environment_type,
                    "status": env_session.status,
                    "access_url": access_url,
                    "created_at": env_session.created_at.isoformat() if env_session.created_at else None
                }
            )
        
        if not training_id or not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="training_id 和 user_id 是必需的"
            )
        
        training = db.query(db_models.Training).filter(
            db_models.Training.id == training_id
        ).first()
        if not training:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"实训ID {training_id} 不存在"
            )
        
        env_type = _resolve_training_env_type(training, db)
        training_metadata = _build_training_metadata(training)
        
        # 检查是否已有运行中的容器
        existing_container_id = container_manager.get_existing_container(
            user_id, training_id, env_type, db
        )
        
        if existing_container_id:
            # 返回现有容器状态
            status_info = container_manager.get_container_status(existing_container_id)
            return {
                "code": "0000",
                "message": "环境已运行",
                "data": {
                    "container_id": existing_container_id,
                    "status": status_info["status"],
                    "url": status_info["url"],
                    "host_port": status_info["host_port"]
                }
            }
        
        # 准备环境资源注入配置 (V3.0 新增)
        from app.services.resource_sync_v3.environment_launcher import EnvironmentLauncher
        environment_launcher = EnvironmentLauncher()

        # 异步获取资源配置（避免阻塞主线程）
        resource_config_task = None
        try:
            # 在后台准备资源配置
            resource_config_task = asyncio.create_task(
                environment_launcher.prepare_environment_resources(training_id, db)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"准备环境资源配置失败: {e}")

        # 异步启动容器
        training_name = training.title if hasattr(training, 'title') else None

        # 先创建一个"starting"状态的容器记录，让前端可以立即查询
        # 使用UUID作为临时container_id，稍后会被替换为真实的Docker容器ID
        temp_container_id = str(uuid.uuid4())
        container_process = db_models.ContainerProcess(
            container_id=temp_container_id,  # 临时ID，稍后会被替换
            container_name=f"starting-{env_type.lower()}-{training_id}",
            user_id=user_id,
            training_id=training_id,
            environment_type=env_type.upper(),
            status="starting",
            start_time=datetime.now(timezone.utc),
        )
        db.add(container_process)
        db.commit()
        db.refresh(container_process)

        # 创建一个新的数据库会话用于后台任务
        from app.core.database import SessionLocal
        record_id = container_process.id  # 保存记录ID

        async def start_container_task():
            # 在后台任务中创建新的数据库会话
            logger.info(f"[BACKGROUND_TASK] 开始启动容器: training_id={training_id}, user_id={user_id}, env_type={env_type}")
            db_session = SessionLocal()
            try:
                # 等待资源配置准备完成（如果有的话）
                init_config = None
                if resource_config_task:
                    try:
                        init_config = await resource_config_task
                        logger.info(f"实训 {training_id} 资源配置准备完成: {len(init_config.get('resources', {}).get('sql_scripts', []))} 个SQL脚本, {len(init_config.get('resources', {}).get('bi_templates', []))} 个BI模板")
                    except HTTPException:
                        raise
                    except Exception as e:
                        logger.error(f"获取资源配置失败: {e}")
                        init_config = None

                logger.info(f"[BACKGROUND_TASK] 调用container_manager.start_container()")
                container_id, host_port = container_manager.start_container(
                    env_type=env_type,
                    user_id=user_id,
                    training_id=training_id,
                    training_name=training_name,
                    db=db_session,
                    existing_record_id=record_id,
                    training_metadata=dict(training_metadata) if training_metadata else None,
                    # V3.0 新增：传递资源配置用于环境变量注入
                    init_config=init_config
                )
                logger.info(f"[BACKGROUND_TASK] 容器启动成功: container_id={container_id}, host_port={host_port}")

                # V3.0 新增：如果有资源配置，在容器启动后注入资源
                if init_config and container_id and host_port:
                    try:
                        logger.info(f"开始向容器 {container_id} 注入资源...")
                        injection_success = await environment_launcher.inject_resources_into_container(
                            container_id=container_id,
                            init_config=init_config,
                            container_host="localhost",
                            container_port=host_port
                        )
                        if injection_success:
                            logger.info(f"容器 {container_id} 资源注入成功")
                        else:
                            logger.warning(f"容器 {container_id} 资源注入失败，但容器将继续运行")
                    except HTTPException:
                        raise
                    except Exception as e:
                        logger.error(f"容器资源注入异常: {e}")
                        # 不因为资源注入失败而影响容器启动

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"后台启动容器失败: {e}")
                # 更新容器状态为error
                try:
                    container_process = db_session.query(db_models.ContainerProcess).filter(
                        db_models.ContainerProcess.id == record_id
                    ).first()
                    if container_process:
                        container_process.status = "error"
                        db_session.commit()
                except:
                    pass
            finally:
                db_session.close()
        
        background_tasks.add_task(start_container_task)
        
        # 立即返回启动中状态
        return {
            "code": "0000",
            "message": "环境启动中，请稍候...",
            "data": {
                "container_id": None,  # 将在后台创建
                "record_id": record_id,  # 临时记录ID，用于查询
                "status": "starting",
                "env_type": env_type,
                "training_id": training_id,
                "user_id": user_id
            }
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动环境失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动失败: {str(e)}"
        )


@router.get("/environments/query")
async def query_container_by_training(
    training_id: int = Query(..., description="实训ID"),
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """根据training_id和user_id查询容器ID"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"), forbidden_detail="无权查询该用户的实训环境")
        container_process = db.query(db_models.ContainerProcess).filter(
            db_models.ContainerProcess.training_id == training_id,
            db_models.ContainerProcess.user_id == user_id
        ).order_by(db_models.ContainerProcess.created_at.desc()).first()
        
        if container_process:
            # 如果后台任务仍在启动容器，直接返回 starting 状态，避免访问临时ID导致 404
            if container_process.status == "starting":
                return {
                    "code": "0000",
                    "message": "环境启动中",
                    "data": {
                        "container_id": container_process.container_id,
                        "status": "starting",
                        "url": None,
                        "host_port": None
                    }
                }
            
            # 如果后台标记为 error/stopped，直接返回，避免误报
            if container_process.status in ("error", "stopped"):
                return {
                    "code": "0000",
                    "message": "环境状态已更新",
                    "data": {
                        "container_id": container_process.container_id,
                        "status": container_process.status,
                        "url": None,
                        "host_port": None,
                        "error": "环境启动失败" if container_process.status == "error" else "环境已停止"
                    }
                }
            
            status_info = container_manager.get_container_status(container_process.container_id)
            return {
                "code": "0000",
                "message": "查询成功",
                "data": {
                    "container_id": container_process.container_id,
                    "status": status_info["status"],
                    "url": status_info["url"],
                    "host_port": status_info["host_port"]
                }
            }
        else:
            return {
                "code": "0000",
                "message": "未找到容器",
                "data": {
                    "container_id": None,
                    "status": "not_found"
                }
            }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询容器失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/environments/{container_id}/status")
async def get_environment_status(
    container_id: str = Path(..., description="容器ID"),
    db: Session = Depends(get_db)
):
    """获取环境状态（用于轮询）"""
    try:
        status_info = container_manager.get_container_status(container_id)
        
        # 更新数据库中的状态
        container_process = db.query(db_models.ContainerProcess).filter(
            db_models.ContainerProcess.container_id == container_id
        ).first()
        
        if container_process:
            container_process.status = status_info["status"]
            if status_info["status"] == "running":
                container_process.last_activity = datetime.now(timezone.utc)
            db.commit()
        
        return {
            "code": "0000",
            "message": "获取状态成功",
            "data": status_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取环境状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )


@router.post("/environments/{session_id}/stop")
async def stop_environment(
    session_id: str = Path(..., description="环境会话ID或容器ID"),
    db: Session = Depends(get_db)
):
    """停止环境 - 支持session_id或container_id"""
    try:
        # 首先尝试作为session_id查找环境会话
        from app.models.models import EnvironmentSession
        env_session = db.query(EnvironmentSession).filter(
            EnvironmentSession.id == session_id
        ).first()
        
        if env_session:
            # 找到环境会话，更新状态为stopped
            env_session.status = "stopped"
            db.commit()
            logger.info(f"环境会话 {session_id} 已标记为停止")
            return {
                "code": "0000",
                "message": "环境停止成功",
                "data": {
                    "session_id": session_id,
                    "stopped_at": datetime.now().isoformat()
                }
            }
        
        # 如果不是session_id，尝试作为container_id处理
        success = container_manager.stop_container(session_id, db)
        
        if success:
            return {
                "code": "0000",
                "message": "环境停止成功",
                "data": {
                    "container_id": session_id,
                    "stopped_at": datetime.now().isoformat()
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="环境会话或容器不存在"
            )
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止环境失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止失败: {str(e)}"
        )


# ==================== Jupyter相关接口（保留兼容性） ====================

@router.get("/jupyter/{training_id}/launch")
async def launch_jupyter(
    training_id: int = Path(..., description="实训ID"),
    student_id: Optional[int] = Query(None, description="学生ID（用于教师查看学生环境）"),
    classroom_id: Optional[int] = Query(None, description="课堂ID"),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user = Depends(get_current_user)
):
    """启动Jupyter环境（兼容性接口）"""
    # 安全提取 user_id，支持 dict 和 User 对象两种情况
    current_user_id = current_user.get('id') or current_user.get('user_id') if isinstance(current_user, dict) else current_user.id
    current_user_role = current_user.get('role') if isinstance(current_user, dict) else current_user.role

    user_id = current_user_id
    
    # 权限控制 (IDOR 修复)
    if student_id and str(student_id) != str(current_user_id):
        # 必须是教师或管理员
        from app.models.models import UserRole, Classroom
        if current_user_role not in ["ADMIN", "TEACHER", UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：只有教师或管理员才能访问其他学员的实训环境"
            )
        
        # 对于教师，验证其是否负责该课堂
        if classroom_id and current_user_role in ["TEACHER", UserRole.TEACHER]:
            classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
            if not classroom or str(classroom.teacher_id) != str(current_user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：您并非该课堂的负责教师"
                )
        
        user_id = student_id

    # 检查是否已有运行中的容器
    existing_container_id = container_manager.get_existing_container(
        user_id, training_id, "JUPYTER", db
    )

    if existing_container_id:
        # 返回现有容器状态，包含remainingTime
        status_info = container_manager.get_container_status(existing_container_id)
        return {
            "code": "0000",
            "message": "环境已运行",
            "data": {
                "container_id": existing_container_id,
                "status": status_info["status"],
                "url": status_info["url"],
                "host_port": status_info["host_port"],
                "remainingTime": 30,  # 默认30分钟
                "envId": existing_container_id
            }
        }

    # 调用通用环境启动接口
    result = await launch_environment(
        request={"training_id": training_id, "user_id": user_id},
        background_tasks=background_tasks,
        db=db
    )

    # 确保返回remainingTime字段和url字段
    if isinstance(result, dict) and "data" in result:
        result["data"]["remainingTime"] = 30  # 默认30分钟
        result["data"]["envId"] = result["data"].get("container_id") or result["data"].get("record_id")

        # 如果状态是 running，使用实际的 host_port 构建完整URL
        if result["data"].get("status") == "running":
            host_port = result["data"].get("host_port")
            if host_port:
                # 从请求中获取服务器地址，或使用默认值
                from app.core.config import settings
                # 使用配置的基础URL或从请求中获取
                base_url = getattr(settings, 'JUPYTER_BASE_URL', None)
                if not base_url:
                    # 从请求头获取原始主机
                    base_url = "http://100.74.141.3"  # 默认服务器IP
                result["data"]["url"] = f"{base_url}:{host_port}/lab?token=huixue_token"
                logger.info(f"[JUPYTER_LAUNCH] 返回动态URL: {result['data']['url']}")
        # 如果状态是 starting，也返回共享的 Jupyter URL 以便前端可以显示
        # 这样用户在容器启动期间也能看到 Jupyter 界面
        elif result["data"].get("status") == "starting" and not result["data"].get("url"):
            # 返回共享 Jupyter 容器 URL，使用配置中的基础 URL 或默认值
            from app.core.config import settings
            jupyter_base_url = getattr(settings, 'JUPYTER_BASE_URL', None) or "http://localhost:8888"
            result["data"]["url"] = f"{jupyter_base_url}/lab?token=huixue_token"
            logger.info(f"[JUPYTER_LAUNCH] 返回共享 Jupyter URL: {result['data']['url']}")

    return result

@router.post("/jupyter/{env_id}/extend-time")
async def extend_jupyter_time(
    env_id: str = Path(..., description="环境ID"),
    minutes: int = Body(30, description="延长时间（分钟）"),
    db: Session = Depends(get_db)
):
    """延长Jupyter环境时间"""
    try:
        return {
            "code": "0000",
            "message": f"环境时间延长{minutes}分钟",
            "data": {
                "env_id": env_id,
                "extended_minutes": minutes,
                "new_expires_in": minutes * 60,  # 转换为秒
                "extended_at": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"延长Jupyter时间失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"延长时间失败: {str(e)}"
        )

@router.post("/jupyter/{env_id}/reset-env")
async def reset_jupyter_env(
    env_id: str = Path(..., description="环境ID"),
    db: Session = Depends(get_db)
):
    """重置Jupyter环境（恢复依赖）"""
    try:
        return schemas.ApiResponse(
            code="0000",
            message="环境重置成功",
            data={
                "env_id": env_id,
                "reset_type": "environment",
                "reset_at": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置Jupyter环境失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置环境失败: {str(e)}"
        )

@router.post("/jupyter/{env_id}/reset-repo")
async def reset_jupyter_repo(
    env_id: str = Path(..., description="环境ID"),
    db: Session = Depends(get_db)
):
    """重置代码仓库（清空用户修改）"""
    try:
        return {
            "code": "0000",
            "message": "代码仓库重置成功（警告：所有修改已清空）",
            "data": {
                "env_id": env_id,
                "reset_type": "repository",
                "reset_at": datetime.now().isoformat(),
                "warning": "所有用户修改已被清空，此操作不可撤销"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置代码仓库失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置代码仓库失败: {str(e)}"
        )

# ==================== 通用接口 ====================

@router.get("/trainings/{training_id}/handbook")
async def get_training_handbook(
    training_id: int = Path(..., description="实训ID"),
    db: Session = Depends(get_db)
):
    """获取实训手册（Markdown格式）"""
    try:
        # 查询实训信息
        training = db.query(db_models.Training).filter(
            db_models.Training.id == training_id
        ).first()

        if not training:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"实训ID {training_id} 不存在"
            )

        # 构建手册内容
        current_date = datetime.now().strftime('%Y-%m-%d')
        default_objectives = '''- 掌握相关技能
- 完成实训任务
- 提交作业'''
        handbook_content = f"""# {training.title}

## 实训简介
{training.intro or '暂无简介'}

## 学习目标
{default_objectives}

## 操作指南

### 1. 环境准备
- 确保网络连接正常
- 使用Chrome或Firefox浏览器
- 检查实训资源是否加载完成

### 2. 实训步骤
1. 阅读任务要求
2. 分析数据集
3. 编写代码/配置模型
4. 运行并查看结果
5. 优化调整
6. 保存并提交

### 3. 注意事项
- 定期保存你的工作
- 注意环境时间限制
- 遇到问题可查看帮助文档

## 评分标准
- 功能完整性：40%
- 代码质量：30%
- 结果正确性：30%

## 常见问题
**Q: 环境无法启动怎么办？**
A: 请刷新页面重试，或联系技术支持。

**Q: 如何保存我的工作？**
A: 点击保存按钮或使用快捷键 Ctrl+S。

---
*最后更新：{current_date}*
"""

        return {
            "code": "0000",
            "message": "获取手册成功",
            "data": {
                "training_id": training_id,
                "content": handbook_content,
                "format": "markdown"
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训手册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取手册失败: {str(e)}"
        )

@router.get("/trainings/{training_id}/datasets")
async def get_training_datasets(
    training_id: int = Path(..., description="实训ID"),
    db: Session = Depends(get_db)
):
    """获取实训数据集列表 - 从数据库查询真实数据"""
    try:
        # 查询实训信息
        training = db.query(db_models.Training).filter(
            db_models.Training.id == training_id
        ).first()

        if not training:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"实训ID {training_id} 不存在"
            )

        # 从数据库查询真实的数据集记录
        db_datasets = db.query(db_models.TrainingDataset).filter(
            db_models.TrainingDataset.training_id == training_id
        ).all()

        datasets = []
        for ds in db_datasets:
            datasets.append({
                "id": ds.id,
                "name": ds.name,
                "path": ds.file_url,
                "relative_path": ds.relative_path,
                "size": ds.file_size or 0,
                "type": ds.file_type,
                "description": ds.description,
                "access_path": ds.access_path,
                "access_path_in_env": ds.access_path_in_env,
                "created_at": ds.created_at.isoformat() if ds.created_at else None
            })

        return {
            "code": "0000",
            "message": "获取数据集列表成功",
            "data": {
                "training_id": training_id,
                "datasets": datasets,
                "total": len(datasets)
            }
        }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训数据集失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据集失败: {str(e)}"
        )

# ==================== 代理路由 ====================

@router.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], include_in_schema=False)
async def proxy_environment(request: Request, path: str, db: Session = Depends(get_db)):
    """
    代理Superset和其他实训环境的API请求到相应的容器
    处理来自iframe的所有请求
    """
    try:
        # 从请求URL中获取training_id和user_id
        training_id = request.query_params.get("training_id")
        user_id = request.query_params.get("user_id")
        referer = request.headers.get("referer", "")
        
        logger.info(f"[代理路由] 处理代理请求: path={path}, training_id={training_id}, user_id={user_id}")
        
        # 如果没有参数，从referer中提取
        if not training_id or not user_id:
            import re
            training_match = re.search(r'training_id=(\d+)', referer)
            user_match = re.search(r'user_id=(\d+)', referer)
            if training_match:
                training_id = training_match.group(1)
            if user_match:
                user_id = user_match.group(1)
        
        if not training_id or not user_id:
            logger.warning(f"[代理路由] ⚠️ 缺少training_id或user_id")
            return JSONResponse(
                status_code=400,
                content={"detail": "缺少training_id或user_id参数"}
            )
        
        # 获取容器信息
        status_info = container_manager.get_container_status_by_training(int(training_id), int(user_id), db)
        if status_info["status"] != "running":
            logger.warning(f"[代理路由] ⚠️ 容器未运行: {status_info['status']}")
            return JSONResponse(
                status_code=503,
                content={"detail": f"容器未运行: {status_info['status']}"}
            )
        
        # 获取容器端口
        port = status_info.get("host_port")
        if not port:
            logger.warning(f"[代理路由] ⚠️ 无法获取容器端口")
            return JSONResponse(
                status_code=500,
                content={"detail": "无法获取容器端口"}
            )
        
        # 构建目标URL
        target_url = f"http://localhost:{port}/{path}"
        if request.url.query:
            # 移除training_id和user_id参数
            query_params = dict(request.query_params)
            query_params.pop("training_id", None)
            query_params.pop("user_id", None)
            if query_params:
                from urllib.parse import urlencode
                target_url += f"?{urlencode(query_params)}"
        
        logger.info(f"[代理路由] 转发请求到: {target_url}")
        
        # 获取请求体
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # 转发请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = dict(request.headers)
            headers.pop("host", None)
            headers.pop("connection", None)
            
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                follow_redirects=False
            )
            
            # 返回响应
            return StreamingResponse(
                iter([response.content]),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[代理路由] ❌ 代理请求失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"代理请求失败: {str(e)}"}
        )
