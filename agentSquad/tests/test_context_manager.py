"""Unit tests for Context Manager."""

import pytest
import pytest_asyncio
import os
import asyncio
from src.context_manager import ContextManager


@pytest_asyncio.fixture
async def context_manager():
    """Create a test context manager with temporary database."""
    db_path = "test_cop.db"

    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)

    cm = ContextManager(db_path)
    await cm.initialize()

    yield cm

    await cm.close()

    # Clean up
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_add_and_get_drone(context_manager):
    """Test adding and retrieving drone data."""
    await context_manager.update_drone(
        drone_id="TEST-001",
        lat=34.0,
        lon=-118.0,
        altitude=500,
        fuel_percent=75.0,
        sensor_status="operational",
        current_task="test mission"
    )

    drone = await context_manager.get_drone("TEST-001")

    assert drone is not None
    assert drone['id'] == "TEST-001"
    assert drone['lat'] == 34.0
    assert drone['lon'] == -118.0
    assert drone['fuel_percent'] == 75.0
    assert drone['current_task'] == "test mission"


@pytest.mark.asyncio
async def test_add_and_get_entity(context_manager):
    """Test adding and retrieving entities."""
    entity_id = await context_manager.add_entity(
        entity_type="vehicle",
        lat=34.1,
        lon=-118.1,
        confidence=0.85,
        detected_by="TEST-001",
        description="Test vehicle"
    )

    entities = await context_manager.get_entities()

    assert len(entities) == 1
    assert entities[0]['id'] == entity_id
    assert entities[0]['entity_type'] == "vehicle"
    assert entities[0]['confidence'] == 0.85


@pytest.mark.asyncio
async def test_create_collection_task(context_manager):
    """Test creating collection tasks."""
    # First add a drone
    await context_manager.update_drone(
        drone_id="TEST-001",
        lat=34.0,
        lon=-118.0,
        altitude=500,
        fuel_percent=75.0,
        sensor_status="operational"
    )

    task_id = await context_manager.create_collection_task(
        drone_id="TEST-001",
        task_type="surveillance",
        target_area="Test Area",
        priority=5,
        created_by="test_agent"
    )

    tasks = await context_manager.get_collection_tasks()

    assert len(tasks) == 1
    assert tasks[0]['id'] == task_id
    assert tasks[0]['drone_id'] == "TEST-001"
    assert tasks[0]['task_type'] == "surveillance"
    assert tasks[0]['status'] == "pending"


@pytest.mark.asyncio
async def test_create_mission_plan(context_manager):
    """Test creating mission plans."""
    plan_id = await context_manager.create_mission_plan(
        plan_name="Test Plan",
        objectives="Test objectives",
        assigned_drones=["TEST-001", "TEST-002"],
        created_by="test_agent"
    )

    plans = await context_manager.get_mission_plans()

    assert len(plans) == 1
    assert plans[0]['id'] == plan_id
    assert plans[0]['plan_name'] == "Test Plan"
    assert plans[0]['assigned_drones'] == ["TEST-001", "TEST-002"]
    assert plans[0]['status'] == "draft"


@pytest.mark.asyncio
async def test_message_logging(context_manager):
    """Test message logging."""
    await context_manager.log_message(
        sender="agent1",
        recipient="agent2",
        message_type="test_message",
        content="Test content",
        metadata={"key": "value"}
    )

    messages = await context_manager.get_message_history(limit=10)

    assert len(messages) == 1
    assert messages[0]['sender'] == "agent1"
    assert messages[0]['recipient'] == "agent2"
    assert messages[0]['message_type'] == "test_message"


@pytest.mark.asyncio
async def test_event_logging(context_manager):
    """Test event logging."""
    await context_manager.log_event(
        agent_role="test_agent",
        event_type="test_event",
        description="Test description",
        data={"key": "value"}
    )

    events = await context_manager.get_event_log(limit=10)

    assert len(events) == 1
    assert events[0]['agent_role'] == "test_agent"
    assert events[0]['event_type'] == "test_event"
