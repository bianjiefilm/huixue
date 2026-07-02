-- ============================================================
-- MJ7: 无监督学习: 聚类
-- practice_id=7, order_in_practice=7
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$无监督学习: 聚类$v$,
    'PRACTICE',
    7,
    $v$intermediate$v$,
    $v$## K-Means 聚类

## 7.1 算法原理

1. 随机选择 K 个中心点
2. 将每个点分配给最近的中心
3. 重新计算各簇中心
4. 重复2-3直至收敛

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# elbow 法: 绘制不同 K 值的 inertia(SSE)
inertias = []
K_range = range(2, 11)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)

# 确定 K 后
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
labels = kmeans.fit_predict(X_scaled)
centroids = kmeans.cluster_centers_
```


## DBSCAN

## 7.2 DBSCAN 密度聚类

基于密度的聚类,可发现任意形状簇并自动识别噪声点:

```python
from sklearn.cluster import DBSCAN

dbscan = DBSCAN(eps=0.5, min_samples=5)
labels = dbscan.fit_predict(X_scaled)
# labels == -1 表示噪声点
n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = list(labels).count(-1)
print(f"聚类数: {n_clusters}, 噪声点: {n_noise}")
```


## 层次聚类与评估

## 7.3 层次聚类

```python
from sklearn.cluster import AgglomerativeClustering
import scipy.cluster.hierarchy as sch

# 树状图
dendrogram = sch.dendrogram(sch.linkage(X_scaled, method='ward'))
plt.title('Dendrogram')
plt.xlabel('Samples')
plt.ylabel('Distance')
plt.show()

# 层次聚类
hc = AgglomerativeClustering(n_clusters=3, linkage='ward')
labels = hc.fit_predict(X_scaled)
```

## 7.4 轮廓系数

$s = \\frac{b - a}{max(a, b)}$, 其中 a=簇内距离,b=最近簇距离,s∈[-1,1]

```python
from sklearn.metrics import silhouette_score

sil_score = silhouette_score(X_scaled, labels)
print(f"轮廓系数: {sil_score:.4f}")  # 越接近1越好
```
$v$,
    $v${"questions": [{"id": "q7-1", "type": "concept", "difficulty": "easy", "question": "MJ7 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q7-2", "type": "concept", "difficulty": "easy", "question": "MJ7 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q7-3", "type": "calculation", "difficulty": "medium", "question": "MJ7 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q7-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ7 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 7;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$euclidean(0,0)-(3,4)$v$, $v$5.0$v$, false, $v$欧氏距离$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$K-Means++初始化$v$, $v$返回k个初始中心$v$, false, $v$初始化中心$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$分配簇$v$, $v$返回簇标签$v$, false, $v$簇分配$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$轮廓系数$v$, $v$返回-1~1之间值$v$, true, $v$轮廓系数$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ7';
END $$;

COMMIT;
