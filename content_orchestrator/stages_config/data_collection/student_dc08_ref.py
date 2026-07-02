import re
from urllib.parse import urljoin


def parse_scrapy_product_page(html, page_url, category=None):
    """Parse a product list page using Scrapy-style output."""
    if not isinstance(html, str) or not isinstance(page_url, str):
        raise TypeError("html and page_url must be strings")
    if not (page_url.startswith("http://") or page_url.startswith("https://")):
        raise ValueError("page_url must start with http:// or https://")

    items = []
    seen = set()
    for card in re.findall(r'<div[^>]*class="[^"]*product-card[^"]*"[^>]*>(.*?)</div>', html, flags=re.S):
        title_match = re.search(r'class="[^"]*title[^"]*"[^>]*>(.*?)<', card, flags=re.S)
        price_match = re.search(r'class="[^"]*price[^"]*"[^>]*>(.*?)<', card, flags=re.S)
        link_match = re.search(r'<a[^>]*href="([^"]+)"', card)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else ""
        price_text = price_match.group(1).strip() if price_match else ""
        price_match_value = re.search(r"-?\d+(?:\.\d+)?", price_text)
        product_url = urljoin(page_url, link_match.group(1)) if link_match else page_url
        if product_url in seen:
            continue
        seen.add(product_url)
        items.append(
            {
                "title": title,
                "price": float(price_match_value.group(0)) if price_match_value else None,
                "product_url": product_url,
                "category": category,
            }
        )

    next_match = re.search(r'<a[^>]*class="[^"]*next[^"]*"[^>]*href="([^"]+)"', html)
    requests = []
    if next_match:
        requests.append(
            {
                "url": urljoin(page_url, next_match.group(1)),
                "callback": "parse",
                "meta": {"category": category},
            }
        )

    return {"items": items, "requests": requests}
