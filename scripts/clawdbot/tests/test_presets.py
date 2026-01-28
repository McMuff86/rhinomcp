"""Tests for presets.py - PresetManager with actual config files."""
import pytest
from presets import PresetManager


@pytest.fixture
def manager():
    """Create a PresetManager using actual config files."""
    return PresetManager()


# --- list_presets ---

class TestListPresets:
    def test_returns_non_empty(self, manager):
        presets = manager.list_presets()
        assert len(presets) > 0

    def test_filter_by_category(self, manager):
        presets = manager.list_presets(category='doors')
        assert len(presets) > 0
        for p in presets:
            assert p['category'] == 'doors'

    def test_filter_unknown_category(self, manager):
        presets = manager.list_presets(category='nonexistent')
        assert presets == []

    def test_preset_has_expected_keys(self, manager):
        presets = manager.list_presets()
        for p in presets:
            assert 'name' in p
            assert 'description' in p


# --- list_templates ---

class TestListTemplates:
    def test_returns_non_empty(self, manager):
        templates = manager.list_templates()
        assert len(templates) > 0

    def test_template_has_expected_keys(self, manager):
        templates = manager.list_templates()
        for t in templates:
            assert 'name' in t
            assert 'description' in t


# --- get_preset ---

class TestGetPreset:
    def test_standard_900(self, manager):
        preset = manager.get_preset('standard_900')
        assert preset['name'] == 'standard_900'
        assert preset['file'].endswith('.gh')
        assert preset['params']['Lichtbreite'] == 900
        assert preset['params']['Lichthoehe'] == 2100

    def test_brandschutz_t30_inherits(self, manager):
        """brandschutz_t30 uses rahmentuer_ud5 which inherits ud4 → ud3."""
        preset = manager.get_preset('brandschutz_t30')
        # From ud5
        assert preset['params']['Brandschutz'] is True
        assert preset['params']['Intumex'] is True
        # From ud4 (inherited via ud5)
        assert preset['params']['DichtNut_Rahmen'] is True
        # From ud3 (inherited via ud4 → ud5)
        assert preset['params']['Rahmendicke'] == 53
        # Overridden by preset itself
        assert preset['params']['Lichtbreite'] == 900
        # File should be ud5's
        assert 'UD5' in preset['file']

    def test_unknown_raises(self, manager):
        with pytest.raises(ValueError, match="Unknown preset"):
            manager.get_preset('unknown')

    def test_preset_has_aliases(self, manager):
        preset = manager.get_preset('standard_900')
        assert 'Pt' in preset['aliases']
        assert preset['aliases']['Pt'] == 'Point'


# --- get_template ---

class TestGetTemplate:
    def test_rahmentuer_ud4_inherits(self, manager):
        template = manager.get_template('rahmentuer_ud4')
        # Own defaults
        assert template['defaults']['Tuerstaerke'] == 58
        assert template['defaults']['DichtNut_Rahmen'] is True
        # Inherited from ud3
        assert template['defaults']['Lichtbreite'] == 900
        assert template['defaults']['Rahmendicke'] == 53

    def test_unknown_raises(self, manager):
        with pytest.raises(ValueError, match="Unknown template"):
            manager.get_template('unknown')

    def test_base_template(self, manager):
        template = manager.get_template('rahmentuer_ud3')
        assert template['file'].endswith('.gh')
        assert template['category'] == 'doors'


# --- resolve_aliases ---

class TestResolveAliases:
    def test_basic(self, manager):
        aliases = {'Pt': 'Point', 'Breite': 'Lichtbreite'}
        result = manager.resolve_aliases({'Pt': '0,0,0', 'Breite': 900}, aliases)
        assert result == {'Point': '0,0,0', 'Lichtbreite': 900}

    def test_no_alias_passthrough(self, manager):
        aliases = {'Pt': 'Point'}
        result = manager.resolve_aliases({'Lichthoehe': 2100}, aliases)
        assert result == {'Lichthoehe': 2100}

    def test_empty_params(self, manager):
        result = manager.resolve_aliases({}, {'Pt': 'Point'})
        assert result == {}

    def test_empty_aliases(self, manager):
        result = manager.resolve_aliases({'Pt': '0,0,0'}, {})
        assert result == {'Pt': '0,0,0'}
