"""综合项目: 客户流失预测全流程 - 学生作答文件"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# 模拟客户流失数据
CUSTOMERS_DATA = {
    'customer_id': list(range(1, 101)),
    'tenure': [5, 10, 2, 20, 15, 3, 8, 12, 6, 25] * 10,
    'monthly_charges': [30.0 + i * 2 for i in range(100)],
    'total_charges': [150.0 + i * 15 for i in range(100)],
    'contract_type': ['Month-to-month'] * 30 + ['One year'] * 30 + ['Two year'] * 40,
    'tech_support': ['No'] * 40 + ['Yes'] * 60,
    'churn': [0, 1, 1, 0, 0, 1, 1, 0, 0, 1][:10] * 10,
}


def load_churn_data() -> pd.DataFrame:
    """加载客户流失数据集"""
    return pd.DataFrame(CUSTOMERS_DATA)


def preprocess_and_split(df: pd.DataFrame, target_col: str = 'churn',
                        test_size: float = 0.2, random_state: int = 42) -> Tuple:
    """
    预处理: Label编码 + 训练/测试集划分 + 标准化。

    Returns:
        (X_train_scaled, X_test_scaled, y_train, y_test, scaler)
    """
    pass


def train_and_compare_models(X_train, y_train) -> Dict[str, float]:
    """
    训练多个模型(LogisticRegression, RandomForest, GradientBoosting),
    返回各模型训练集准确率字典。

    Returns:
        dict: {model_name: accuracy}
    """
    pass


def evaluate_model(model, X_test, y_test) -> Dict:
    """
    在测试集上评估模型: accuracy, precision, recall, f1, roc_auc。

    Returns:
        dict: 各指标值
    """
    pass


def get_top_features(model, feature_names: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
    """
    提取模型特征重要性,返回 top_k 最重要的特征。

    Returns:
        List[(feature_name, importance), ...] 按重要性降序
    """
    pass
