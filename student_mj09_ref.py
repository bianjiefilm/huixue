"""MJ09 ref 实现 — 关联规则挖掘 4 函数."""
from typing import Set


def compute_support(transactions, itemset):
    if not isinstance(transactions, list):
        raise TypeError("transactions must be list")
    if not transactions:
        raise ValueError("transactions empty")
    if not isinstance(itemset, (set, list, tuple, frozenset)):
        raise TypeError("itemset must be iterable collection")
    items = frozenset(itemset)
    if not items:
        raise ValueError("itemset empty")
    cnt = sum(1 for t in transactions if items.issubset(set(t) if not isinstance(t, (set, frozenset)) else t))
    return cnt / len(transactions)


def compute_confidence(transactions, antecedent, consequent):
    if not isinstance(transactions, list):
        raise TypeError("transactions must be list")
    if not transactions:
        raise ValueError("transactions empty")
    ante = frozenset(antecedent) if isinstance(antecedent, (set, list, tuple, frozenset)) else None
    cons = frozenset(consequent) if isinstance(consequent, (set, list, tuple, frozenset)) else None
    if ante is None or cons is None:
        raise TypeError("antecedent/consequent must be iterable")
    if not ante:
        raise ValueError("antecedent empty")
    sup_ante = compute_support(transactions, ante)
    if sup_ante == 0:
        raise ValueError("antecedent has zero support")
    sup_union = compute_support(transactions, ante | cons)
    return sup_union / sup_ante


def compute_lift(transactions, antecedent, consequent):
    if not isinstance(transactions, list):
        raise TypeError("transactions must be list")
    if not transactions:
        raise ValueError("transactions empty")
    ante = frozenset(antecedent) if isinstance(antecedent, (set, list, tuple, frozenset)) else None
    cons = frozenset(consequent) if isinstance(consequent, (set, list, tuple, frozenset)) else None
    if ante is None or cons is None:
        raise TypeError()
    sup_ante = compute_support(transactions, ante)
    sup_cons = compute_support(transactions, cons)
    if sup_ante == 0 or sup_cons == 0:
        raise ValueError("antecedent/consequent has zero support")
    sup_union = compute_support(transactions, ante | cons)
    return sup_union / (sup_ante * sup_cons)


def find_frequent_itemsets(transactions, min_support):
    if not isinstance(transactions, list):
        raise TypeError("transactions must be list")
    if not transactions:
        raise ValueError("transactions empty")
    if not isinstance(min_support, (int, float)) or isinstance(min_support, bool):
        raise TypeError("min_support must be number")
    if min_support < 0 or min_support > 1:
        raise ValueError("min_support out of [0,1]")

    n = len(transactions)
    items = set()
    for t in transactions:
        items.update(t)

    result = set()

    # 1-itemsets
    L_prev = []
    for item in items:
        sup = sum(1 for t in transactions if item in t) / n
        if sup >= min_support:
            fs = frozenset({item})
            result.add(fs)
            L_prev.append(fs)

    # K-itemsets via apriori-style join
    k = 2
    while L_prev:
        candidates = set()
        for i, a in enumerate(L_prev):
            for b in L_prev[i+1:]:
                cand = a | b
                if len(cand) == k:
                    candidates.add(cand)
        L_curr = []
        for cand in candidates:
            sup = sum(1 for t in transactions if cand.issubset(set(t) if not isinstance(t, (set, frozenset)) else t)) / n
            if sup >= min_support:
                result.add(cand)
                L_curr.append(cand)
        L_prev = L_curr
        k += 1

    return result
