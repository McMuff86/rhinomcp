"""
Tests for group and block operations tools.
"""
import json
import pytest
from unittest.mock import MagicMock, patch


class TestCreateGroup:
    """Tests for create_group tool."""

    @patch("rhinomcp.tools.create_group.get_rhino_connection")
    def test_create_group_success(self, mock_get_conn):
        from rhinomcp.tools.create_group import create_group

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "group_id": "group-123",
            "name": "TestGroup"
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = create_group(
            ctx,
            object_ids=["obj1", "obj2", "obj3"],
            name="TestGroup"
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert "TestGroup" in parsed["message"]
        assert "3 objects" in parsed["message"]
        assert parsed["data"]["group_id"] == "group-123"
        assert parsed["data"]["name"] == "TestGroup"
        assert parsed["data"]["object_count"] == 3

    @patch("rhinomcp.tools.create_group.get_rhino_connection")
    def test_create_group_without_name(self, mock_get_conn):
        from rhinomcp.tools.create_group import create_group

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "group_id": "group-456",
            "name": "Group 2"
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = create_group(
            ctx,
            object_ids=["obj1", "obj2"]
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["data"]["object_count"] == 2

    def test_create_group_empty_ids(self):
        from rhinomcp.tools.create_group import create_group

        ctx = MagicMock()
        with pytest.raises(ValueError, match="object_ids cannot be empty"):
            create_group(ctx, object_ids=[])

    def test_create_group_none_ids(self):
        from rhinomcp.tools.create_group import create_group

        ctx = MagicMock()
        with pytest.raises(ValueError, match="object_ids cannot be empty"):
            create_group(ctx, object_ids=None)


class TestUngroup:
    """Tests for ungroup tool."""

    @patch("rhinomcp.tools.ungroup.get_rhino_connection")
    def test_ungroup_success_multiple_groups(self, mock_get_conn):
        from rhinomcp.tools.ungroup import ungroup

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "objects_released": 6
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = ungroup(
            ctx,
            group_ids=["group1", "group2"]
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert "2 groups" in parsed["message"]
        assert "6 objects" in parsed["message"]
        assert parsed["data"]["groups_ungrouped"] == 2
        assert parsed["data"]["objects_released"] == 6

    @patch("rhinomcp.tools.ungroup.get_rhino_connection")
    def test_ungroup_success_single_group(self, mock_get_conn):
        from rhinomcp.tools.ungroup import ungroup

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "objects_released": 3
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = ungroup(
            ctx,
            group_id="group1"
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["data"]["groups_ungrouped"] == 1
        assert parsed["data"]["objects_released"] == 3

    def test_ungroup_no_parameters(self):
        from rhinomcp.tools.ungroup import ungroup

        ctx = MagicMock()
        with pytest.raises(ValueError, match="Either group_ids or group_id must be provided"):
            ungroup(ctx)


class TestCreateBlock:
    """Tests for create_block tool."""

    @patch("rhinomcp.tools.create_block.get_rhino_connection")
    def test_create_block_success(self, mock_get_conn):
        from rhinomcp.tools.create_block import create_block

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "block_id": "block-123",
            "name": "MyBlock",
            "object_count": 2,
            "base_point": [1, 2, 3]
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = create_block(
            ctx,
            object_ids=["obj1", "obj2"],
            name="MyBlock",
            base_point=[1, 2, 3]
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert "MyBlock" in parsed["message"]
        assert "2 objects" in parsed["message"]
        assert parsed["data"]["block_id"] == "block-123"
        assert parsed["data"]["name"] == "MyBlock"
        assert parsed["data"]["object_count"] == 2
        assert parsed["data"]["base_point"] == [1, 2, 3]

    @patch("rhinomcp.tools.create_block.get_rhino_connection")
    def test_create_block_default_base_point(self, mock_get_conn):
        from rhinomcp.tools.create_block import create_block

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "block_id": "block-456",
            "name": "Block2",
            "object_count": 1,
            "base_point": [0, 0, 0]
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = create_block(
            ctx,
            object_ids=["obj1"],
            name="Block2"
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["data"]["base_point"] == [0, 0, 0]

    def test_create_block_empty_name(self):
        from rhinomcp.tools.create_block import create_block

        ctx = MagicMock()
        with pytest.raises(ValueError, match="name cannot be empty"):
            create_block(ctx, object_ids=["obj1"], name="")

    def test_create_block_empty_ids(self):
        from rhinomcp.tools.create_block import create_block

        ctx = MagicMock()
        with pytest.raises(ValueError, match="object_ids cannot be empty"):
            create_block(ctx, object_ids=[], name="Test")

    def test_create_block_invalid_base_point(self):
        from rhinomcp.tools.create_block import create_block

        ctx = MagicMock()
        with pytest.raises(ValueError, match="base_point must be"):
            create_block(ctx, object_ids=["obj1"], name="Test", base_point=[1, 2])


class TestInsertBlock:
    """Tests for insert_block tool."""

    @patch("rhinomcp.tools.insert_block.get_rhino_connection")
    def test_insert_block_success(self, mock_get_conn):
        from rhinomcp.tools.insert_block import insert_block

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "instance_id": "instance-123",
            "block_name": "MyBlock",
            "position": [10, 20, 30],
            "scale": [2, 2, 2],
            "rotation": [0, 0, 1.57]
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = insert_block(
            ctx,
            block_name="MyBlock",
            position=[10, 20, 30],
            scale=[2, 2, 2],
            rotation=[0, 0, 1.57]
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert "MyBlock" in parsed["message"]
        assert "[10, 20, 30]" in parsed["message"]
        assert parsed["data"]["instance_id"] == "instance-123"
        assert parsed["data"]["block_name"] == "MyBlock"
        assert parsed["data"]["position"] == [10, 20, 30]
        assert parsed["data"]["scale"] == [2, 2, 2]
        assert parsed["data"]["rotation"] == [0, 0, 1.57]

    @patch("rhinomcp.tools.insert_block.get_rhino_connection")
    def test_insert_block_defaults(self, mock_get_conn):
        from rhinomcp.tools.insert_block import insert_block

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "instance_id": "instance-456",
            "block_name": "Block2",
            "position": [5, 5, 5],
            "scale": [1, 1, 1],
            "rotation": [0, 0, 0]
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = insert_block(
            ctx,
            block_name="Block2",
            position=[5, 5, 5]
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["data"]["scale"] == [1, 1, 1]
        assert parsed["data"]["rotation"] == [0, 0, 0]

    def test_insert_block_empty_name(self):
        from rhinomcp.tools.insert_block import insert_block

        ctx = MagicMock()
        with pytest.raises(ValueError, match="block_name cannot be empty"):
            insert_block(ctx, block_name="", position=[0, 0, 0])

    def test_insert_block_invalid_position(self):
        from rhinomcp.tools.insert_block import insert_block

        ctx = MagicMock()
        with pytest.raises(ValueError, match="position must be"):
            insert_block(ctx, block_name="Test", position=[1, 2])

    def test_insert_block_invalid_scale(self):
        from rhinomcp.tools.insert_block import insert_block

        ctx = MagicMock()
        with pytest.raises(ValueError, match="scale must be"):
            insert_block(ctx, block_name="Test", position=[0, 0, 0], scale=[1, 2])

    def test_insert_block_invalid_rotation(self):
        from rhinomcp.tools.insert_block import insert_block

        ctx = MagicMock()
        with pytest.raises(ValueError, match="rotation must be"):
            insert_block(ctx, block_name="Test", position=[0, 0, 0], rotation=[0, 1])


class TestExplodeBlock:
    """Tests for explode_block tool."""

    @patch("rhinomcp.tools.explode_block.get_rhino_connection")
    def test_explode_block_success_multiple_instances(self, mock_get_conn):
        from rhinomcp.tools.explode_block import explode_block

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "objects_created": 6
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = explode_block(
            ctx,
            instance_ids=["inst1", "inst2"]
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert "2 block instances" in parsed["message"]
        assert "6 objects" in parsed["message"]
        assert parsed["data"]["instances_exploded"] == 2
        assert parsed["data"]["objects_created"] == 6

    @patch("rhinomcp.tools.explode_block.get_rhino_connection")
    def test_explode_block_success_single_instance(self, mock_get_conn):
        from rhinomcp.tools.explode_block import explode_block

        mock_rhino = MagicMock()
        mock_rhino.send_command.return_value = {
            "objects_created": 3
        }
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = explode_block(
            ctx,
            instance_id="inst1"
        )
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["data"]["instances_exploded"] == 1
        assert parsed["data"]["objects_created"] == 3

    def test_explode_block_no_parameters(self):
        from rhinomcp.tools.explode_block import explode_block

        ctx = MagicMock()
        with pytest.raises(ValueError, match="Either instance_ids or instance_id must be provided"):
            explode_block(ctx)


class TestGroupOperationsErrors:
    """Tests for error handling in group operations."""

    @patch("rhinomcp.tools.create_group.get_rhino_connection")
    def test_connection_error(self, mock_get_conn):
        from rhinomcp.tools.create_group import create_group

        mock_get_conn.side_effect = Exception("Connection refused")

        ctx = MagicMock()
        result = create_group(
            ctx,
            object_ids=["obj1", "obj2"]
        )

        parsed = json.loads(result)
        assert parsed["success"] is False

    @patch("rhinomcp.tools.create_group.get_rhino_connection")
    def test_rhino_error(self, mock_get_conn):
        from rhinomcp.tools.create_group import create_group

        mock_rhino = MagicMock()
        mock_rhino.send_command.side_effect = Exception("Invalid object ID")
        mock_get_conn.return_value = mock_rhino

        ctx = MagicMock()
        result = create_group(
            ctx,
            object_ids=["invalid-id"]
        )

        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "Invalid object ID" in parsed["message"]