"""Tests for run_grasshopper tool."""
import pytest
import json
from unittest.mock import MagicMock, patch


class TestRunGrasshopper:
    """Tests for run_grasshopper tool."""

    def test_run_grasshopper_success(self):
        """Test successful Grasshopper execution."""
        from rhinomcp.tools.run_grasshopper import run_grasshopper

        mock_ctx = MagicMock()
        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "file_path": "C:/test/script.gh",
            "status": "executed"
        }

        with patch("rhinomcp.tools.run_grasshopper.get_rhino_connection", return_value=mock_rhino):
            result = run_grasshopper(mock_ctx, "C:/test/script.gh")

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "file_path" in result_data["data"]
        mock_rhino.send_command.assert_called_once()

    def test_run_grasshopper_empty_path(self):
        """Test run with empty path fails."""
        from rhinomcp.tools.run_grasshopper import run_grasshopper

        mock_ctx = MagicMock()

        result = run_grasshopper(mock_ctx, "")
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "file_path is required" in result_data["message"]

    def test_run_grasshopper_wrong_extension(self):
        """Test run with non-.gh file fails."""
        from rhinomcp.tools.run_grasshopper import run_grasshopper

        mock_ctx = MagicMock()

        result = run_grasshopper(mock_ctx, "C:/test/script.py")
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert ".gh" in result_data["message"]

    def test_run_grasshopper_with_spaces(self):
        """Test run with path containing spaces."""
        from rhinomcp.tools.run_grasshopper import run_grasshopper

        mock_ctx = MagicMock()
        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "file_path": "C:/test folder/script.gh",
            "status": "executed"
        }

        with patch("rhinomcp.tools.run_grasshopper.get_rhino_connection", return_value=mock_rhino):
            result = run_grasshopper(mock_ctx, "C:/test folder/script.gh")

        result_data = json.loads(result)
        assert result_data["success"] is True
        # Verify the path was passed correctly
        call_args = mock_rhino.send_command.call_args
        assert call_args[0][1]["file_path"] == "C:/test folder/script.gh"


class TestRunGrasshopperWithParams:
    """Tests for run_grasshopper_with_params tool."""

    def test_run_grasshopper_with_params_success(self):
        """Test successful Grasshopper execution with params."""
        from rhinomcp.tools.run_grasshopper_with_params import run_grasshopper_with_params

        mock_ctx = MagicMock()
        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "file_path": "C:/test/script.gh",
            "status": "executed"
        }

        with patch("rhinomcp.tools.run_grasshopper_with_params.get_rhino_connection", return_value=mock_rhino):
            result = run_grasshopper_with_params(mock_ctx, "C:/test/script.gh")

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "interactive parameters" in result_data["message"]
        mock_rhino.send_command.assert_called_once()


class TestCreateDoorFromPlan:
    """Tests for create_door_from_plan tool."""

    def test_create_door_from_plan_standard(self):
        """Test door creation from plan text."""
        from rhinomcp.tools.create_door_from_plan import create_door_from_plan

        mock_ctx = MagicMock()
        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {"status": "started_with_instructions"}

        plan_text = "Bauplan: Einfache Tür 2200mm x 910mm für Innenbereich"

        with patch("rhinomcp.tools.create_door_from_plan.get_rhino_connection", return_value=mock_rhino):
            result = create_door_from_plan(mock_ctx, plan_text)

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "door created from plan" in result_data["message"].lower()

    def test_create_door_from_plan_with_dimensions(self):
        """Test door creation with explicit dimensions in plan."""
        from rhinomcp.tools.create_door_from_plan import create_door_from_plan

        mock_ctx = MagicMock()
        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {"status": "started_with_instructions"}

        plan_text = "Eingangstür mit Maßen 2200mm Höhe und 1010mm Breite"

        with patch("rhinomcp.tools.create_door_from_plan.get_rhino_connection", return_value=mock_rhino):
            result = create_door_from_plan(mock_ctx, plan_text, "entrance")

        result_data = json.loads(result)
        assert result_data["success"] is True
        # Should extract dimensions from text
        door_specs = result_data["data"]["door_specs"]
        assert door_specs["height"] == 2200
        assert door_specs["width"] == 1010


class TestGenerateBillOfMaterials:
    """Tests for generate_bill_of_materials tool."""

    def test_generate_bom_simple(self):
        """Test basic BOM generation."""
        from rhinomcp.tools.create_door_from_plan import generate_bill_of_materials

        mock_ctx = MagicMock()

        objects_info = json.dumps([
            {"type": "door", "dimensions": {"width": 910, "height": 2200}},
            {"type": "wall", "dimensions": {"length": 5000, "height": 2800}},
            {"type": "window", "dimensions": {"width": 1200, "height": 1500}}
        ])

        result = generate_bill_of_materials(mock_ctx, objects_info)
        result_data = json.loads(result)

        assert result_data["success"] is True
        assert "bill of materials" in result_data["message"].lower()
        assert result_data["data"]["total_items"] > 0