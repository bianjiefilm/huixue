def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def clean_operation_rows(rows):
    if not isinstance(rows,list): raise ValueError("rows must be a list")
    out=[]
    for r in rows:
        if not isinstance(r,dict) or not r.get("unit_id"): continue
        out.append({"unit_id":str(r["unit_id"]),"metric":max(0,_num(r.get("metric"))),"cost":max(0,_num(r.get("cost"))),"volume":max(0,_num(r.get("volume"))),"period":str(r.get("period","unknown"))})
    return sorted(out,key=lambda r:(r["unit_id"],r["period"]))

def summarize_unit_performance(rows):
    buckets={}
    for r in rows:
        if isinstance(r,dict) and r.get("unit_id"):
            b=buckets.setdefault(r["unit_id"],{"metric":0.0,"cost":0.0,"volume":0.0,"n":0}); b["metric"]+=_num(r.get("metric")); b["cost"]+=_num(r.get("cost")); b["volume"]+=_num(r.get("volume")); b["n"]+=1
    out=[]
    for uid,b in buckets.items():
        net=b["metric"]-b["cost"]; eff=0 if b["volume"]==0 else b["metric"]/b["volume"]; status="excellent" if net>=10000 else "watch" if net>=0 else "risk"
        out.append({"unit_id":uid,"net_value":round(net,2),"efficiency":round(eff,4),"status":status})
    return sorted(out,key=lambda r:(-r["net_value"],r["unit_id"]))

def forecast_operation_metric(history, horizon):
    vals=[_num(x.get("metric"),None) for x in history if isinstance(x,dict)]; vals=[v for v in vals if v is not None and v>=0]; h=max(1,int(_num(horizon,1)))
    if not vals: return {"baseline":0.0,"forecast":0.0,"trend":0.0}
    baseline=sum(vals[-3:])/min(3,len(vals)); trend=0 if len(vals)<2 else (vals[-1]-vals[0])/(len(vals)-1)
    return {"baseline":round(baseline,2),"forecast":round(max(0,baseline+trend*h),2),"trend":round(trend,2)}

def recommend_operation_actions(performance, forecasts):
    fmap={f.get("unit_id"):f for f in forecasts if isinstance(f,dict)}; out=[]
    for p in performance:
        if not isinstance(p,dict) or not p.get("unit_id"): continue
        fc=_num(fmap.get(p["unit_id"],{}).get("forecast"),0); status=p.get("status")
        if status=="risk": action="立即诊断"
        elif fc>_num(p.get("net_value"))*1.2: action="加大投入"
        else: action="常规优化"
        out.append({"unit_id":p["unit_id"],"action":action,"priority":3 if action=="立即诊断" else 2 if action=="加大投入" else 1})
    return sorted(out,key=lambda r:(-r["priority"],r["unit_id"]))

def summarize_operation_report(performance, actions):
    risk=sum(1 for p in performance if isinstance(p,dict) and p.get("status")=="risk"); urgent=sum(1 for a in actions if isinstance(a,dict) and a.get("priority")==3); total=sum(_num(p.get("net_value")) for p in performance if isinstance(p,dict)); status="urgent" if urgent else "watch" if risk else "stable"
    return {"unit_count":len(performance),"total_net_value":round(total,2),"risk_units":risk,"urgent_actions":urgent,"operation_status":status}
