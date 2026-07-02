def plan_dynamic_page_collection(username, password, login_url):
    """Build a dynamic-page collection plan."""
    if not isinstance(username, str) or not isinstance(password, str) or not isinstance(login_url, str):
        raise TypeError("username, password and login_url must be strings")
    if not username.strip() or not password.strip():
        raise ValueError("username and password are required")
    if not (login_url.startswith("http://") or login_url.startswith("https://")):
        raise ValueError("login_url must start with http:// or https://")

    return {
        "login_url": login_url,
        "credentials": {
            "username": username,
            "password": password,
        },
        "browser": {
            "engine": "chromium",
            "arguments": ["--headless=new", "--disable-gpu", "--no-sandbox"],
        },
        "wait_strategy": {
            "type": "explicit",
            "timeout_seconds": 10,
            "poll_seconds": 0.5,
        },
        "locators": [
            {"name": "username", "by": "css", "value": "input[name='username']"},
            {"name": "password", "by": "xpath", "value": "//input[@type='password']"},
            {"name": "submit", "by": "css", "value": "button[type='submit']"},
        ],
        "cleanup": ["driver.quit"],
    }
