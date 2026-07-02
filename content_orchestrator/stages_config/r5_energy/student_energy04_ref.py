def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def optimize_energy_cost(traffic_rows):
    """成本优化。"""
    if not isinstance(traffic_rows, list): raise ValueError("traffic_rows must be a list")
    buckets={}
    for r in traffic_rows:
        if not isinstance(r,dict) or not r.get("period"): continue
        visitors=max(0,_num(r.get("visitors"))); buyers=max(0,_num(r.get("buyers"))); dwell=max(0,_num(r.get("dwell_minutes")))
        b=buckets.setdefault(str(r["period"]),{"visitors":0.0,"buyers":0.0,"dwell":0.0,"n":0}); b["visitors"]+=visitors; b["buyers"]+=buyers; b["dwell"]+=dwell; b["n"]+=1
    out=[]
    for period,b in buckets.items():
        conv=0.0 if b["visitors"]==0 else b["buyers"]/b["visitors"]; avg_dwell=b["dwell"]/b["n"] if b["n"] else 0
        label="peak" if b["visitors"]>=500 else "normal" if b["visitors"]>=100 else "low"
        out.append({"period":period,"visitors":int(b["visitors"]),"conversion_rate":round(conv,4),"avg_dwell":round(avg_dwell,2),"traffic_level":label})
    return sorted(out,key=lambda r:(-r["visitors"],r["period"]))
