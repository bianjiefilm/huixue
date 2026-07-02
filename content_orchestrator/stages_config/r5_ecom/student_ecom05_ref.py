def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def clean_order_events(events):
    if not isinstance(events, list): raise ValueError("events must be a list")
    out=[]
    for e in events:
        if not isinstance(e,dict) or not e.get("sku"): continue
        qty=max(0.0,_num(e.get("quantity"))); price=max(0.0,_num(e.get("unit_price")))
        if qty<=0: continue
        out.append({"sku":str(e["sku"]),"customer_id":str(e.get("customer_id","unknown")),"quantity":qty,"unit_price":price,"category":str(e.get("category","unknown")),"is_refund":bool(e.get("is_refund",False))})
    return sorted(out,key=lambda r:(r["sku"],r["customer_id"]))

def summarize_product_performance(events):
    buckets={}
    for e in events:
        if isinstance(e,dict) and e.get("sku"):
            b=buckets.setdefault(e["sku"],{"units":0.0,"revenue":0.0,"refunds":0,"orders":0,"category":e.get("category","unknown")})
            b["units"]+=_num(e.get("quantity")); b["revenue"]+=_num(e.get("quantity"))*_num(e.get("unit_price")); b["refunds"]+=1 if e.get("is_refund") else 0; b["orders"]+=1
    out=[]
    for sku,b in buckets.items():
        out.append({"sku":sku,"category":b["category"],"units":int(b["units"]),"revenue":round(b["revenue"],2),"refund_rate":round(b["refunds"]/b["orders"],4)})
    return sorted(out,key=lambda r:(-r["revenue"],r["sku"]))

def forecast_replenishment(performance, inventory):
    inv={str(i.get("sku")):i for i in inventory if isinstance(i,dict) and i.get("sku")}
    out=[]
    for p in performance:
        sku=p["sku"]; stock=_num(inv.get(sku,{}).get("stock")); safety=_num(inv.get(sku,{}).get("safety_stock")); need=max(0,p["units"]*2+safety-stock); level="urgent" if need>=20 else "watch" if need>0 else "ok"
        out.append({"sku":sku,"reorder_qty":int(round(need)),"priority":level})
    return sorted(out,key=lambda r:({"urgent":0,"watch":1,"ok":2}[r["priority"]],-r["reorder_qty"],r["sku"]))

def build_product_recommendations(user_profile, products, events):
    prefs=set(user_profile.get("preferred_categories") or []); bought={e.get("sku") for e in events if isinstance(e,dict) and e.get("customer_id")==user_profile.get("customer_id")}
    out=[]
    for p in products:
        if not isinstance(p,dict) or not p.get("sku") or p.get("sku") in bought: continue
        score=_num(p.get("rating"))*20 + (30 if p.get("category") in prefs else 0) + _num(p.get("margin"))*20
        out.append({"sku":str(p["sku"]),"score":round(score,2),"reason":"偏好匹配" if p.get("category") in prefs else "综合排序"})
    return sorted(out,key=lambda r:(-r["score"],r["sku"]))[:5]

def summarize_sales_operation(performance, replenishment, recommendations):
    revenue=sum(_num(p.get("revenue")) for p in performance); urgent=sum(1 for r in replenishment if r.get("priority")=="urgent"); hot=sum(1 for p in performance if _num(p.get("revenue"))>=10000); status="urgent" if urgent else "growth" if hot else "stable"
    return {"product_count":len(performance),"total_revenue":round(revenue,2),"urgent_replenishments":urgent,"recommendation_count":len(recommendations),"operation_status":status}
