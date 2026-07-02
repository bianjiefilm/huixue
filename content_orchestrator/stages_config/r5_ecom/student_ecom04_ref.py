def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def recommend_products(user_profile, product_catalog, interactions):
    """生成商品推荐列表。"""
    if not isinstance(user_profile, dict) or not isinstance(product_catalog, list) or not isinstance(interactions, list): raise ValueError("invalid inputs")
    prefs=set(user_profile.get("preferred_categories") or []); budget=_num(user_profile.get("budget"),10**9); seen={str(x.get("sku")) for x in interactions if isinstance(x,dict) and x.get("event") in {"buy","cart"}}
    out=[]
    for p in product_catalog:
        if not isinstance(p,dict) or not p.get("sku"): continue
        sku=str(p["sku"]); price=_num(p.get("price")); rating=_num(p.get("rating")); margin=_num(p.get("margin")); cat=p.get("category")
        if sku in seen or price>budget: continue
        score=rating*20 + margin*30 + (25 if cat in prefs else 0) + max(0, (budget-price)/max(budget,1))*10
        out.append({"sku":sku,"recommend_score":round(score,2),"category":cat,"reason":"偏好匹配" if cat in prefs else "综合排序"})
    return sorted(out,key=lambda r:(-r["recommend_score"],r["sku"]))[:5]
