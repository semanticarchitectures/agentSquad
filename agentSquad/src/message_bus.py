"""Message Bus for agent-to-agent communication.

This module provides an in-memory event system for agents to communicate
through a publish-subscribe pattern.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a message passed between agents."""

    sender: str
    recipient: str  # Can be specific agent role or "all" for broadcast
    message_type: str
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()


class MessageBus:
    """In-memory message bus for agent communication.

    Supports publish-subscribe pattern where agents can:
    - Subscribe to specific message types
    - Publish messages to specific agents or broadcast to all
    - Receive messages asynchronously via queues
    """

    def __init__(self):
        """Initialize the message bus."""
        # Dict mapping agent role to their message queue
        self._agent_queues: Dict[str, asyncio.Queue] = {}

        # Dict mapping message type to list of subscribed agents
        self._subscriptions: Dict[str, List[str]] = {}

        # Message history for debugging
        self._message_history: List[Message] = []
        self._max_history = 1000

        logger.info("Message bus initialized")

    def register_agent(self, agent_role: str) -> asyncio.Queue:
        """Register an agent and create its message queue.

        Args:
            agent_role: The role identifier of the agent.

        Returns:
            The agent's message queue.
        """
        if agent_role in self._agent_queues:
            logger.warning(f"Agent {agent_role} already registered")
            return self._agent_queues[agent_role]

        queue = asyncio.Queue()
        self._agent_queues[agent_role] = queue
        logger.info(f"Registered agent: {agent_role}")
        return queue

    def unregister_agent(self, agent_role: str) -> None:
        """Unregister an agent and remove its queue.

        Args:
            agent_role: The role identifier of the agent.
        """
        if agent_role in self._agent_queues:
            del self._agent_queues[agent_role]
            logger.info(f"Unregistered agent: {agent_role}")

        # Remove from all subscriptions
        for message_type in list(self._subscriptions.keys()):
            if agent_role in self._subscriptions[message_type]:
                self._subscriptions[message_type].remove(agent_role)

    def subscribe(self, agent_role: str, message_type: str) -> None:
        """Subscribe an agent to a message type.

        Args:
            agent_role: The role identifier of the agent.
            message_type: The type of message to subscribe to.
        """
        if message_type not in self._subscriptions:
            self._subscriptions[message_type] = []

        if agent_role not in self._subscriptions[message_type]:
            self._subscriptions[message_type].append(agent_role)
            logger.debug(f"Agent {agent_role} subscribed to {message_type}")

    def unsubscribe(self, agent_role: str, message_type: str) -> None:
        """Unsubscribe an agent from a message type.

        Args:
            agent_role: The role identifier of the agent.
            message_type: The type of message to unsubscribe from.
        """
        if message_type in self._subscriptions:
            if agent_role in self._subscriptions[message_type]:
                self._subscriptions[message_type].remove(agent_role)
                logger.debug(f"Agent {agent_role} unsubscribed from {message_type}")

    async def publish(self, message: Message) -> None:
        """Publish a message to recipients.

        Messages are delivered to:
        1. The specific recipient if named
        2. All agents subscribed to the message type

        Args:
            message: The message to publish.
        """
        # Add to message history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)

        recipients = set()

        # Add specific recipient if not broadcast
        if message.recipient != "all" and message.recipient in self._agent_queues:
            recipients.add(message.recipient)

        # Add all subscribers to this message type
        if message.message_type in self._subscriptions:
            for agent in self._subscriptions[message.message_type]:
                # Don't send message back to sender
                if agent != message.sender:
                    recipients.add(agent)

        # If broadcast to all
        if message.recipient == "all":
            for agent in self._agent_queues.keys():
                if agent != message.sender:
                    recipients.add(agent)

        # Deliver to all recipients
        for recipient in recipients:
            if recipient in self._agent_queues:
                await self._agent_queues[recipient].put(message)
                logger.debug(
                    f"Delivered message from {message.sender} to {recipient} "
                    f"(type: {message.message_type})"
                )

        if not recipients:
            logger.debug(
                f"No recipients for message from {message.sender} "
                f"(type: {message.message_type})"
            )

    async def send(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Convenience method to create and publish a message.

        Args:
            sender: The sending agent role.
            recipient: The recipient agent role or "all".
            message_type: The type of message.
            content: The message content.
            metadata: Optional metadata dictionary.
        """
        message = Message(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            metadata=metadata,
        )
        await self.publish(message)

    async def receive(self, agent_role: str, timeout: Optional[float] = None) -> Optional[Message]:
        """Receive a message for an agent (non-blocking with optional timeout).

        Args:
            agent_role: The role identifier of the agent.
            timeout: Optional timeout in seconds.

        Returns:
            The next message for the agent, or None if timeout expires.
        """
        if agent_role not in self._agent_queues:
            raise ValueError(f"Agent {agent_role} not registered")

        queue = self._agent_queues[agent_role]

        try:
            if timeout:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                message = await queue.get()
            return message
        except asyncio.TimeoutError:
            return None

    def get_queue(self, agent_role: str) -> Optional[asyncio.Queue]:
        """Get the message queue for an agent.

        Args:
            agent_role: The role identifier of the agent.

        Returns:
            The agent's queue or None if not registered.
        """
        return self._agent_queues.get(agent_role)

    def get_message_history(self, limit: int = 100) -> List[Message]:
        """Get recent message history.

        Args:
            limit: Maximum number of messages to return.

        Returns:
            List of recent messages, newest first.
        """
        return list(reversed(self._message_history[-limit:]))

    def clear_history(self) -> None:
        """Clear the message history."""
        self._message_history.clear()
        logger.debug("Message history cleared")

    def get_subscriptions(self, agent_role: str) -> List[str]:
        """Get all message types an agent is subscribed to.

        Args:
            agent_role: The role identifier of the agent.

        Returns:
            List of message types.
        """
        subscriptions = []
        for message_type, agents in self._subscriptions.items():
            if agent_role in agents:
                subscriptions.append(message_type)
        return subscriptions

    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics.

        Returns:
            Dictionary with statistics.
        """
        return {
            "registered_agents": list(self._agent_queues.keys()),
            "total_agents": len(self._agent_queues),
            "subscriptions": {
                msg_type: len(agents)
                for msg_type, agents in self._subscriptions.items()
            },
            "message_history_size": len(self._message_history),
            "queue_sizes": {
                agent: queue.qsize()
                for agent, queue in self._agent_queues.items()
            },
        }
