import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("DC08_MODULE", "student_dc08"))


CASES = [
    (
        '<div class="product-card"><a href="/p/1"><span class="title">键盘</span><span class="price">$19.99</span></a></div><div class="product-card"><a href="/p/2"><span class="title">鼠标</span><span class="price">$9.50</span></a></div><div class="product-card"><a href="/p/3"><span class="title">显示器</span><span class="price">$199.00</span></a></div>',
        "https://shop.example.com/list",
        "electronics",
        {
            "items": [
                {"title": "键盘", "price": 19.99, "product_url": "https://shop.example.com/p/1", "category": "electronics"},
                {"title": "鼠标", "price": 9.5, "product_url": "https://shop.example.com/p/2", "category": "electronics"},
                {"title": "显示器", "price": 199.0, "product_url": "https://shop.example.com/p/3", "category": "electronics"},
            ],
            "requests": [],
        },
    ),
    (
        '<div class="product-card"><a href="item/a"><span class="title">A</span><span class="price">￥88</span></a></div><a class="next" href="/list?page=2">Next</a>',
        "https://shop.example.com/list?page=1",
        "books",
        {
            "items": [{"title": "A", "price": 88.0, "product_url": "https://shop.example.com/item/a", "category": "books"}],
            "requests": [{"url": "https://shop.example.com/list?page=2", "callback": "parse", "meta": {"category": "books"}}],
        },
    ),
    (
        '<div class="product-card"><a href="https://cdn.example.com/p/9"><span class="title">云服务</span><span class="price">free</span></a></div>',
        "https://shop.example.com/list",
        None,
        {
            "items": [{"title": "云服务", "price": None, "product_url": "https://cdn.example.com/p/9", "category": None}],
            "requests": [],
        },
    ),
    (
        '<div class="product-card"><a href="/p/dup"><span class="title">重复1</span><span class="price">10</span></a></div><div class="product-card"><a href="/p/dup"><span class="title">重复2</span><span class="price">20</span></a></div>',
        "https://shop.example.com/list",
        "sale",
        {
            "items": [{"title": "重复1", "price": 10.0, "product_url": "https://shop.example.com/p/dup", "category": "sale"}],
            "requests": [],
        },
    ),
    (
        "",
        "https://shop.example.com/list",
        "empty",
        {"items": [], "requests": []},
    ),
    (
        '<div class="product-card"><span class="title">无链接</span><span class="price">42</span></div>',
        "https://shop.example.com/current",
        "misc",
        {
            "items": [{"title": "无链接", "price": 42.0, "product_url": "https://shop.example.com/current", "category": "misc"}],
            "requests": [],
        },
    ),
    (
        '<div class="product-card"><a href="../p/7"><span class="title">相对路径</span><span class="price">7.25</span></a></div>',
        "https://shop.example.com/category/list/index.html",
        "relative",
        {
            "items": [{"title": "相对路径", "price": 7.25, "product_url": "https://shop.example.com/category/p/7", "category": "relative"}],
            "requests": [],
        },
    ),
    (
        '<div class="product-card"><a href="/p/n"><span class="title">负价测试</span><span class="price">-1</span></a></div>',
        "http://localhost:8000/list",
        "test",
        {
            "items": [{"title": "负价测试", "price": -1.0, "product_url": "http://localhost:8000/p/n", "category": "test"}],
            "requests": [],
        },
    ),
    (
        '<a class="next" href="page/2">Next</a>',
        "https://shop.example.com/list/",
        None,
        {"items": [], "requests": [{"url": "https://shop.example.com/list/page/2", "callback": "parse", "meta": {"category": None}}]},
    ),
]


@pytest.mark.parametrize(("html", "page_url", "category", "expected"), CASES)
def test_parse_scrapy_product_page(html, page_url, category, expected):
    assert _student().parse_scrapy_product_page(html, page_url, category) == expected


def test_rejects_non_string_html():
    with pytest.raises(TypeError):
        _student().parse_scrapy_product_page(None, "https://shop.example.com/list")


def test_rejects_non_string_url():
    with pytest.raises(TypeError):
        _student().parse_scrapy_product_page("", None)


def test_rejects_bad_url_scheme():
    with pytest.raises(ValueError):
        _student().parse_scrapy_product_page("", "ftp://shop.example.com/list")
