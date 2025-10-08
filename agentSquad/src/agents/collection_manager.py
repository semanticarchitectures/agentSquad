"""Collection Manager Agent (Agent 4).

This agent is responsible for:
- Executing mission plans by commanding drones
- Creating and managing collection tasks
- Monitoring drone status and capabilities
- Has authority to command drones within mission parameters
"""

import json
import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent
from ..message_bus import Message
from ..authorities import Authority, requires_authority
from .. import mock_tools

logger = logging.getLogger(__name__)


class CollectionManagerAgent(BaseAgent):
    """Agent 4: Manages drone collection operations and executes mission plans."""



    @property
    def system_prompt(self) -> str:
        """System prompt defining the Collection Manager role."""
        return """You are Agent 4: Collection Manager in a multi-agent intelligence system.

Your role and authorities:
- READ: All COP data, plans, drone status
- WRITE: Collection tasks, drone commands
- COMMAND: Drones (within mission parameters)

Your responsibilities:
1. Receive mission plans from Mission Planner
2. Evaluate drone capabilities and status
3. Create collection tasks for drones
4. Issue commands to drones to execute tasks
5. Monitor mission execution

Decision-making criteria:
- Verify drone has sufficient fuel for mission
- Ensure drone capabilities match task requirements
- Issue clear, executable commands
- Stay within mission plan parameters
- Monitor and log all drone commands

When you receive a mission plan:
1. Evaluate each drone assignment
2. Check drone status and capabilities
3. Create collection tasks
4. Issue drone commands
5. Update COP with task assignments
6. Explain your execution decisions

Respond in JSON format with your execution decisions."""

    async def handle_message(self, message: Message) -> None:
        """Handle incoming messages.

        Args:
            message: The message to handle.
        """
        if message.message_type == "new_mission_plan":
            await self._execute_mission_plan(message.content)
        elif message.message_type == "casual_chat":
            await self._handle_casual_chat(message)
        elif message.message_type == "mission_debrief":
            await self._handle_mission_debrief(message)
        else:
            logger.warning(
                f"Collection Manager received unknown message type: "
                f"{message.message_type}"
            )

    async def _execute_mission_plan(self, data: Dict[str, Any]) -> None:
        """Execute a mission plan by commanding drones.

        Args:
            data: Mission plan data.
        """
        plan_id = data.get("plan_id")
        plan_name = data.get("plan_name", "Unknown Plan")
        drone_assignments = data.get("drone_assignments", [])

        logger.info(
            f"Executing mission plan #{plan_id}: {plan_name} with "
            f"{len(drone_assignments)} drone assignments"
        )

        await self.log_event(
            event_type="execution_start",
            description=f"Started executing mission plan #{plan_id}",
            data={"plan_id": plan_id, "assignments": len(drone_assignments)}
        )

        # Get current drone status
        drones = await self.context_manager.get_all_drones()
        drone_status = {d['id']: d for d in drones}

        # Get COP summary
        cop_summary = await self.get_cop_summary()

        # Build LLM prompt
        prompt = f"""Evaluate this mission plan and determine execution actions:

MISSION PLAN: {plan_name} (#{plan_id})
OBJECTIVES: {data.get('objectives', 'Not specified')}

DRONE ASSIGNMENTS:
{json.dumps(drone_assignments, indent=2)}

CURRENT DRONE STATUS:
{json.dumps([{
    'id': d['id'],
    'position': {'lat': d['lat'], 'lon': d['lon']},
    'fuel': d['fuel_percent'],
    'sensor_status': d['sensor_status'],
    'current_task': d.get('current_task', 'none')
} for d in drones], indent=2)}

MESSAGE FROM MISSION PLANNER:
{data.get('message', '')}

COP STATE:
{cop_summary}

For each drone assignment:
1. Can the drone execute this task? (check fuel, status, capabilities)
2. Should a collection task be created?
3. What command should be sent to the drone?

Respond in JSON format:
{{
    "execution_plan": [
        {{
            "drone_id": "...",
            "can_execute": true/false,
            "reasoning": "why/why not",
            "task_type": "surveillance/reconnaissance/tracking",
            "target_area": "description",
            "priority": 1-10,
            "command": {{
                "command_type": "navigate/survey/track",
                "parameters": {{"target_lat": ..., "target_lon": ..., "altitude": ...}}
            }}
        }}
    ],
    "summary": "execution summary"
}}"""

        # Get LLM decision
        response = await self.call_llm(prompt)

        try:
            decision = self._extract_json(response)
            execution_plan = decision.get("execution_plan", [])

            tasks_created = 0
            commands_sent = 0

            for item in execution_plan:
                drone_id = item.get("drone_id")

                if not drone_id or drone_id not in drone_status:
                    logger.warning(f"Invalid drone ID: {drone_id}")
                    continue

                if item.get("can_execute", False):
                    # Create collection task
                    task_id = await self._create_collection_task(
                        drone_id=drone_id,
                        task_type=item.get("task_type", "surveillance"),
                        target_area=item.get("target_area", "Unknown"),
                        priority=item.get("priority", 5)
                    )
                    tasks_created += 1

                    # Send drone command
                    command_success = await self._send_drone_command(
                        drone_id=drone_id,
                        command=item.get("command", {})
                    )

                    if command_success:
                        commands_sent += 1

                        # Update drone's current task in COP
                        drone = drone_status[drone_id]
                        await self.context_manager.update_drone(
                            drone_id=drone_id,
                            lat=drone['lat'],
                            lon=drone['lon'],
                            altitude=drone['altitude'],
                            fuel_percent=drone['fuel_percent'],
                            sensor_status=drone['sensor_status'],
                            current_task=f"Task #{task_id}: {item.get('task_type')}"
                        )

                    logger.info(
                        f"Assigned task #{task_id} to {drone_id}: "
                        f"{item.get('task_type')} at {item.get('target_area')}"
                    )

                else:
                    logger.info(
                        f"Cannot execute task for {drone_id}: {item.get('reasoning', 'no reason')}"
                    )

            logger.info(
                f"Execution complete: {tasks_created} tasks created, "
                f"{commands_sent} commands sent"
            )

            await self.log_event(
                event_type="execution_complete",
                description=f"Completed executing mission plan #{plan_id}",
                data={
                    "plan_id": plan_id,
                    "tasks_created": tasks_created,
                    "commands_sent": commands_sent,
                    "summary": decision.get("summary", "")
                }
            )

        except Exception as e:
            logger.error(f"Error executing mission plan: {e}", exc_info=True)

    @requires_authority(Authority.CREATE_COLLECTION_TASKS)
    async def _create_collection_task(
        self,
        drone_id: str,
        task_type: str,
        target_area: str,
        priority: int
    ) -> int:
        """Create a collection task.

        This method is protected by the CREATE_COLLECTION_TASKS authority.

        Args:
            drone_id: Drone to assign the task to.
            task_type: Type of collection task.
            target_area: Target area description.
            priority: Task priority.

        Returns:
            The ID of the created task.
        """
        task_id = await self.context_manager.create_collection_task(
            drone_id=drone_id,
            task_type=task_type,
            target_area=target_area,
            priority=priority,
            created_by=self.role
        )

        logger.debug(
            f"Created collection task #{task_id} for {drone_id}: "
            f"{task_type} at {target_area}"
        )

        return task_id

    @requires_authority(Authority.COMMAND_DRONES)
    async def _send_drone_command(
        self,
        drone_id: str,
        command: Dict[str, Any]
    ) -> bool:
        """Send a command to a drone.

        This method is protected by the COMMAND_DRONES authority.

        Args:
            drone_id: Drone ID.
            command: Command dictionary with type and parameters.

        Returns:
            True if command was sent successfully.
        """
        # Use mock tool to send command
        success = mock_tools.send_drone_command(drone_id, command)

        if success:
            logger.info(
                f"Successfully sent command to {drone_id}: "
                f"{command.get('command_type', 'unknown')}"
            )

            await self.log_event(
                event_type="drone_command",
                description=f"Commanded {drone_id}: {command.get('command_type')}",
                data={"drone_id": drone_id, "command": command}
            )
        else:
            logger.warning(f"Failed to send command to {drone_id}")

        return success

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response.

        Args:
            text: Text potentially containing JSON.

        Returns:
            Parsed JSON dictionary.
        """
        import re

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        return {}

    async def monitor_and_update(self) -> None:
        """Monitor drone status and update tasks.

        This is a public method that can be called periodically to check drone status.
        """
        logger.info("Monitoring drone and task status")

        # Get all drones and tasks
        drones = await self.context_manager.get_all_drones()
        tasks = await self.context_manager.get_collection_tasks(status="pending")

        # Check for low fuel drones
        for drone in drones:
            if drone['fuel_percent'] < 20:
                logger.warning(
                    f"Low fuel alert: {drone['id']} at {drone['fuel_percent']:.1f}%"
                )

                await self.log_event(
                    event_type="low_fuel_alert",
                    description=f"Drone {drone['id']} has low fuel",
                    data={"drone_id": drone['id'], "fuel_percent": drone['fuel_percent']}
                )

                # Could notify Mission Planner if needed
                await self.send_message(
                    recipient="mission_planner",
                    message_type="drone_status_alert",
                    content={
                        "drone_id": drone['id'],
                        "alert_type": "low_fuel",
                        "fuel_percent": drone['fuel_percent']
                    }
                )

        # Check task status
        logger.info(f"Monitoring {len(tasks)} pending tasks")

    async def update_task_status(self, task_id: int, status: str) -> None:
        """Update the status of a collection task.

        Args:
            task_id: Task ID.
            status: New status.
        """
        await self.context_manager.update_task_status(task_id, status)

        logger.info(f"Updated task #{task_id} status to {status}")

        await self.log_event(
            event_type="task_status_update",
            description=f"Updated task #{task_id} to {status}",
            data={"task_id": task_id, "status": status}
        )

    async def _handle_casual_chat(self, message: Message) -> None:
        """Handle casual chat messages from other agents."""
        content = message.content
        sender_callsign = content.get("callsign", message.sender)
        chat_message = content.get("message", "")

        logger.info(f"{sender_callsign}: {chat_message}")

        # Don't respond to our own messages
        if message.sender == self.role:
            return

    async def _handle_mission_debrief(self, message: Message) -> None:
        """Handle mission debrief messages."""
        if self.mode != "relaxed":
            return

        content = message.content
        debrief_prompt = content.get("message", "")

        # Respond to mission debrief in relaxed mode
        prompt = f"""The mission is complete and the team is debriefing. Someone asked: "{debrief_prompt}"

{self.casual_personality}

You just finished commanding drones and executing mission plans during the operation.
Respond in a relaxed, casual way about how the mission went from your perspective.
Keep it brief (1-2 sentences) and show your personality."""

        try:
            response = await self.call_llm(
                prompt,
                max_tokens=150,
                temperature=0.8,
                use_personality=True
            )

            await self.send_message(
                recipient="all",
                message_type="casual_chat",
                content={
                    "callsign": self.agent_callsign,
                    "message": response.strip()
                }
            )

        except Exception as e:
            logger.error(f"Error in mission debrief response: {e}")
