def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def clean_extension_events(events):
    """清洗扩展综合关事件。"""
    if not isinstance(events, list): raise ValueError("events must be a list")
    out=[]
    for row in events:
        if not isinstance(row, dict) or not row.get("entity_id"): continue
        risk=max(0.0,min(1.0,_num(row.get("risk_score"))))
        value=max(0.0,_num(row.get("business_value")))
        cost=max(0.0,_num(row.get("action_cost")))
        impact=max(0.0,_num(row.get("impact"), value-cost))
        out.append({"entity_id":str(row["entity_id"]),"risk_score":risk,"business_value":value,"action_cost":cost,"impact":impact,"category":str(row.get("category","general"))})
    return sorted(out,key=lambda r:(-r["risk_score"],r["entity_id"]))

def rank_extension_actions(events):
    """按风险、收益和成本排序行动。"""
    if not isinstance(events, list): raise ValueError("events must be a list")
    out=[]
    for row in events:
        if not isinstance(row, dict) or not row.get("entity_id"): continue
        risk=_num(row.get("risk_score")); value=_num(row.get("business_value")); cost=_num(row.get("action_cost")); impact=_num(row.get("impact"), value-cost)
        priority_score=risk*60 + max(0, impact-cost)*0.01 + (15 if risk>=0.8 else 0)
        action="immediate" if priority_score>=70 else "scheduled" if priority_score>=35 else "monitor"
        out.append({"entity_id":str(row["entity_id"]),"priority_score":round(priority_score,2),"action":action,"net_gain":round(impact-cost,2)})
    return sorted(out,key=lambda r:(-r["priority_score"],r["entity_id"]))

def summarize_extension_report(events, actions):
    """汇总扩展综合关复盘报告。"""
    total_value=sum(_num(e.get("business_value")) for e in events if isinstance(e,dict))
    immediate=sum(1 for a in actions if isinstance(a,dict) and a.get("action")=="immediate")
    scheduled=sum(1 for a in actions if isinstance(a,dict) and a.get("action")=="scheduled")
    net_gain=sum(_num(a.get("net_gain")) for a in actions if isinstance(a,dict))
    status="urgent" if immediate else "watch" if scheduled else "stable"
    return {"event_count":len(events),"total_value":round(total_value,2),"immediate_actions":immediate,"scheduled_actions":scheduled,"expected_net_gain":round(net_gain,2),"status":status}
