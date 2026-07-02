def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def analyze_store_performance(rows):
    """门店分析。"""
    if not isinstance(rows, list): raise ValueError("rows must be a list")
    buckets={}
    for r in rows:
        if not isinstance(r,dict) or not r.get("unit_id"): continue
        revenue=_num(r.get("revenue")); cost=_num(r.get("cost")); visitors=_num(r.get("visitors"), _num(r.get("output"), 0)); area=_num(r.get("area"),1) or 1
        b=buckets.setdefault(str(r["unit_id"]),{"revenue":0.0,"cost":0.0,"visitors":0.0,"area":area,"days":0})
        b["revenue"]+=max(0,revenue); b["cost"]+=max(0,cost); b["visitors"]+=max(0,visitors); b["days"]+=1; b["area"]=area
    out=[]
    for uid,b in buckets.items():
        profit=b["revenue"]-b["cost"]; efficiency=b["revenue"]/b["area"] if b["area"] else 0
        level="excellent" if profit>=10000 else "watch" if profit>=0 else "loss"
        out.append({"unit_id":uid,"total_revenue":round(b["revenue"],2),"profit":round(profit,2),"avg_visitors":round(b["visitors"]/b["days"],2),"efficiency":round(efficiency,2),"level":level})
    return sorted(out,key=lambda x:(-x["profit"],x["unit_id"]))
