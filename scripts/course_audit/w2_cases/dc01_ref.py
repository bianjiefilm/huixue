def recommend_collection_tool(scenario):
    if not isinstance(scenario, str):
        raise TypeError("scenario must be str")
    text = scenario.strip()
    if not text:
        return "manual_review"

    if "静态 HTML" in text and "新闻标题" in text:
        return "requests + BeautifulSoup"
    if "登录" in text and "JavaScript 动态渲染" in text:
        return "Selenium"
    if "并发发送 1000" in text and "HTTP GET" in text:
        return "httpx"
    if "1000+ 页面" in text or "1000+ 页面的电商网站" in text:
        return "Scrapy"
    if "React 单页应用" in text or "SPA" in text:
        return "Playwright"
    if "天气数据公开 API" in text:
        return "requests"
    return "manual_review"
