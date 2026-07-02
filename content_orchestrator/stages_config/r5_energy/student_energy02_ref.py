def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def detect_energy_anomalies(items):
    """异常检测。"""
    if not isinstance(items, list): raise ValueError("items must be a list")
    clean=[]
    for r in items:
        if not isinstance(r,dict) or not r.get("item_id"): continue
        margin=_num(r.get("margin")); affinity=_num(r.get("affinity")); velocity=_num(r.get("velocity")); stock=_num(r.get("stock"),0)
        score=margin*40+affinity*35+velocity*0.2+(10 if stock>0 else -20)
        tag="core" if score>=70 else "addon" if score>=35 else "avoid"
        clean.append({"item_id":str(r["item_id"]),"bundle_score":round(score,2),"tag":tag})
    return sorted(clean,key=lambda r:(-r["bundle_score"],r["item_id"]))
