def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default

def forecast_inventory_needs(inventory_rows, sales_history):
    """预测库存补货需求。"""
    if not isinstance(inventory_rows, list) or not isinstance(sales_history, list): raise ValueError("invalid inputs")
    sold={}
    for row in sales_history:
        if isinstance(row, dict) and row.get("sku"):
            sold[str(row["sku"])] = sold.get(str(row["sku"]),0.0) + max(0.0,_num(row.get("sold_qty")))
    days=max(1, len({r.get("date") for r in sales_history if isinstance(r,dict) and r.get("date")}))
    out=[]
    for row in inventory_rows:
        if not isinstance(row, dict) or not row.get("sku"): continue
        sku=str(row["sku"]); stock=max(0.0,_num(row.get("stock"))); lead=max(1.0,_num(row.get("lead_days"),1)); safety=max(0.0,_num(row.get("safety_stock")))
        velocity=sold.get(sku,0.0)/days; target=velocity*lead+safety; reorder=max(0.0,target-stock)
        priority="urgent" if stock < safety or (velocity > 0 and reorder >= velocity*2.5) else "watch" if reorder > 0 else "ok"
        out.append({"sku":sku,"daily_velocity":round(velocity,2),"days_of_stock":round(999.0 if velocity==0 else stock/velocity,2),"reorder_qty":int(round(reorder)),"priority":priority})
    return sorted(out,key=lambda r:({"urgent":0,"watch":1,"ok":2}[r["priority"]],-r["reorder_qty"],r["sku"]))
