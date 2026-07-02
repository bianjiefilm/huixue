"""
Unit tests for backend/app/core/errors.py — pure error response factories.
"""
import pytest
from app.core.errors import (
    ERROR_CODES,
    success_response,
    error_response,
    not_found_response,
    validation_error_response,
    internal_error_response,
    paginate_meta,
)


class TestSuccessResponse:

    def test_defaults(self):
        r = success_response()
        assert r["code"] == "0000"
        assert r["message"] == "success"
        assert r["data"] is None

    def test_with_data(self):
        r = success_response(data={"id": 1})
        assert r["data"] == {"id": 1}

    def test_custom_message(self):
        r = success_response(message="created")
        assert r["message"] == "created"


class TestErrorResponse:

    def test_basic(self):
        r = error_response("5000", "boom")
        assert r["code"] == "5000"
        assert r["message"] == "boom"
        assert r["data"] is None

    def test_with_data(self):
        r = error_response("4000", "bad", data={"field": "name"})
        assert r["data"] == {"field": "name"}


class TestNotFound:

    def test_default_entity(self):
        r = not_found_response()
        assert r["code"] == "4004"
        assert "资源" in r["message"]

    def test_with_entity_and_id(self):
        r = not_found_response("课程", 42)
        assert "课程" in r["message"]
        assert "42" in r["message"]


class TestValidationError:

    def test_message(self):
        r = validation_error_response("字段不合法")
        assert r["code"] == "4000"
        assert r["message"] == "字段不合法"

    def test_with_details(self):
        r = validation_error_response("bad", details={"f": "x"})
        assert r["data"] == {"f": "x"}


class TestInternalError:

    def test_default(self):
        r = internal_error_response()
        assert r["code"] == "5000"

    def test_custom(self):
        r = internal_error_response("db crashed")
        assert r["message"] == "db crashed"


class TestPaginateMeta:

    def test_single_page(self):
        m = paginate_meta(5, 1, 20)
        assert m == {"total": 5, "page": 1, "page_size": 20, "total_pages": 1}

    def test_multiple_pages(self):
        m = paginate_meta(25, 2, 10)
        assert m["total_pages"] == 3

    def test_exact_division(self):
        m = paginate_meta(20, 1, 10)
        assert m["total_pages"] == 2

    def test_zero_total(self):
        m = paginate_meta(0, 1, 10)
        assert m["total_pages"] == 0

    def test_zero_page_size(self):
        m = paginate_meta(10, 1, 0)
        assert m["total_pages"] == 0


class TestErrorCodes:

    def test_all_codes_are_strings(self):
        for k, v in ERROR_CODES.items():
            assert isinstance(v, str), f"{k} should be str"

    def test_success_code(self):
        assert ERROR_CODES["SUCCESS"] == "0000"
