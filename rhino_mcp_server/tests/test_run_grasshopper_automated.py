"""Tests for run_grasshopper_automated and run_door_script tools."""
import json
from unittest.mock import MagicMock, patch


class TestRunGrasshopperAutomated:
    """Tests for run_grasshopper_automated tool."""

    def test_empty_file_path_returns_error(self):
        """Test that empty file_path returns validation error."""
        from rhinomcp.tools.run_grasshopper_automated import run_grasshopper_automated

        result = run_grasshopper_automated(
            ctx=MagicMock(),
            file_path="",
            inputs=["100", "200"]
        )
        data = json.loads(result)
        
        assert data["success"] is False
        assert "file_path is required" in data["message"]

    def test_invalid_file_extension_returns_error(self):
        """Test that non-.gh file returns validation error."""
        from rhinomcp.tools.run_grasshopper_automated import run_grasshopper_automated

        result = run_grasshopper_automated(
            ctx=MagicMock(),
            file_path="C:/path/to/file.txt",
            inputs=["100", "200"]
        )
        data = json.loads(result)
        
        assert data["success"] is False
        assert ".gh file" in data["message"]

    def test_empty_inputs_returns_error(self):
        """Test that empty inputs array returns validation error."""
        from rhinomcp.tools.run_grasshopper_automated import run_grasshopper_automated

        result = run_grasshopper_automated(
            ctx=MagicMock(),
            file_path="C:/path/to/script.gh",
            inputs=[]
        )
        data = json.loads(result)
        
        assert data["success"] is False
        assert "inputs array is required" in data["message"]

    def test_negative_initial_delay_returns_error(self):
        """Test that negative initial_delay_ms returns validation error."""
        from rhinomcp.tools.run_grasshopper_automated import run_grasshopper_automated

        result = run_grasshopper_automated(
            ctx=MagicMock(),
            file_path="C:/path/to/script.gh",
            inputs=["100"],
            initial_delay_ms=-100
        )
        data = json.loads(result)
        
        assert data["success"] is False
        assert "non-negative" in data["message"]

    def test_timeout_too_short_returns_error(self):
        """Test that timeout_ms < 1000 returns validation error."""
        from rhinomcp.tools.run_grasshopper_automated import run_grasshopper_automated

        result = run_grasshopper_automated(
            ctx=MagicMock(),
            file_path="C:/path/to/script.gh",
            inputs=["100"],
            timeout_ms=500
        )
        data = json.loads(result)
        
        assert data["success"] is False
        assert "at least 1000ms" in data["message"]

    @patch("rhinomcp.tools.run_grasshopper_automated.get_rhino_connection")
    def test_successful_execution(self, mock_get_rhino):
        """Test successful Grasshopper automated execution."""
        from rhinomcp.tools.run_grasshopper_automated import run_grasshopper_automated

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "file_path": "C:/scripts/test.gh",
            "status": "success",
            "automated": True,
            "inputs_sent": ["2200", "910", "0"]
        }
        mock_get_rhino.return_value = mock_rhino

        result = run_grasshopper_automated(
            ctx=MagicMock(),
            file_path="C:/scripts/test.gh",
            inputs=["2200", "910", "0"]
        )
        data = json.loads(result)
        
        assert data["success"] is True
        assert "3 automated inputs" in data["message"]
        assert data["data"]["status"] == "success"
        assert data["data"]["automated"] is True

    @patch("rhinomcp.tools.run_grasshopper_automated.get_rhino_connection")
    def test_timeout_status(self, mock_get_rhino):
        """Test timeout status is properly handled."""
        from rhinomcp.tools.run_grasshopper_automated import run_grasshopper_automated

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "file_path": "C:/scripts/test.gh",
            "status": "timeout",
            "automated": False
        }
        mock_get_rhino.return_value = mock_rhino

        result = run_grasshopper_automated(
            ctx=MagicMock(),
            file_path="C:/scripts/test.gh",
            inputs=["100"]
        )
        data = json.loads(result)
        
        assert data["success"] is True
        assert "timed out" in data["message"]
        assert data["data"]["status"] == "timeout"

    @patch("rhinomcp.tools.run_grasshopper_automated.get_rhino_connection")
    def test_connection_error(self, mock_get_rhino):
        """Test connection error handling."""
        from rhinomcp.tools.run_grasshopper_automated import run_grasshopper_automated

        mock_get_rhino.side_effect = ConnectionError("Rhino not running")

        result = run_grasshopper_automated(
            ctx=MagicMock(),
            file_path="C:/scripts/test.gh",
            inputs=["100"]
        )
        data = json.loads(result)
        
        assert data["success"] is False
        assert "message" in data


