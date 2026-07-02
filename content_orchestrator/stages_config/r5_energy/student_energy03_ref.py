def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def identify_saving_opportunities(history, horizon_days):
    """节能识别。"""
    if not isinstance(history, list): raise ValueError("history must be a list")
    horizon=max(1,int(_num(horizon_days,1)))
    vals=[_num(r.get("value"), None) for r in history if isinstance(r,dict)]
    vals=[v for v in vals if v is not None and v>=0]
    if not vals: return {"baseline":0.0,"trend":0.0,"forecast":0.0,"confidence":"low"}
    baseline=sum(vals[-3:])/min(3,len(vals)); trend=0.0 if len(vals)<2 else (vals[-1]-vals[0])/(len(vals)-1); forecast=max(0,baseline+trend*horizon); conf="high" if len(vals)>=6 else "medium" if len(vals)>=3 else "low"
    return {"baseline":round(baseline,2),"trend":round(trend,2),"forecast":round(forecast,2),"confidence":conf}
