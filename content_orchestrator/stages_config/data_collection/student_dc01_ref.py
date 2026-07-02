def recommend_collection_tool(scenario):
    """Return the recommended data collection tool for a scenario."""
    if not isinstance(scenario, str):
        raise TypeError("scenario must be a string")

    text = scenario.strip().lower()
    if not text:
        return "manual_review"

    has_js = any(token in text for token in ["javascript", "js", "动态渲染", "spa", "react", "vue"])
    needs_login = any(token in text for token in ["登录", "login", "认证", "cookie"])
    needs_intercept = any(token in text for token in ["拦截", "内部 api", "network", "接口"])
    large_crawl = any(token in text for token in ["1000+ 页", "1000+页", "大量页面", "请求调度", "自动去重"])
    concurrent_api = any(token in text for token in ["并发", "1000 个 http", "1000个http", "不同的 api", "批量 api"])
    api_data = any(token in text for token in ["公开 api", "天气", "json 数据", "json", "api"])
    static_html = any(token in text for token in ["静态 html", "新闻标题", "标题和链接", "beautifulsoup"])

    if needs_intercept and has_js:
        return "Playwright"
    if needs_login and has_js:
        return "Selenium"
    if large_crawl:
        return "Scrapy"
    if concurrent_api:
        return "httpx"
    if static_html:
        return "requests + BeautifulSoup"
    if api_data:
        return "requests"
    return "manual_review"
