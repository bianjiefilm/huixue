import importlib
import os

import pytest


CASES = [
    ('<html><body><a href="https://example.com">Example</a><a href="https://test.org">Test</a></body></html>', [{"text": "Example", "href": "https://example.com"}, {"text": "Test", "href": "https://test.org"}]),
    ('<html><body><a>无 href 链接</a><a href="https://cn.bing.com">必应</a><div>不是链接</div></body></html>', [{"text": "无 href 链接", "href": None}, {"text": "必应", "href": "https://cn.bing.com"}]),
    ('<html><body><a href="/path?param=中文&key=value">编码测试</a><a href="https://unicode.com">Unicode</a></body></html>', [{"text": "编码测试", "href": "/path?param=中文&key=value"}, {"text": "Unicode", "href": "https://unicode.com"}]),
    ('<html><body><a href="https://a.com"><span class="icon">🔗</span>带图标的链接</a></body></html>', [{"text": "🔗带图标的链接", "href": "https://a.com"}]),
    ('<html><body><!-- 注释里的 <a> 链接 --><a href="https://visible.com">可见链接</a><script>document.write(\\\'<a href="https://invisible.com">脚本链接</a>\\\')</script></body></html>', [{"text": "可见链接", "href": "https://visible.com"}]),
    ('<html><body>\n    <div class="nav">\n        <a href="/home"> 首页 </a>\n        <a href="/about"> 关于 </a>\n        <a href=""> 空 href </a>\n        <a href="https://demo.com">  示例站  </a>\n    </div>\n</body></html>', [{"text": "首页", "href": "/home"}, {"text": "关于", "href": "/about"}, {"text": "空 href", "href": ""}, {"text": "示例站", "href": "https://demo.com"}]),
    ('<a href="https://x.com">X</a>', [{"text": "X", "href": "https://x.com"}]),
    ('<a href="https://y.com">Y</a>', [{"text": "Y", "href": "https://y.com"}]),
    ('<a href="https://z.com">Z</a>', [{"text": "Z", "href": "https://z.com"}]),
    ('<a href="https://w.com">W</a>', [{"text": "W", "href": "https://w.com"}]),
    ("<div>No links</div>", []),
    ("", []),
]


def _student():
    return importlib.import_module(os.environ.get("DC03_MODULE", "student_dc03"))


@pytest.mark.parametrize(("html", "expected"), CASES)
def test_extract_links(html, expected):
    assert _student().extract_links(html) == expected


def test_extract_links_rejects_none():
    with pytest.raises(TypeError):
        _student().extract_links(None)


def test_extract_links_rejects_list():
    with pytest.raises(TypeError):
        _student().extract_links(["<a>x</a>"])
