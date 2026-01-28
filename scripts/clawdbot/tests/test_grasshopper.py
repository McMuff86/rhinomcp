"""Tests for grasshopper.py - pure functions only (no Rhino connection needed)."""
import pytest
from grasshopper import normalize_param_name, parse_prompt, validate_parameters

# Mock GH parameter definitions for validation tests
MOCK_GH_PARAMS = {
    'Lichthoehe': {
        'name': 'Lichthoehe',
        'type': 'NumberSlider',
        'value': 2100.0,
        'min': 1800.0,
        'max': 2600.0,
    },
    'Lichtbreite': {
        'name': 'Lichtbreite',
        'type': 'Number',
        'value': 900.0,
        'min': 600.0,
        'max': 1400.0,
    },
    'DichtNut_Rahmen': {
        'name': 'DichtNut_Rahmen',
        'type': 'Boolean',
        'value': True,
    },
}


# --- normalize_param_name ---

class TestNormalizeParamName:
    def test_pt_to_point(self):
        assert normalize_param_name('Pt') == 'Point'

    def test_punkt_to_point(self):
        assert normalize_param_name('Punkt') == 'Point'

    def test_pos_to_point(self):
        assert normalize_param_name('Pos') == 'Point'

    def test_position_to_point(self):
        assert normalize_param_name('Position') == 'Point'

    def test_unknown_passthrough(self):
        assert normalize_param_name('Lichthoehe') == 'Lichthoehe'

    def test_empty_passthrough(self):
        assert normalize_param_name('') == ''

    def test_arbitrary_name(self):
        assert normalize_param_name('FooBar') == 'FooBar'


# --- parse_prompt ---

class TestParsePrompt:
    def test_name_with_default(self):
        assert parse_prompt("Lichthoehe <2100>") == ("Lichthoehe", "2100")

    def test_get_point(self):
        assert parse_prompt("Get Point ( Undo )") == ("Point", None)

    def test_name_with_default_and_undo(self):
        assert parse_prompt("RahmenbreiteL <120> ( Undo )") == ("RahmenbreiteL", "120")

    def test_command_only(self):
        assert parse_prompt("Command") == (None, None)

    def test_empty_string(self):
        assert parse_prompt("") == (None, None)


# --- validate_parameters ---

class TestValidateParameters:
    def test_valid_number_in_range(self):
        result = validate_parameters({'Lichthoehe': 2200}, MOCK_GH_PARAMS)
        assert result.valid is True
        assert result.errors == []

    def test_number_below_minimum(self):
        result = validate_parameters({'Lichthoehe': 1500}, MOCK_GH_PARAMS)
        assert result.valid is False
        assert any('below minimum' in e for e in result.errors)

    def test_number_above_maximum(self):
        result = validate_parameters({'Lichthoehe': 3000}, MOCK_GH_PARAMS)
        assert result.valid is False
        assert any('above maximum' in e for e in result.errors)

    def test_invalid_number_string(self):
        result = validate_parameters({'Lichthoehe': 'abc'}, MOCK_GH_PARAMS)
        assert result.valid is False
        assert any('not a valid number' in e for e in result.errors)

    def test_valid_boolean_true(self):
        result = validate_parameters({'DichtNut_Rahmen': 'true'}, MOCK_GH_PARAMS)
        assert result.valid is True

    def test_valid_boolean_false(self):
        result = validate_parameters({'DichtNut_Rahmen': 'false'}, MOCK_GH_PARAMS)
        assert result.valid is True

    def test_valid_boolean_1(self):
        result = validate_parameters({'DichtNut_Rahmen': '1'}, MOCK_GH_PARAMS)
        assert result.valid is True

    def test_valid_boolean_0(self):
        result = validate_parameters({'DichtNut_Rahmen': '0'}, MOCK_GH_PARAMS)
        assert result.valid is True

    def test_invalid_boolean(self):
        result = validate_parameters({'DichtNut_Rahmen': 'maybe'}, MOCK_GH_PARAMS)
        assert result.valid is False
        assert any('not a valid boolean' in e for e in result.errors)

    def test_unknown_parameter_warning(self):
        result = validate_parameters({'UnknownParam': 42}, MOCK_GH_PARAMS)
        assert result.valid is True  # warnings don't make it invalid
        assert any('Unknown parameter' in w for w in result.warnings)

    def test_valid_point(self):
        result = validate_parameters({'Point': '1,2,3'}, MOCK_GH_PARAMS)
        assert result.valid is True

    def test_invalid_point_2d(self):
        result = validate_parameters({'Point': '1,2'}, MOCK_GH_PARAMS)
        assert result.valid is False
        assert any('Point format invalid' in e for e in result.errors)

    def test_non_numeric_point(self):
        result = validate_parameters({'Point': 'a,b,c'}, MOCK_GH_PARAMS)
        assert result.valid is False
        assert any('non-numeric' in e.lower() for e in result.errors)

    def test_multiple_params_valid(self):
        result = validate_parameters(
            {'Lichthoehe': 2100, 'Lichtbreite': 900, 'DichtNut_Rahmen': 'true'},
            MOCK_GH_PARAMS
        )
        assert result.valid is True
        assert result.errors == []

    def test_boundary_min(self):
        result = validate_parameters({'Lichthoehe': 1800}, MOCK_GH_PARAMS)
        assert result.valid is True

    def test_boundary_max(self):
        result = validate_parameters({'Lichthoehe': 2600}, MOCK_GH_PARAMS)
        assert result.valid is True
