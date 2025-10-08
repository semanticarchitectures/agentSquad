"""Base Agent class for multi-agent intelligence system.

This module provides the abstract base class that all specialized agents inherit from.
It enforces the authority model and provides common functionality for LLM interaction.
"""

import asyncio
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from anthropic import AsyncAnthropic

from .context_manager import ContextManager
from .message_bus import MessageBus, Message
from .authorities import get_role_authorities, Authority

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the system.

    Provides:
    - Authority checking based on role
    - Access to Context Manager (COP)
    - Access to Message Bus
    - LLM API integration
    - Message handling loop
    - Personality modes (casual/professional)
    """

    def __init__(
        self,
        role: str,
        context_manager: ContextManager,
        message_bus: MessageBus,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize the base agent.

        Args:
            role: The agent's role identifier (e.g., "collection_processor").
            context_manager: Shared context manager instance.
            message_bus: Shared message bus instance.
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var).
            model: Claude model to use.
        """
        self.role = role
        self.context_manager = context_manager
        self.message_bus = message_bus
        self.model = model

        # Personality and mode tracking
        self.mode = "casual"  # "casual", "professional", "relaxed"
        self.has_introduced = False

        # Verify role has defined authorities
        try:
            self.authorities = get_role_authorities(role)
            logger.info(f"Agent {role} initialized with {len(self.authorities)} authorities")
        except ValueError:
            logger.error(f"Invalid role: {role}")
            raise

        # Initialize Anthropic client
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")
        self.client = AsyncAnthropic(api_key=api_key)

        # Register with message bus
        self.message_queue = message_bus.register_agent(role)

        # Control flags
        self._running = False
        self._task: Optional[asyncio.Task] = None

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent.

        Each agent must define its own system prompt that describes its role,
        authorities, and decision-making criteria.

        Returns:
            System prompt string.
        """
        pass

    @property
    @abstractmethod
    def casual_personality(self) -> str:
        """Return the casual personality description for this agent.

        Returns:
            Casual personality string for introductions and relaxed chat.
        """
        pass

    @property
    @abstractmethod
    def agent_callsign(self) -> str:
        """Return the agent's callsign/nickname.

        Returns:
            Short callsign for the agent.
        """
        pass

    def set_mode(self, mode: str) -> None:
        """Set the agent's communication mode.

        Args:
            mode: "casual", "professional", or "relaxed"
        """
        self.mode = mode
        logger.info(f"Agent {self.role} switched to {mode} mode")

    async def introduce_self(self) -> None:
        """Have the agent introduce themselves in casual mode."""
        if self.has_introduced:
            return

        self.has_introduced = True

        # Build casual introduction prompt
        prompt = f"""You are {self.agent_callsign} in a multi-agent squad.

{self.casual_personality}

The squad is gathering for a mission briefing. Introduce yourself to the team in a casual, friendly way.
Keep it brief (2-3 sentences), mention your role, and show your personality.
You're talking to your fellow agents before the serious work begins.

