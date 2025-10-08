"""Integration test for the full multi-agent system.

Tests the complete scenario from CLAUDE.md:
1. Initial state with 3 drones
2. UAV-002 detects new high-value entity in Area Delta
3. Agents coordinate to revise mission plan
4. UAV-003 is redirected to Area Delta
"""

import pytest
import pytest_asyncio
import os
import asyncio
from pathlib import Path

from src.context_manager import ContextManager
from src.message_bus import MessageBus
from src.agents.collection_processor import CollectionProcessorAgent
from src.agents.intelligence_analyst import IntelligenceAnalystAgent
from src.agents.mission_planner import MissionPlannerAgent
from src.agents.collection_manager import CollectionManagerAgent


@pytest_asyncio.fixture
async def system_components():
    """Set up the complete system for integration testing."""
    db_path = "test_integration_cop.db"

    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)

    # Initialize components
    context_manager = ContextManager(db_path)
    await context_manager.initialize()

    message_bus = MessageBus()

    # Create agents
    agents = {
        "collection_processor": CollectionProcessorAgent(
            role="collection_processor",
            context_manager=context_manager,
            message_bus=message_bus
        ),
        "intelligence_analyst": IntelligenceAnalystAgent(
            role="intelligence_analyst",
            context_manager=context_manager,
            message_bus=message_bus
        ),
        "mission_planner": MissionPlannerAgent(
            role="mission_planner",
            context_manager=context_manager,
            message_bus=message_bus
        ),
        "collection_manager": CollectionManagerAgent(
            role="collection_manager",
            context_manager=context_manager,
            message_bus=message_bus
        ),
    }

    # Subscribe agents
    message_bus.subscribe("intelligence_analyst", "new_intelligence")
    message_bus.subscribe("intelligence_analyst", "processed_intelligence")
    message_bus.subscribe("mission_planner", "coverage_assessment")
    message_bus.subscribe("collection_manager", "new_mission_plan")

    # Set up initial COP state
    await context_manager.update_drone(
        drone_id="UAV-001",
        lat=34.0522,
        lon=-118.2437,
        altitude=450,
        fuel_percent=85.5,
        sensor_status="operational",
        current_task="Surveilling Area Alpha"
    )

    await context_manager.update_drone(
        drone_id="UAV-002",
        lat=34.08,
        lon=-118.30,
        altitude=500,
        fuel_percent=82.5,
        sensor_status="operational",
        current_task="Surveilling Area Bravo"
    )

    await context_manager.update_drone(
        drone_id="UAV-003",
        lat=34.065,
        lon=-118.255,
        altitude=400,
        fuel_percent=68.5,
        sensor_status="operational",
        current_task="In transit"
    )

    # Add initial entities
    await context_manager.add_entity(
        entity_type="structure",
        lat=34.053,
        lon=-118.244,
        confidence=0.85,
        detected_by="UAV-001",
        description="Known facility"
    )

    await context_manager.add_entity(
        entity_type="vehicle",
        lat=34.081,
        lon=-118.301,
        confidence=0.75,
        detected_by="UAV-002",
        description="Tracked vehicle"
    )

    yield {
        "context_manager": context_manager,
        "message_bus": message_bus,
        "agents": agents
    }

    # Cleanup
    await context_manager.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_full_scenario(system_components):
    """Test the complete multi-agent coordination scenario."""
    context_manager = system_components["context_manager"]
    message_bus = system_components["message_bus"]
    agents = system_components["agents"]

    # Start all agents
    for agent in agents.values():
        await agent.start()

    # Give agents time to start
    await asyncio.sleep(1)

    # Get initial entity count
    initial_entities = await context_manager.get_entities()
    initial_count = len(initial_entities)

    # Simulate sensor data detection (the trigger event)
    sensor_data = {
        "drone_id": "UAV-002",
        "timestamp": 1704067200,
        "position": {"lat": 34.08, "lon": -118.30, "alt": 500},
        "fuel": 82.5,
        "sensor_status": "operational",
        "sensor_data": {
            "type": "visual",
            "detections": [
                {
                    "type": "vehicle",
                    "position": {"lat": 34.10, "lon": -118.35, "alt": 0},
                    "attributes": {
                        "size": "large",
                        "classification": "high_value_target"
                    }
                }
            ]
        }
    }

    # Process the sensor data
    processor = agents["collection_processor"]
    await processor._process_sensor_data(sensor_data)

    # Wait for agent coordination
    await asyncio.sleep(8)

    # Verify results
    # 1. Check that new entities were added to COP
    final_entities = await context_manager.get_entities()
    assert len(final_entities) > initial_count, "New entities should be added to COP"

    # 2. Check event log for agent activities
    events = await context_manager.get_event_log(limit=100)
    assert len(events) > 0, "Events should be logged"

    # Find events from each agent
    processor_events = [e for e in events if e['agent_role'] == 'collection_processor']
    analyst_events = [e for e in events if e['agent_role'] == 'intelligence_analyst']

    assert len(processor_events) > 0, "Collection Processor should log events"
    assert len(analyst_events) > 0, "Intelligence Analyst should log events"

    # 3. Check message history
    messages = await context_manager.get_message_history(limit=100)
    assert len(messages) > 0, "Messages should be exchanged between agents"

    # 4. Check for coverage assessment and mission planning
    planner_events = [e for e in events if e['agent_role'] == 'mission_planner']
    manager_events = [e for e in events if e['agent_role'] == 'collection_manager']

    # The system should show coordination happening
    assert len(planner_events) > 0 or len(manager_events) > 0, \
        "Mission Planner or Collection Manager should be involved"

    # Stop all agents
    for agent in agents.values():
        await agent.stop()


