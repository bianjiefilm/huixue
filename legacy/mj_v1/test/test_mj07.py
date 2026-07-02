import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj07 import euclidean_distance, kmeans_init_centroids, assign_clusters, compute_inertia, silhouette_score
import numpy as np

def test_euclidean():
    a = np.array([0, 0])
    b = np.array([3, 4])
    d = euclidean_distance(a, b)
    assert d == 5.0, f"距离应为5，实际 {d}"

def test_kmeans_init():
    X = np.array([[0, 0], [1, 1], [10, 10], [11, 11]])
    k = 2
    result = kmeans_init_centroids(X, k)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (k, 2)

def test_assign_clusters():
    X = np.array([[0, 0], [10, 10]])
    centroids = np.array([[0, 0], [10, 10]])
    labels = assign_clusters(X, centroids)
    assert labels is not None, "pass-only 不得分"
    assert labels.shape == (2,)
    assert labels[0] != labels[1]

def test_inertia():
    X = np.array([[0, 0], [1, 1], [10, 10], [11, 11]])
    labels = np.array([0, 0, 1, 1])
    centroids = np.array([[0.5, 0.5], [10.5, 10.5]])
    result = compute_inertia(X, labels, centroids)
    assert result is not None, "pass-only 不得分"
    assert result >= 0

def test_silhouette():
    X = np.array([[0, 0], [0.1, 0.1], [10, 10], [10.1, 10.1]])
    labels = np.array([0, 0, 1, 1])
    result = silhouette_score(X, labels)
    assert result is not None, "pass-only 不得分"
    assert -1 <= result <= 1
