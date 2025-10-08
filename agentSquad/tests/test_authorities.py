"""Unit tests for the authority system."""

import pytest
from src.authorities import (
    Authority,
    get_role_authorities,
    has_authority,
    UnauthorizedActionError,
    requires_authority
)


def test_get_role_authorities():
    """Test getting authorities for each role."""
    # Test collection processor
    cp_authorities = get_role_authorities("collection_processor")
    assert Authority.READ_SENSOR_DATA in cp_authorities
    assert Authority.WRITE_PROCESSED_INTEL in cp_authorities
    assert Authority.COMMAND_DRONES not in cp_authorities

    # Test intelligence analyst
    ia_authorities = get_role_authorities("intelligence_analyst")
    assert Authority.READ_COP in ia_authorities
    assert Authority.WRITE_COP in ia_authorities
    assert Authority.COMMAND_DRONES not in ia_authorities

    # Test mission planner
    mp_authorities = get_role_authorities("mission_planner")
    assert Authority.READ_COP in mp_authorities
    assert Authority.WRITE_PLANS in mp_authorities
    assert Authority.COMMAND_DRONES not in mp_authorities

    # Test collection manager
    cm_authorities = get_role_authorities("collection_manager")
    assert Authority.COMMAND_DRONES in cm_authorities
    assert Authority.CREATE_COLLECTION_TASKS in cm_authorities


def test_invalid_role():
    """Test that invalid roles raise ValueError."""
    with pytest.raises(ValueError):
        get_role_authorities("invalid_role")


def test_has_authority():
    """Test checking if a role has specific authority."""
    assert has_authority("collection_processor", Authority.READ_SENSOR_DATA) is True
    assert has_authority("collection_processor", Authority.COMMAND_DRONES) is False

    assert has_authority("collection_manager", Authority.COMMAND_DRONES) is True
    assert has_authority("collection_manager", Authority.READ_SENSOR_DATA) is False


def test_requires_authority_decorator():
    """Test the requires_authority decorator."""

    class TestAgent:
        def __init__(self, role):
            self.role = role

        @requires_authority(Authority.COMMAND_DRONES)
        def command_drone(self):
            return "Command sent"

    # Collection manager should succeed
    manager = TestAgent("collection_manager")
    result = manager.command_drone()
    assert result == "Command sent"

    # Collection processor should fail
    processor = TestAgent("collection_processor")
    with pytest.raises(UnauthorizedActionError):
        processor.command_drone()


@pytest.mark.asyncio
async def test_requires_authority_async():
    """Test the requires_authority decorator with async methods."""

    class TestAgent:
        def __init__(self, role):
            self.role = role

        @requires_authority(Authority.COMMAND_DRONES)
        async def command_drone_async(self):
            return "Async command sent"

    # Collection manager should succeed
    manager = TestAgent("collection_manager")
    result = await manager.command_drone_async()
    assert result == "Async command sent"

    # Intelligence analyst should fail
    analyst = TestAgent("intelligence_analyst")
    with pytest.raises(UnauthorizedActionError):
        await analyst.command_drone_async()
