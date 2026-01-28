"""Tests for utils.py - shared utility functions."""
import json
import pytest
from utils import parse_coords, parse_color, parse_ids, format_point, format_result


# --- parse_coords ---

class TestParseCoords:
    def test_valid_3d(self):
        assert parse_coords("1,2,3") == [1.0, 2.0, 3.0]

    def test_valid_with_spaces(self):
        assert parse_coords("1, 2, 3") == [1.0, 2.0, 3.0]

    def test_none(self):
        assert parse_coords(None) is None

    def test_empty_string(self):
        assert parse_coords("") is None

    def test_invalid(self):
        assert parse_coords("abc") is None

    def test_2d(self):
        result = parse_coords("1,2")
        assert result == [1.0, 2.0]

    def test_floats(self):
        assert parse_coords("1.5,2.7,3.9") == [1.5, 2.7, 3.9]

    def test_negative(self):
        assert parse_coords("-1,0,3.5") == [-1.0, 0.0, 3.5]


# --- parse_color ---

class TestParseColor:
    def test_valid(self):
        assert parse_color("255,128,0") == [255, 128, 0]

    def test_none(self):
        assert parse_color(None) is None

    def test_empty(self):
        assert parse_color("") is None

    def test_invalid(self):
        assert parse_color("red,green,blue") is None

    def test_with_spaces(self):
        assert parse_color("255, 128, 0") == [255, 128, 0]


# --- parse_ids ---

class TestParseIds:
    def test_valid(self):
        assert parse_ids("abc,def,ghi") == ["abc", "def", "ghi"]

    def test_none(self):
        assert parse_ids(None) == []

    def test_empty(self):
        assert parse_ids("") == []

    def test_single(self):
        assert parse_ids("abc") == ["abc"]

    def test_with_spaces(self):
        assert parse_ids("abc, def, ghi") == ["abc", "def", "ghi"]

    def test_trailing_comma(self):
        assert parse_ids("abc,def,") == ["abc", "def"]


# --- format_point ---

class TestFormatPoint:
    def test_basic(self):
        assert format_point([1.0, 2.0, 3.0]) == "(1.00, 2.00, 3.00)"

    def test_custom_decimals(self):
        assert format_point([1.0, 2.0, 3.0], decimals=0) == "(1, 2, 3)"

    def test_negative(self):
        assert format_point([-1.5, 0.0, 3.14]) == "(-1.50, 0.00, 3.14)"

    def test_single_decimal(self):
        assert format_point([1.0, 2.0, 3.0], decimals=1) == "(1.0, 2.0, 3.0)"


# --- format_result ---

class TestFormatResult:
    def test_success_with_id(self):
        result = {"status": "success", "result": {"id": "abc-123"}}
        output = format_result(result)
        assert "OK" in output
        assert "abc-123" in output

    def test_success_with_count(self):
        result = {"status": "success", "result": {"count": 5}}
        output = format_result(result)
        assert "OK" in output
        assert "5" in output

    def test_error(self):
        result = {"status": "error", "message": "Something failed"}
        output = format_result(result)
        assert "ERROR" in output
        assert "Something failed" in output

    def test_empty_dict(self):
        # Empty dict is falsy, so format_result returns "No result"
        assert format_result({}) == "No result"

    def test_none(self):
        assert format_result(None) == "No result"

    def test_verbose(self):
        result = {"status": "success", "result": {"id": "abc"}}
        output = format_result(result, verbose=True)
        parsed = json.loads(output)
        assert parsed == result

    def test_success_with_list_result(self):
        result = {"status": "success", "result": [1, 2, 3]}
        output = format_result(result)
        assert "OK" in output
        assert "3 items" in output
