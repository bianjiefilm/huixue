def _num(v, default=0.0):
    if isinstance(v, bool): return default
    try: return float(v)
    except (TypeError, ValueError): return default


def analyze_product_sales(orders):
    """分析商品销售表现。"""
    if not isinstance(orders, list): raise ValueError("orders must be a list")
    buckets = {}
    for row in orders:
        if not isinstance(row, dict) or not row.get("sku"): continue
        qty = _num(row.get("quantity"), None); price = _num(row.get("unit_price"), None)
        refund = bool(row.get("is_refund", False))
        if qty is None or price is None or qty <= 0 or price < 0: continue
        b = buckets.setdefault(str(row["sku"]), {"units":0,"revenue":0.0,"orders":0,"refunds":0})
        b["units"] += qty; b["revenue"] += qty * price; b["orders"] += 1; b["refunds"] += 1 if refund else 0
    out=[]
    for sku,b in buckets.items():
        avg = b["revenue"] / b["units"] if b["units"] else 0
        rate = b["refunds"] / b["orders"] if b["orders"] else 0
        band = "hot" if b["revenue"] >= 10000 else "normal" if b["revenue"] >= 3000 else "cold"
        out.append({"sku":sku,"units":int(b["units"]),"revenue":round(b["revenue"],2),"avg_price":round(avg,2),"refund_rate":round(rate,4),"sales_band":band})
    return sorted(out, key=lambda r:(-r["revenue"], r["sku"]))