class TestRunDoorScript:
    """Tests for run_door_script convenience tool."""

    def test_empty_file_path_returns_error(self):
        """Test that empty file_path returns validation error."""
        from rhinomcp.tools.run_grasshopper_automated import run_door_script

        result = run_door_script(
            ctx=MagicMock(),
            file_path=""
        )
        data = json.loads(result)
        
        assert data["success"] is False
        assert "file_path is required" in data["message"]

    def test_invalid_file_extension_returns_error(self):
        """Test that non-.gh file returns validation error."""
        from rhinomcp.tools.run_grasshopper_automated import run_door_script

        result = run_door_script(
            ctx=MagicMock(),
            file_path="C:/path/to/file.py"
        )
        data = json.loads(result)
        
        assert data["success"] is False
        assert ".gh file" in data["message"]

    @patch("rhinomcp.tools.run_grasshopper_automated.get_rhino_connection")
    def test_default_parameters(self, mock_get_rhino):
        """Test that default parameters are used correctly."""
        from rhinomcp.tools.run_grasshopper_automated import run_door_script

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "result": "Door created: True"
        }
        mock_get_rhino.return_value = mock_rhino

        result = run_door_script(
            ctx=MagicMock(),
            file_path="C:/scripts/door.gh"
        )
        data = json.loads(result)
        
        assert data["success"] is True
        # Check that correct command was sent
        call_args = mock_rhino.send_command.call_args
        code = call_args[0][1]["code"]
        assert "2200" in code  # Default height
        assert "910" in code   # Default width
        assert "0 0 0" in code or "0.0 0.0 0.0" in code  # Default origin

    @patch("rhinomcp.tools.run_grasshopper_automated.get_rhino_connection")
    def test_custom_parameters(self, mock_get_rhino):
        """Test that custom parameters are passed correctly."""
        from rhinomcp.tools.run_grasshopper_automated import run_door_script

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "result": "Door created: True"
        }
        mock_get_rhino.return_value = mock_rhino

        result = run_door_script(
            ctx=MagicMock(),
            file_path="C:/scripts/door.gh",
            height=2500,
            width=1200,
            origin_x=1000,
            origin_y=500,
            origin_z=0
        )
        data = json.loads(result)
        
        assert data["success"] is True
        # Check that custom values are in the code
        call_args = mock_rhino.send_command.call_args
        code = call_args[0][1]["code"]
        assert "2500" in code  # Custom height
        assert "1200" in code  # Custom width
        assert "1000" in code  # Custom origin_x

    @patch("rhinomcp.tools.run_grasshopper_automated.get_rhino_connection")
    def test_door_parameters_in_response(self, mock_get_rhino):
        """Test that door parameters are included in response."""
        from rhinomcp.tools.run_grasshopper_automated import run_door_script

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "result": "Door created: True"
        }
        mock_get_rhino.return_value = mock_rhino

        result = run_door_script(
            ctx=MagicMock(),
            file_path="C:/scripts/door.gh",
            height=2200,
            width=910,
            origin_x=0,
            origin_y=0,
            origin_z=0
        )
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["data"]["height"] == 2200
        assert data["data"]["width"] == 910
        assert data["data"]["origin"] == [0, 0, 0]
        assert data["data"]["fully_automated"] is True

    @patch("rhinomcp.tools.run_grasshopper_automated.get_rhino_connection")
    def test_custom_origin_position(self, mock_get_rhino):
        """Test door at custom position."""
        from rhinomcp.tools.run_grasshopper_automated import run_door_script

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "result": "Door created: True"
        }
        mock_get_rhino.return_value = mock_rhino

        result = run_door_script(
            ctx=MagicMock(),
            file_path="C:/scripts/door.gh",
            origin_x=5000,
            origin_y=2000,
            origin_z=100
        )
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["data"]["origin"] == [5000, 2000, 100]
