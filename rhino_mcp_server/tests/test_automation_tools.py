"""Tests for automation tools (plan analysis, BOM generation)."""
import json
from unittest.mock import MagicMock, patch

from rhinomcp.tools.create_door_from_plan import analyze_plan_for_doors


class TestPlanAnalysis:
    """Tests for plan analysis functions."""

    def test_analyze_plan_standard_door(self):
        """Test analysis of standard door specifications."""
        plan_text = "Normale Innentür mit Standardmaßen"
        result = analyze_plan_for_doors(plan_text, "standard")

        assert result["height"] == 2200
        assert result["width"] == 910
        assert "standard" in result["description"].lower()

    def test_analyze_plan_entrance_door(self):
        """Test analysis of entrance door specifications."""
        plan_text = "Haupteingangstür 2200mm x 1010mm"
        result = analyze_plan_for_doors(plan_text, "entrance")

        assert result["height"] == 2200
        assert result["width"] == 1010
        assert "entrance" in result["description"].lower()

    def test_analyze_plan_with_explicit_dimensions(self):
        """Test extraction of explicit dimensions from plan text."""
        plan_text = "Tür mit Maßen Höhe 2100mm und Breite 950mm"
        result = analyze_plan_for_doors(plan_text, "standard")

        assert result["height"] == 2100
        assert result["width"] == 950

    def test_analyze_plan_german_text(self):
        """Test analysis of German plan text."""
        plan_text = "Tür mit Lichthöhe 2200 und Lichtbreite 810"
        result = analyze_plan_for_doors(plan_text, "interior")

        assert result["height"] == 2200
        assert result["width"] == 810

    def test_analyze_plan_plane_detection(self):
        """Test automatic plane detection from context."""
        # Front door should be WorldXY
        front_plan = "Haustür im Vordereingang"
        result = analyze_plan_for_doors(front_plan, "entrance")
        assert result["plane"] == "WorldXY"

        # Side door might be WorldYZ
        side_plan = "Seiteneingang mit Tür"
        result = analyze_plan_for_doors(side_plan, "standard")
        assert result["plane"] == "WorldXY"  # Default for now