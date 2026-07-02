-- ============================================================
-- MJ8: 无监督学习: 降维
-- practice_id=7, order_in_practice=8
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$无监督学习: 降维$v$,
    'PRACTICE',
    8,
    $v$intermediate$v$,
    $v$## PCA 主成分分析

## 8.1 原理

PCA 通过正交变换将高维数据投影到低维,同时最大化保留方差:

```python
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 1. 先用 PCA 看方差解释率
pca_full = PCA()
pca_full.fit(X_scaled)
cumvar = pca_full.explained_variance_ratio_.cumsum()

plt.figure(figsize=(8, 4))
plt.plot(range(1, len(cumvar)+1), cumvar, 'bo-')
plt.axhline(y=0.95, color='r', linestyle='--', label='95% variance')
plt.xlabel('Number of Components')
plt.ylabel('Cumulative Explained Variance')
plt.title('PCA Cumulative Explained Variance')
plt.legend()
plt.show()

# 2. 选择保留 95% 方差的维度
n_components = (cumvar < 0.95).sum() + 1
pca = PCA(n_components=n_components)
X_pca = pca.fit_transform(X_scaled)
print(f"保留 {n_components} 个主成分, 解释方差: {cumvar[n_components-1]:.4f}")
```


## t-SNE 可视化

## 8.2 t-SNE

t-SNE 通过保持局部邻域关系在高维空间到2D/3D的映射,适合可视化:

```python
from sklearn.manifold import TSNE

tsne = TSNE(n_components=2, perplexity=30, random_state=42, n_iter=1000)
X_tsne = tsne.fit_transform(X_scaled)

plt.figure(figsize=(10, 8))
plt.scatter(X_tsne[:, 0], X_tsne[:, 1], c=y, cmap='viridis', alpha=0.6)
plt.colorbar(label='Label')
plt.title('t-SNE Visualization')
plt.xlabel('t-SNE 1')
plt.ylabel('t-SNE 2')
plt.show()
```

## 8.3 降维方法对比

| 方法 | 降维目标 | 计算复杂度 | 可逆性 |
|------|---------|-----------|--------|
| PCA | 最大方差保留 | O(n·d²) | 可逆 |
| LDA | 类别可分性 | O(n·d·k) | 可逆 |
| t-SNE | 局部邻域保持 | O(n²) | 不可逆 |
| UMAP | 全局+局部保持 | O(n log n) | 不可逆 |
$v$,
    $v${"questions": [{"id": "q8-1", "type": "concept", "difficulty": "easy", "question": "MJ8 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q8-2", "type": "concept", "difficulty": "easy", "question": "MJ8 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q8-3", "type": "calculation", "difficulty": "medium", "question": "MJ8 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q8-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ8 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 8;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$PCA拟合$v$, $v$返回components和variance$v$, false, $v$PCA拟合$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$PCA投影$v$, $v$返回降维后矩阵$v$, false, $v$PCA投影$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$方差解释率$v$, $v$总和=1.0$v$, false, $v$解释方差$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$从PCA重建$v$, $v$返回重建矩阵$v$, true, $v$重建$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ8';
END $$;

COMMIT;
