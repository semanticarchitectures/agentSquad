"""Unit tests for Message Bus."""

import pytest
import asyncio
from src.message_bus import MessageBus, Message


@pytest.fixture
def message_bus():
    """Create a message bus for testing."""
    return MessageBus()


@pytest.mark.asyncio
async def test_register_agent(message_bus):
    """Test agent registration."""
    queue = message_bus.register_agent("test_agent")

    assert queue is not None
    assert "test_agent" in message_bus._agent_queues


@pytest.mark.asyncio
async def test_subscribe(message_bus):
    """Test message type subscription."""
    message_bus.register_agent("agent1")
    message_bus.subscribe("agent1", "test_type")

    assert "test_type" in message_bus._subscriptions
    assert "agent1" in message_bus._subscriptions["test_type"]


@pytest.mark.asyncio
async def test_send_and_receive(message_bus):
    """Test sending and receiving messages."""
    message_bus.register_agent("sender")
    message_bus.register_agent("recipient")

    await message_bus.send(
        sender="sender",
        recipient="recipient",
        message_type="test",
        content="Hello"
    )

    message = await message_bus.receive("recipient", timeout=1.0)

    assert message is not None
    assert message.sender == "sender"
    assert message.recipient == "recipient"
    assert message.content == "Hello"


@pytest.mark.asyncio
async def test_broadcast(message_bus):
    """Test broadcasting to all agents."""
    message_bus.register_agent("agent1")
    message_bus.register_agent("agent2")
    message_bus.register_agent("sender")

    await message_bus.send(
        sender="sender",
        recipient="all",
        message_type="broadcast",
        content="Broadcast message"
    )

    # Both non-sender agents should receive the message
    msg1 = await message_bus.receive("agent1", timeout=1.0)
    msg2 = await message_bus.receive("agent2", timeout=1.0)

    assert msg1 is not None
    assert msg2 is not None
    assert msg1.content == "Broadcast message"
    assert msg2.content == "Broadcast message"


@pytest.mark.asyncio
async def test_subscription_delivery(message_bus):
    """Test that subscribed agents receive messages."""
    message_bus.register_agent("agent1")
    message_bus.register_agent("agent2")
    message_bus.register_agent("sender")

    message_bus.subscribe("agent1", "important")
    # agent2 is not subscribed

    await message_bus.send(
        sender="sender",
        recipient="agent2",  # Specific recipient
        message_type="important",
        content="Important message"
    )

    # agent1 should receive because it's subscribed
    msg1 = await message_bus.receive("agent1", timeout=1.0)
    assert msg1 is not None

    # agent2 should receive because it's the named recipient
    msg2 = await message_bus.receive("agent2", timeout=1.0)
    assert msg2 is not None


@pytest.mark.asyncio
async def test_message_history(message_bus):
    """Test message history tracking."""
    message_bus.register_agent("agent1")
    message_bus.register_agent("agent2")

    await message_bus.send(
        sender="agent1",
        recipient="agent2",
        message_type="test",
        content="Message 1"
    )

    await message_bus.send(
        sender="agent2",
        recipient="agent1",
        message_type="test",
        content="Message 2"
    )

    history = message_bus.get_message_history(limit=10)

    assert len(history) == 2
    assert history[0].content == "Message 2"  # Newest first
    assert history[1].content == "Message 1"


@pytest.mark.asyncio
async def test_unregister_agent(message_bus):
    """Test agent unregistration."""
    message_bus.register_agent("test_agent")
    message_bus.subscribe("test_agent", "test_type")

    message_bus.unregister_agent("test_agent")

    assert "test_agent" not in message_bus._agent_queues
    assert "test_agent" not in message_bus._subscriptions.get("test_type", [])
