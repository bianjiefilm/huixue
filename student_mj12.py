"""综合项目: 客户流失预测全流程 - 学生作答文件

不嵌完整数据 (与 v1 灾难形成对照)。
学生需自己构造满足 schema 的 100 行不平衡数据。
仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
"""
from typing import Dict, List, Tuple


def load_churn_data() -> Dict[str, list]:
    """
    构造或加载客户流失数据集。

    Returns:
        dict 含 5 个键, 每个键对应一个长度 100 的 list:
          - 'tenure' (int 1..72)
          - 'monthly_charges' (float 30.0..150.0)
          - 'contract_type' (str ∈ {Month-to-month, One year, Two year})
          - 'tech_support' (str ∈ {Yes, No})
          - 'churn' (int 0 或 1, 80 行 churn=0 + 20 行 churn=1)
    """
    pass


def preprocess_and_split(data: dict, target_col: str = "churn",
                         test_size: float = 0.2,
                         random_state: int = 42) -> Tuple[list, list, list, list]:
    """
    对客户流失数据做编码 + 标准化 + 分层划分。

    步骤约定 (复用 MJ03):
      1. contract_type 标签编码 {Month-to-month:0, One year:1, Two year:2}
      2. tech_support 标签编码 {No:0, Yes:1}
      3. 数值特征 (tenure / monthly_charges) z-score 标准化 (用 train 统计量, test 只 transform)
      4. 分层 train_test_split, 保持 churn 比例

    Returns:
        (X_train, X_test, y_train, y_test):
          X_train / X_test: list[list[float]] 行=样本 列=已编码标准化特征
          y_train / y_test: list[int] 0/1 标签

    Raises:
        ValueError: target_col 不在 data 中 / data 字段缺失。
        TypeError: data 不是 dict。
    """
    pass


def train_and_compare_models(X_train: list, y_train: list,
                              X_test: list, y_test: list) -> Dict[str, float]:
    """
    训练至少 3 种差异化分类算法 (LogisticRegression / DecisionTree / RandomForest), 返回测试集 accuracy。

    Returns:
        dict {模型名: accuracy} 至少含 3 个键, 每值 ∈ [0, 1]。
        模型构造时设 random_state=42 保证可复现。

    Raises:
        ValueError: 输入空 / 长度不一致。
        TypeError: 输入类型错误。
    """
    pass


def evaluate_model(y_true: list, y_pred: list) -> Dict[str, float]:
    """
    根据真实/预测标签计算 5 个分类指标。

    Returns:
        dict 含 5 个键 (都是 float, 除零情况返回 0.0):
          - 'accuracy'
          - 'precision'
          - 'recall'
          - 'f1'
          - 'specificity' (TN/(TN+FP), 派生自 MJ04 confusion matrix)

    Raises:
        ValueError: 输入空 / 长度不一致 / 含非 0/1 标签。
        TypeError: 输入类型错误。
    """
    pass
