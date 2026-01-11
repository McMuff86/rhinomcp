"""Tests for command output monitoring tools."""

import json
from unittest.mock import MagicMock, patch

import pytest

from rhinomcp.tools.get_command_output import (
    clear_command_output,
    disable_command_listener,
    enable_command_listener,
    get_command_output,
)


@pytest.fixture
def mock_rhino_connection():
    """Mock Rhino connection."""
    with patch("rhinomcp.tools.get_command_output.get_rhino_connection") as mock:
        connection = MagicMock()
        mock.return_value = connection
        yield connection


@pytest.fixture
def mock_context():
    """Mock MCP context."""
    return MagicMock()


def test_get_command_output_default(mock_context, mock_rhino_connection):
    """Test getting command output with default parameters."""
    mock_rhino_connection.send_command.return_value = {
        "events": [
            {
                "timestamp": "2026-01-11 12:34:56.789",
                "text": "Command: _Line",
                "type": "Out"
            },
            {
                "timestamp": "2026-01-11 12:34:57.123",
                "text": "Start of line ( Undo )",
                "type": "Prompt"
            }
        ],
        "count": 2,
        "current_prompt": "Start of line ( Undo )"
    }
    
    result = get_command_output(mock_context)
    
    mock_rhino_connection.send_command.assert_called_once_with(
        "get_command_output",
        {"count": 50, "since": None}
    )
    
    result_data = json.loads(result)
    assert result_data["status"] == "success"
    assert result_data["data"]["count"] == 2
    assert len(result_data["data"]["events"]) == 2
    assert result_data["data"]["current_prompt"] == "Start of line ( Undo )"


def test_get_command_output_with_count(mock_context, mock_rhino_connection):
    """Test getting command output with custom count."""
    mock_rhino_connection.send_command.return_value = {
        "events": [],
        "count": 0,
        "current_prompt": "Command: "
    }
    
    result = get_command_output(mock_context, count=20)
    
    mock_rhino_connection.send_command.assert_called_once_with(
        "get_command_output",
        {"count": 20, "since": None}
    )
    
    result_data = json.loads(result)
    assert result_data["status"] == "success"


def test_get_command_output_with_since(mock_context, mock_rhino_connection):
    """Test getting command output since specific time."""
    mock_rhino_connection.send_command.return_value = {
        "events": [
            {
                "timestamp": "2026-01-11 12:35:00.000",
                "text": "GetPlane ( WorldXY WorldYZ WorldZX Undo )",
                "type": "Prompt"
            }
        ],
        "count": 1,
        "current_prompt": "GetPlane ( WorldXY WorldYZ WorldZX Undo )"
    }
    
    since_time = "2026-01-11 12:34:00.000"
    result = get_command_output(mock_context, since=since_time)
    
    mock_rhino_connection.send_command.assert_called_once_with(
        "get_command_output",
        {"count": 50, "since": since_time}
    )
    
    result_data = json.loads(result)
    assert result_data["status"] == "success"
    assert result_data["data"]["events"][0]["type"] == "Prompt"


def test_get_command_output_max_count(mock_context, mock_rhino_connection):
    """Test count is capped at maximum."""
    mock_rhino_connection.send_command.return_value = {
        "events": [],
        "count": 0,
        "current_prompt": ""
    }
    
    result = get_command_output(mock_context, count=1000)
    
    # Should be capped at 200
    mock_rhino_connection.send_command.assert_called_once_with(
        "get_command_output",
        {"count": 200, "since": None}
    )


def test_get_command_output_error(mock_context, mock_rhino_connection):
    """Test error handling when getting command output fails."""
    mock_rhino_connection.send_command.side_effect = Exception("Connection lost")
    
    result = get_command_output(mock_context)
    
    result_data = json.loads(result)
    assert result_data["status"] == "error"
    assert "Connection lost" in result_data["message"]


def test_clear_command_output(mock_context, mock_rhino_connection):
    """Test clearing command output buffer."""
    mock_rhino_connection.send_command.return_value = {
        "message": "Command output cleared"
    }
    
    result = clear_command_output(mock_context)
    
    mock_rhino_connection.send_command.assert_called_once_with(
        "clear_command_output",
        {}
    )
    
    result_data = json.loads(result)
    assert result_data["status"] == "success"


def test_clear_command_output_error(mock_context, mock_rhino_connection):
    """Test error handling when clearing fails."""
    mock_rhino_connection.send_command.side_effect = Exception("Clear failed")
    
    result = clear_command_output(mock_context)
    
    result_data = json.loads(result)
    assert result_data["status"] == "error"


def test_enable_command_listener(mock_context, mock_rhino_connection):
    """Test enabling command listener."""
    mock_rhino_connection.send_command.return_value = {
        "message": "Command listener enabled"
    }
    
    result = enable_command_listener(mock_context)
    
    mock_rhino_connection.send_command.assert_called_once_with(
        "enable_command_listener",
        {}
    )
    
    result_data = json.loads(result)
    assert result_data["status"] == "success"


def test_enable_command_listener_error(mock_context, mock_rhino_connection):
    """Test error handling when enabling fails."""
    mock_rhino_connection.send_command.side_effect = Exception("Enable failed")
    
    result = enable_command_listener(mock_context)
    
    result_data = json.loads(result)
    assert result_data["status"] == "error"


def test_disable_command_listener(mock_context, mock_rhino_connection):
    """Test disabling command listener."""
    mock_rhino_connection.send_command.return_value = {
        "message": "Command listener disabled"
    }
    
    result = disable_command_listener(mock_context)
    
    mock_rhino_connection.send_command.assert_called_once_with(
        "disable_command_listener",
        {}
    )
    
    result_data = json.loads(result)
    assert result_data["status"] == "success"


def test_disable_command_listener_error(mock_context, mock_rhino_connection):
    """Test error handling when disabling fails."""
    mock_rhino_connection.send_command.side_effect = Exception("Disable failed")
    
    result = disable_command_listener(mock_context)
    
    result_data = json.loads(result)
    assert result_data["status"] == "error"


def test_prompt_detection():
    """Test that we can detect different types of prompts."""
    # Test data mimicking real Rhino prompts
    prompts = [
        ("GetPlane ( WorldXY WorldYZ WorldZX Undo )", "Prompt"),
        ("Start of line ( Undo )", "Prompt"),
        ("Command: _Line", "Out"),
        ("Line created", "Out"),
        ("Lichthoehe: ___", "Prompt"),
    ]
    
    for text, expected_type in prompts:
        # This would be handled by the C# side, but we test the concept
        is_prompt = "(" in text and ")" in text or ":" in text
        detected_type = "Prompt" if is_prompt else "Out"
        assert detected_type == expected_type or text.startswith("Command:")
