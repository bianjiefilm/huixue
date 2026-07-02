import json
import re


COMBINED_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>[^"]+)" (?P<status>\d{3}) (?P<size>\d+|-)'
)
SYSLOG_RE = re.compile(r"^<(?P<priority>\d+)>(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+) (?P<host>\S+) (?P<message>.*)$")


def parse_log_entry(line):
    """Parse one log line into a structured dictionary."""
    if not isinstance(line, str):
        raise TypeError("line must be a string")
    text = line.strip()
    if not text:
        return {"error": "invalid_log"}
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {"error": "invalid_log"}
        return {"type": "json", "timestamp": data.get("ts"), "level": data.get("level"), "message": data.get("message", "")}
    match = COMBINED_RE.match(text)
    if match:
        size = match.group("size")
        return {
            "type": "access",
            "ip": match.group("ip"),
            "time": match.group("time"),
            "method": match.group("method"),
            "path": match.group("path"),
            "status": int(match.group("status")),
            "size": 0 if size == "-" else int(size),
        }
    match = SYSLOG_RE.match(text)
    if match:
        return {
            "type": "syslog",
            "priority": int(match.group("priority")),
            "timestamp": match.group("timestamp"),
            "host": match.group("host"),
            "message": match.group("message"),
        }
    return {"error": "invalid_log"}


def summarize_log_entries(lines):
    """Summarize status codes and log levels from log lines."""
    if not isinstance(lines, list):
        raise TypeError("lines must be a list")
    status_counts = {}
    level_counts = {}
    invalid = 0
    for line in lines:
        parsed = parse_log_entry(line)
        if "error" in parsed:
            invalid += 1
            continue
        if "status" in parsed:
            key = str(parsed["status"])
            status_counts[key] = status_counts.get(key, 0) + 1
        if parsed.get("level"):
            key = parsed["level"]
            level_counts[key] = level_counts.get(key, 0) + 1
    return {"status_counts": status_counts, "level_counts": level_counts, "invalid": invalid}