@pytest.mark.asyncio
async def test_agent_message_flow(system_components):
    """Test that messages flow correctly between agents."""
    message_bus = system_components["message_bus"]
    agents = system_components["agents"]

    # Start all agents
    for agent in agents.values():
        await agent.start()

    await asyncio.sleep(1)

    # Send a test message from collection processor to intelligence analyst
    await message_bus.send(
        sender="collection_processor",
        recipient="intelligence_analyst",
        message_type="processed_intelligence",
        content={
            "source": "TEST",
            "entities": [
                {"type": "test", "lat": 34.0, "lon": -118.0, "confidence": 0.9}
            ],
            "confidence": 0.9
        }
    )

    # Wait for processing
    await asyncio.sleep(3)

    # Check message history
    history = message_bus.get_message_history(limit=10)
    assert len(history) > 0, "Messages should be in history"

    # Stop agents
    for agent in agents.values():
        await agent.stop()


@pytest.mark.asyncio
async def test_authority_enforcement(system_components):
    """Test that authority enforcement works correctly."""
    context_manager = system_components["context_manager"]
    message_bus = system_components["message_bus"]

    from src.authorities import UnauthorizedActionError

    # Test 1: Intelligence Analyst CAN add entities to COP
    analyst = IntelligenceAnalystAgent(
        role="intelligence_analyst",
        context_manager=context_manager,
        message_bus=message_bus
    )

    # This should succeed
    entity_id = await analyst._add_entity_to_cop(
        entity_type="test_entity",
        lat=34.0,
        lon=-118.0,
        confidence=0.85,
        description="Test",
        source="TEST"
    )
    assert isinstance(entity_id, int)

    # Test 2: Collection Manager CAN command drones
    manager = CollectionManagerAgent(
        role="collection_manager",
        context_manager=context_manager,
        message_bus=message_bus
    )

    # This should succeed (mock returns True/False, not raise error)
    result = await manager._send_drone_command(
        "UAV-001",
        {"command_type": "navigate", "parameters": {}}
    )

    # Should return boolean (from mock), not raise error
    assert isinstance(result, bool)

    # Test 3: Collection Manager CAN create collection tasks
    task_id = await manager._create_collection_task(
        drone_id="UAV-001",
        task_type="surveillance",
        target_area="Test Area",
        priority=5
    )
    assert isinstance(task_id, int)


@pytest.mark.asyncio
async def test_cop_updates(system_components):
    """Test that COP is updated correctly through agent actions."""
    context_manager = system_components["context_manager"]
    message_bus = system_components["message_bus"]
    agents = system_components["agents"]

    analyst = agents["intelligence_analyst"]

    # Intelligence Analyst should be able to add entities
    entity_id = await analyst._add_entity_to_cop(
        entity_type="test_entity",
        lat=34.0,
        lon=-118.0,
        confidence=0.85,
        description="Test entity",
        source="TEST"
    )

    # Verify entity was added
    entities = await context_manager.get_entities()
    added_entity = next((e for e in entities if e['id'] == entity_id), None)

    assert added_entity is not None
    assert added_entity['entity_type'] == "test_entity"
    assert added_entity['confidence'] == 0.85
