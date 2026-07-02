import importlib
import importlib.util
import os
from pathlib import Path

import pytest


def _student():
    module = os.environ.get("DC09_MODULE")
    if module:
        return importlib.import_module(module)
    path = (
        Path(__file__).resolve().parents[2]
        / "content_orchestrator"
        / "stages_config"
        / "data_collection"
        / "student_dc09.py"
    )
    spec = importlib.util.spec_from_file_location("student_dc09_stage", path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


CASES = [
    ('{"data":{"user":{"name":"张三"}}}', "data.user.name", "张三"),
    ('{"data":{"items":["a","b","c"]}}', "data.items.1", "b"),
    ('{"name":"test"}', "name", "test"),
    ('{"a":{"b":{"c":1}}}', "a.x.c", {"error": "path_not_found"}),
    ("invalid json", "data", {"error": "invalid_format"}),
    ('{"data":{"list":[{"id":1},{"id":2}]}}', "data.list.1.id", 2),
    (
        '<catalog><product id="P001"><name>产品A</name><price currency="CNY">99.9</price></product></catalog>',
        None,
        [{"id": "P001", "name": "产品A", "price": 99.9, "currency": "CNY", "specs": {}, "tags": []}],
    ),
    ("<catalog></catalog>", None, []),
    ('{"items":[{"price":42}]}', "items.0.price", 42),
    ('{"users":[{"id":1,"name":"alice"},{"id":2,"name":"bob"}]}', "users.1.name", "bob"),
    ('{"meta":{"version":"v3"}}', "meta.version", "v3"),
    ("<root><tag>hello</tag></root>", None, [{"tag": "hello"}]),
]


@pytest.mark.parametrize(("payload", "path", "expected"), CASES)
def test_parse_structured_data(payload, path, expected):
    assert _student().parse_structured_data(payload, path) == expected


def test_rejects_non_string_payload():
    with pytest.raises(TypeError):
        _student().parse_structured_data(None, "name")


def test_rejects_non_string_path():
    with pytest.raises(TypeError):
        _student().parse_structured_data('{"name":"test"}', 1)


def test_returns_full_json_without_path():
    assert _student().parse_structured_data('{"ok":true}', None) == {"ok": True}
