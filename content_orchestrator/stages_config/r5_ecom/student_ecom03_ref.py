def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def build_customer_segments(customers):
    """构建用户画像分群。"""
    if not isinstance(customers, list): raise ValueError("customers must be a list")
    segs={"high_value":[],"potential":[],"new_user":[],"inactive":[]}
    for row in customers:
        if not isinstance(row, dict) or not row.get("customer_id"): continue
        spend=_num(row.get("total_spend")); orders=_num(row.get("orders")); recency=_num(row.get("days_since_last_order"),999)
        if spend>=5000 and orders>=5: seg="high_value"
        elif recency<=30 and spend>=1000: seg="potential"
        elif orders<=1 and recency<=60: seg="new_user"
        else: seg="inactive"
        segs[seg].append({"customer_id":str(row["customer_id"]),"spend":spend,"orders":orders})
    out=[]
    for seg, rows in segs.items():
        if not rows: continue
        out.append({"segment":seg,"customer_count":len(rows),"avg_spend":round(sum(r["spend"] for r in rows)/len(rows),2),"customer_ids":sorted(r["customer_id"] for r in rows)})
    return sorted(out,key=lambda r:(-r["customer_count"],r["segment"]))
