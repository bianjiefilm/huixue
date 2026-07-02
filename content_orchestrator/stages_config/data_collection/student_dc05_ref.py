def build_api_collection_request(api_url, bearer_token, page=1, page_size=100):
    """Build an authenticated paginated API request."""
    if not isinstance(api_url, str) or not isinstance(bearer_token, str):
        raise TypeError("api_url and bearer_token must be strings")
    if not isinstance(page, int) or not isinstance(page_size, int):
        raise TypeError("page and page_size must be integers")
    if not (api_url.startswith("http://") or api_url.startswith("https://")):
        raise ValueError("api_url must start with http:// or https://")
    if not bearer_token.startswith("Bearer ") or len(bearer_token.strip()) <= len("Bearer "):
        raise ValueError("bearer_token must use Bearer authentication")
    if page < 1:
        raise ValueError("page must be >= 1")
    if page_size < 1 or page_size > 500:
        raise ValueError("page_size must be between 1 and 500")

    return {
        "method": "GET",
        "url": api_url,
        "headers": {
            "Authorization": bearer_token,
            "Accept": "application/json",
        },
        "params": {
            "page": page,
            "page_size": page_size,
        },
        "timeout_seconds": 10,
        "retry": {
            "max_attempts": 3,
            "backoff_seconds": 1,
        },
    }