Respond as if you're speaking directly to the team."""

        try:
            introduction = await self.call_llm(prompt, max_tokens=200, temperature=0.9)

            # Send introduction to all agents
            await self.send_message(
                recipient="all",
                message_type="introduction",
                content={
                    "callsign": self.agent_callsign,
                    "message": introduction.strip()
                }
            )

            logger.info(f"{self.agent_callsign} introduced themselves")

        except Exception as e:
            logger.error(f"Error during introduction for {self.role}: {e}")

    async def start(self) -> None:
        """Start the agent's message processing loop."""
        if self._running:
            logger.warning(f"Agent {self.role} is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Agent {self.role} started")

    async def stop(self) -> None:
        """Stop the agent's message processing loop."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(f"Agent {self.role} stopped")

    async def _run_loop(self) -> None:
        """Main message processing loop.

        Continuously receives messages and processes them.
        """
        logger.info(f"Agent {self.role} entering run loop")

        while self._running:
            try:
                # Wait for messages with timeout to allow checking _running flag
                message = await self.message_bus.receive(self.role, timeout=1.0)

                if message:
                    await self._handle_message(message)

            except asyncio.CancelledError:
                logger.info(f"Agent {self.role} run loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in agent {self.role} run loop: {e}", exc_info=True)
                # Continue running despite errors
                await asyncio.sleep(1)

        logger.info(f"Agent {self.role} exiting run loop")

    async def _handle_message(self, message: Message) -> None:
        """Handle an incoming message.

        Args:
            message: The message to handle.
        """
        logger.info(
            f"Agent {self.role} received message from {message.sender} "
            f"(type: {message.message_type})"
        )

        try:
            # Log message to COP
            await self.context_manager.log_message(
                sender=message.sender,
                recipient=self.role,
                message_type=message.message_type,
                content=str(message.content),
                metadata=message.metadata,
            )

            # Handle introduction messages specially
            if message.message_type == "introduction":
                await self._handle_introduction(message)
            else:
                # Delegate to specific handler
                await self.handle_message(message)

        except Exception as e:
            logger.error(
                f"Error handling message in agent {self.role}: {e}",
                exc_info=True
            )

    async def _handle_introduction(self, message: Message) -> None:
        """Handle introduction messages from other agents.

        Args:
            message: Introduction message from another agent.
        """
        if message.sender == self.role:
            return  # Don't respond to our own introduction

        content = message.content
        callsign = content.get("callsign", message.sender)
        intro_message = content.get("message", "")

        logger.info(f"{callsign}: {intro_message}")

        # Occasionally respond to introductions in casual mode
        if self.mode == "casual" and not self.has_introduced:
            # Small chance to respond casually
            import random
            if random.random() < 0.3:  # 30% chance to respond
                response_prompt = f"""Another agent just introduced themselves: "{intro_message}"

{self.casual_personality}

