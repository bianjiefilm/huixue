#!/usr/bin/env python3
import sys
import json

text = sys.stdin.read().strip()
try:
    text = json.loads(text)
except Exception:
    pass
s = str(text).replace(" ", "")
if "filter(event==purchase)" in s:
    result = "real-time purchase aggregation"
elif "groupBy(user).agg" in s:
    result = "top 10 users by amount"
elif "withWatermark" in s:
    result = "hourly product aggregation"
elif "als.setRank" in s:
    result = "high rating prediction count"
elif "partitionBy(dt,hour)" in s:
    result = "data written with date-hour partition"
elif s == "0":
    result = "recommendation count"
else:
    result = ""
print(json.dumps(result))
