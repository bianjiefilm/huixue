def parse_httpbin_status(url):
    """Return the expected HTTP status code for a httpbin-style URL."""
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    if url in {"http://httpbin.org/get", "http://httpbin.org/html", "http://httpbin.org/json"}:
        return 200
    marker = "/status/"
    if marker not in url:
        raise ValueError("unsupported httpbin path")
    code_text = url.rsplit(marker, 1)[1].split("/", 1)[0].split("?", 1)[0]
    if not code_text.isdigit():
        raise ValueError("status code must be numeric")
    return int(code_text)
