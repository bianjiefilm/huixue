#!/usr/bin/env python3
"""UAT API batch test — runs inside backend container"""
import urllib.request, json, sys

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0

def login(user, pwd):
    req = urllib.request.Request(BASE + "/api/login",
        json.dumps({"username": user, "password": pwd}).encode(),
        headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return r.get("token", {}).get("access_token", "")

def api(url, token):
    req = urllib.request.Request(BASE + url)
    req.add_header("Authorization", "Bearer " + token)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print("  OK  %s %s" % (name, detail))
    else:
        FAIL += 1
        print("  FAIL %s %s" % (name, detail))

# === A. LOGIN ===
print("=== A. LOGIN ===")
for user, pwd in [("admin", "admin123"), ("teacher1", "teacher123"), ("student1", "student123")]:
    t = login(user, pwd)
    check("A: %s login" % user, bool(t))

admin_token = login("admin", "admin123")
teacher_token = login("teacher1", "teacher123")
student_token = login("student1", "student123")

# === B. CLASSROOM ===
print("\n=== B. CLASSROOM ===")
r = api("/api/v1/classrooms/", admin_token)
d = r.get("data", {})
cl = d.get("total", len(d.get("list", d.get("items", []))))
check("B1: admin classrooms", cl == 15, "count=%d" % cl)

r = api("/api/v1/classrooms/", teacher_token)
d = r.get("data", {})
t_cl = len(d.get("list", d.get("items", [])))
check("B2: teacher1 classrooms", t_cl >= 5, "count=%d" % t_cl)

r = api("/api/v1/classrooms/", student_token)
d = r.get("data", {})
s_cl = d.get("total", len(d.get("list", d.get("items", []))))
check("B3: student1 classrooms", s_cl >= 1, "count=%s" % s_cl)

# === C. BI DATASETS ===
print("\n=== C. BI DATASETS ===")
bi_ok = 0
for tid in [100, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]:
    try:
        r = api("/api/v1/trainings/%d/bi-dataset" % tid, admin_token)
        ds = r.get("data", {}).get("datasets", [])
        rows = sum(x.get("totalRows", 0) for x in ds)
        ok = rows > 0
        if ok:
            bi_ok += 1
        check("C: T%d bi-dataset" % tid, ok, "%dds %drows" % (len(ds), rows))
    except Exception as e:
        check("C: T%d bi-dataset" % tid, False, str(e)[:50])
check("C: total BI trainings", bi_ok == 13, "%d/13" % bi_ok)

# === D. RESOURCES ===
print("\n=== D. RESOURCES ===")
try:
    req = urllib.request.Request(BASE + "/static/resources/课程资源/Python程序设计/视频和课件/视频7.2Python中的面向对象.mp4", method="HEAD")
    resp = urllib.request.urlopen(req, timeout=10)
    check("D1: video MP4", resp.status == 200, "HTTP %d" % resp.status)
except Exception as e:
    check("D1: video MP4", False, str(e)[:50])

try:
    req = urllib.request.Request(BASE + "/static/resources/课程资源/Python程序设计/视频和课件/2.2 变量.pdf", method="HEAD")
    resp = urllib.request.urlopen(req, timeout=10)
    check("D2: PDF file", resp.status == 200, "HTTP %d" % resp.status)
except Exception as e:
    check("D2: PDF file", False, str(e)[:50])

# === E. HANDBOOK PERSONALIZATION ===
print("\n=== E. HANDBOOK ===")
handbook_tests = [
    (100, 100, "A股"),
    (103, 103, "企业用能"),
    (104, 104, "公募基金"),
    (106, 106, "客户流失"),
    (108, 113, "零售"),
    (109, 100, "高校"),
    (112, 100, "风电"),
]
for tid, cid, keyword in handbook_tests:
    try:
        r = api("/api/v1/classrooms/%d/trainings/%d/details?student_id=30" % (cid, tid), admin_token)
        hc = r.get("data", {}).get("handbook_content", "")
        found = keyword in hc
        check("E: T%d handbook '%s'" % (tid, keyword), found, "%d chars" % len(hc))
    except Exception as e:
        check("E: T%d handbook '%s'" % (tid, keyword), False, str(e)[:50])

# === F. SUBMISSION ===
print("\n=== F. SUBMISSION ===")
try:
    req = urllib.request.Request(
        BASE + "/api/v1/classrooms/100/trainings/100/submission",
        json.dumps({"student_id": 30, "completed": False, "data": {"test": True}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + student_token})
    resp = urllib.request.urlopen(req, timeout=10)
    r = json.loads(resp.read())
    check("F1: submit training", r.get("code") == "0000", r.get("message", "")[:40])
except Exception as e:
    check("F1: submit training", False, str(e)[:50])

# === G. ADMIN ===
print("\n=== G. ADMIN ===")
r = api("/api/v1/courses/", admin_token)
d = r.get("data", {})
courses = d.get("total", len(d.get("list", d.get("items", []))))
check("G1: courses", courses == 15, "count=%d" % courses)

r = api("/api/v1/trainings/", admin_token)
d = r.get("data", {})
trainings = d.get("total", len(d.get("list", d.get("items", []))))
check("G2: trainings", trainings == 15, "count=%d" % trainings)

# === SUMMARY ===
print("\n" + "=" * 50)
total = PASS + FAIL
print("UAT RESULT: %d/%d PASS (%d FAIL)" % (PASS, total, FAIL))
print("=" * 50)
sys.exit(0 if FAIL == 0 else 1)
