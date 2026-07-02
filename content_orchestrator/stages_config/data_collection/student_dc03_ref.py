from html.parser import HTMLParser


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attr_map = dict(attrs)
            self._current = {"text": "", "href": attr_map.get("href")}

    def handle_data(self, data):
        if self._current is not None:
            self._current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._current is not None:
            self._current["text"] = self._current["text"].strip()
            self.links.append(self._current)
            self._current = None


def extract_links(html):
    """Extract link text and href values from HTML."""
    if not isinstance(html, str):
        raise TypeError("html must be a string")
    parser = _LinkParser()
    parser.feed(html)
    return parser.links
