USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Firefox/121.0",
]


def build_anticrawl_request(url, delay=1.0, user_agent_index=0):
    """Build an anti-crawl aware request plan."""
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    if not isinstance(delay, (int, float)):
        raise TypeError("delay must be numeric")
    if not isinstance(user_agent_index, int):
        raise TypeError("user_agent_index must be an integer")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("url must start with http:// or https://")
    if delay < 0.5 or delay > 10:
        raise ValueError("delay must be between 0.5 and 10 seconds")

    user_agent = USER_AGENTS[user_agent_index % len(USER_AGENTS)]
    referer = url.rsplit("/", 1)[0] + "/"
    return {
        "url": url,
        "headers": {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": referer,
            "Connection": "keep-alive",
        },
        "rate_limit": {
            "strategy": "fixed_delay",
            "delay_seconds": float(delay),
        },
        "session": {
            "enabled": True,
            "cookie_policy": "persist_between_requests",
        },
    }