Respond briefly and casually to their introduction. Keep it short (1 sentence) and friendly.
You haven't introduced yourself yet, so don't give away too much about your role."""

                try:
                    response = await self.call_llm(
                        response_prompt,
                        max_tokens=100,
                        temperature=0.8,
                        use_personality=True
                    )

                    await self.send_message(
                        recipient="all",
                        message_type="casual_chat",
                        content={
                            "callsign": self.agent_callsign,
                            "message": response.strip(),
                            "responding_to": callsign
                        }
                    )

                except Exception as e:
                    logger.error(f"Error responding to introduction: {e}")

    @abstractmethod
    async def handle_message(self, message: Message) -> None:
        """Handle a message (to be implemented by subclasses).

        Args:
            message: The message to handle.
        """
        pass

    async def call_llm(
        self,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        use_personality: bool = False,
    ) -> str:
        """Call the Claude API with the agent's system prompt.

        Args:
            user_message: The user message/prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            use_personality: Whether to use personality-aware prompting.

        Returns:
            The LLM's response text.
        """
        logger.debug(f"Agent {self.role} calling LLM in {self.mode} mode")

        # Choose system prompt based on mode and context
        if use_personality and self.mode == "casual":
            system_prompt = f"{self.casual_personality}\n\nYou are speaking casually with your team before operations begin."
        elif use_personality and self.mode == "relaxed":
            system_prompt = f"{self.casual_personality}\n\nThe mission is complete. You can relax and speak casually with your team."
        elif self.mode == "professional":
            system_prompt = f"{self.system_prompt}\n\nYou are in professional military mode. Use clear, concise, military-style communication. Address others by callsign when appropriate."
        else:
            system_prompt = self.system_prompt

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )

            # Extract text from response
            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            logger.debug(
                f"Agent {self.role} received LLM response ({len(response_text)} chars)"
            )

            # Log the LLM interaction
            await self.context_manager.log_event(
                agent_role=self.role,
                event_type="llm_call",
                description=f"Called LLM with {len(user_message)} char prompt",
                data={
                    "model": self.model,
                    "prompt_length": len(user_message),
                    "response_length": len(response_text),
                }
            )

            return response_text

        except Exception as e:
            logger.error(f"LLM call failed for agent {self.role}: {e}", exc_info=True)
            raise

    async def send_message(
        self,
        recipient: str,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a message to another agent.

        Args:
            recipient: Recipient agent role or "all" for broadcast.
            message_type: Type of message.
            content: Message content.
            metadata: Optional metadata.
        """
        await self.message_bus.send(
            sender=self.role,
            recipient=recipient,
            message_type=message_type,
            content=content,
            metadata=metadata,
        )

        logger.debug(
            f"Agent {self.role} sent message to {recipient} (type: {message_type})"
        )

    async def log_event(
        self,
        event_type: str,
        description: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an event to the COP.

        Args:
            event_type: Type of event.
            description: Human-readable description.
            data: Optional event data.
        """
        await self.context_manager.log_event(
            agent_role=self.role,
            event_type=event_type,
            description=description,
            data=data,
        )

    def has_authority(self, authority: Authority) -> bool:
        """Check if this agent has a specific authority.

        Args:
            authority: The authority to check.

        Returns:
            True if the agent has the authority.
        """
        return authority in self.authorities

    async def get_cop_summary(self) -> str:
        """Get a summary of the current COP state for context.

        Returns:
            Formatted string with COP summary.
        """
        # Get all relevant COP data
        drones = await self.context_manager.get_all_drones()
        entities = await self.context_manager.get_entities()
        tasks = await self.context_manager.get_collection_tasks()
        plans = await self.context_manager.get_mission_plans()

        summary_parts = [
            "=== COMMON OPERATING PICTURE ===\n",
            f"DRONES ({len(drones)}):",
        ]

        for drone in drones:
            summary_parts.append(
                f"  - {drone['id']}: ({drone['lat']:.4f}, {drone['lon']:.4f}) "
                f"alt={drone['altitude']}m, fuel={drone['fuel_percent']:.1f}%, "
                f"sensors={drone['sensor_status']}, task={drone.get('current_task', 'none')}"
            )

        summary_parts.append(f"\nENTITIES ({len(entities)}):")
        for entity in entities[:10]:  # Limit to 10 most recent
            summary_parts.append(
                f"  - #{entity['id']} {entity['entity_type']}: "
                f"({entity['lat']:.4f}, {entity['lon']:.4f}) "
                f"confidence={entity['confidence']:.2f}, detected_by={entity['detected_by']}"
            )

        if len(entities) > 10:
            summary_parts.append(f"  ... and {len(entities) - 10} more")

        summary_parts.append(f"\nCOLLECTION TASKS ({len(tasks)}):")
        for task in tasks:
            summary_parts.append(
                f"  - #{task['id']} {task['task_type']} for {task['drone_id']}: "
                f"{task['target_area']}, priority={task['priority']}, status={task['status']}"
            )

        summary_parts.append(f"\nMISSION PLANS ({len(plans)}):")
        for plan in plans:
            summary_parts.append(
                f"  - #{plan['id']} {plan['plan_name']}: "
                f"status={plan['status']}, drones={plan['assigned_drones']}"
            )

        return "\n".join(summary_parts)

    async def make_decision(self, context: str, question: str) -> str:
        """Use LLM to make a decision based on context.

        Args:
            context: Context information for the decision.
            question: The specific question or decision to make.

        Returns:
            The LLM's decision/response.
        """
        # Build the full prompt
        prompt = f"{context}\n\n{question}"

        # Call LLM
        response = await self.call_llm(prompt)

        # Log the decision
        await self.log_event(
            event_type="decision",
            description=f"Made decision: {question[:100]}...",
            data={
                "question": question,
                "response_preview": response[:200],
            }
        )

        return response
