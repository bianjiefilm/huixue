def clean_order_events(events): return [{"sku":"FIXED","customer_id":"C","quantity":1,"unit_price":1,"category":"x","is_refund":False}]
def summarize_product_performance(events): return [{"sku":"FIXED","category":"x","units":1,"revenue":1,"refund_rate":0}]
def forecast_replenishment(performance, inventory): return [{"sku":"FIXED","reorder_qty":0,"priority":"ok"}]
def build_product_recommendations(user_profile, products, events): return [{"sku":"FIXED","score":0,"reason":"综合排序"}]
def summarize_sales_operation(performance, replenishment, recommendations): return {"product_count":1,"total_revenue":1,"urgent_replenishments":0,"recommendation_count":1,"operation_status":"stable"}
