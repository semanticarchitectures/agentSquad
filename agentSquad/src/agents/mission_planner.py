"""Mission Planner Agent (Agent 3).

This agent is responsible for:
- Creating and revising mission plans
- Responding to coverage gaps and intelligence assessments
- Evaluating drone capabilities for missions
- Cannot command drones directly (only create plans for Collection Manager)
"""

import json
import logging
from typing import Dict, Any, List

from ..base_agent import BaseAgent
from ..message_bus import Message
from ..authorities import Authority, requires_authority
from .. import mock_tools

logger = logging.getLogger(__name__)


class MissionPlannerAgent(BaseAgent):
    """Agent 3: Plans and revises missions based on intelligence and coverage gaps."""



    @property
    def system_prompt(self) -> str:
        """System prompt defining the Mission Planner role."""
        return """You are Agent 3: Mission Planner in a multi-agent intelligence system.

Your role and authorities:
- READ: COP, collection requirements, drone capabilities
- WRITE: Mission plans, plan revisions
- CANNOT: Command drones directly, override Collection Manager

Your responsibilities:
1. Receive coverage assessments from Intelligence Analyst
2. Evaluate current mission plans against needs
3. Create or revise mission plans to address gaps
4. Assign drones to coverage areas
5. Communicate plans to Collection Manager for execution

Decision-making criteria:
- Prioritize high-value targets and coverage gaps
- Consider drone fuel levels and capabilities
- Balance multiple collection requirements
- Create realistic, executable plans
- Explain reasoning for plan decisions

When you receive a coverage assessment or strategic update:
1. Evaluate the current situation
2. Determine if mission plan needs revision
3. Select appropriate drones for the mission
4. Create/update the mission plan
5. Communicate the plan to Collection Manager

Respond in JSON format with your planning decisions."""

    async def handle_message(self, message: Message) -> None:
        """Handle incoming messages.

        Args:
            message: The message to handle.
        """
        if message.message_type == "coverage_assessment":
            await self._handle_coverage_assessment(message.content)
        elif message.message_type == "strategic_assessment":
            await self._handle_strategic_assessment(message.content)
        elif message.message_type == "casual_chat":
            await self._handle_casual_chat(message)
        elif message.message_type == "mission_debrief":
            await self._handle_mission_debrief(message)
        else:
            logger.warning(
                f"Mission Planner received unknown message type: "
                f"{message.message_type}"
            )

    async def _handle_coverage_assessment(self, data: Dict[str, Any]) -> None:
        """Handle a coverage assessment from Intelligence Analyst.

        Args:
            data: Coverage assessment data.
        """
        coverage_gaps = data.get("coverage_gaps", [])
        priority_areas = data.get("priority_areas", [])

        logger.info(
            f"Received coverage assessment: {len(coverage_gaps)} gaps, "
            f"{len(priority_areas)} priority areas"
        )

        await self.log_event(
            event_type="planning_start",
            description="Started mission planning for coverage gaps",
            data={"gaps_count": len(coverage_gaps), "priority_count": len(priority_areas)}
        )

        # Get current COP state
        cop_summary = await self.get_cop_summary()

        # Get drone status
        drones = await self.context_manager.get_all_drones()

        # Get current plans
        plans = await self.context_manager.get_mission_plans()

        # Build LLM prompt
        prompt = f"""Analyze this coverage situation and create/revise mission plan:

COVERAGE ASSESSMENT:
Coverage Percentage: {data.get('coverage_percentage', 0):.1f}%
Total Gaps: {len(coverage_gaps)}
Priority Areas: {len(priority_areas)}

COVERAGE GAPS:
{json.dumps(coverage_gaps, indent=2)}

PRIORITY AREAS NEEDING COVERAGE:
{json.dumps(priority_areas, indent=2)}

ANALYSIS SUMMARY:
{data.get('analysis_summary', 'No summary provided')}

AVAILABLE DRONES:
{json.dumps([{
    'id': d['id'],
    'position': {'lat': d['lat'], 'lon': d['lon']},
    'fuel': d['fuel_percent'],
    'current_task': d.get('current_task', 'none')
} for d in drones], indent=2)}

CURRENT MISSION PLANS:
{json.dumps([{
    'id': p['id'],
    'name': p['plan_name'],
    'status': p['status'],
    'assigned_drones': p['assigned_drones']
} for p in plans], indent=2)}

COP STATE:
{cop_summary}

Based on this situation:
1. Does the current mission plan need revision?
2. Which drones should be reassigned?
3. What are the new mission objectives?

Respond in JSON format:
{{
    "needs_revision": true/false,
    "reasoning": "why revision is needed",
    "plan_name": "name for the plan",
    "objectives": "mission objectives",
    "drone_assignments": [
        {{"drone_id": "...", "target_area": "...", "task_type": "...", "priority": 1-10}}
    ],
    "notify_collection_manager": true/false,
    "message_to_manager": "instructions for collection manager"
}}"""

        # Get LLM decision
        response = await self.call_llm(prompt)

        try:
            decision = self._extract_json(response)

            if decision.get("needs_revision", False):
                # Create or update mission plan
                plan_id = await self._create_mission_plan(
                    plan_name=decision.get("plan_name", "Coverage Gap Response"),
                    objectives=decision.get("objectives", "Address coverage gaps"),
                    drone_assignments=decision.get("drone_assignments", [])
                )

                logger.info(f"Created/revised mission plan #{plan_id}")

                # Notify Collection Manager
                if decision.get("notify_collection_manager", False):
                    await self.send_message(
                        recipient="collection_manager",
                        message_type="new_mission_plan",
                        content={
                            "plan_id": plan_id,
                            "plan_name": decision.get("plan_name"),
                            "objectives": decision.get("objectives"),
                            "drone_assignments": decision.get("drone_assignments"),
                            "message": decision.get("message_to_manager", "")
                        }
                    )

                    logger.info("Notified Collection Manager of new mission plan")

            else:
                logger.info(
                    f"No mission revision needed: {decision.get('reasoning', 'no reason')}"
                )

            await self.log_event(
                event_type="planning_complete",
                description="Completed mission planning",
                data={
                    "revision_needed": decision.get("needs_revision", False),
                    "assignments": len(decision.get("drone_assignments", []))
                }
            )

        except Exception as e:
            logger.error(f"Error in mission planning: {e}", exc_info=True)

    async def _handle_strategic_assessment(self, data: Dict[str, Any]) -> None:
        """Handle a strategic assessment from Intelligence Analyst.

        Args:
            data: Strategic assessment data.
        """
        report_id = data.get("report_id", "unknown")
        assessment = data.get("assessment", "")
        priorities = data.get("priorities", [])

        logger.info(f"Received strategic assessment from report {report_id}")

        await self.log_event(
            event_type="strategic_planning",
            description=f"Processing strategic assessment from {report_id}",
            data={"report_id": report_id}
        )

        # Get current COP and plans
        cop_summary = await self.get_cop_summary()
        plans = await self.context_manager.get_mission_plans()
        drones = await self.context_manager.get_all_drones()

        prompt = f"""Analyze this strategic intelligence and determine planning actions:

STRATEGIC ASSESSMENT:
{assessment}

RECOMMENDED PRIORITIES:
{json.dumps(priorities, indent=2)}

MESSAGE FROM ANALYST:
{data.get('message', '')}

CURRENT PLANS:
{json.dumps([{
    'id': p['id'],
    'name': p['plan_name'],
    'status': p['status']
} for p in plans], indent=2)}

AVAILABLE DRONES:
{json.dumps([{
    'id': d['id'],
    'fuel': d['fuel_percent']
} for d in drones], indent=2)}

COP:
{cop_summary}

Should the mission plan be updated based on this strategic intelligence?

Respond in JSON format:
{{
    "update_needed": true/false,
    "reasoning": "why update is needed",
    "action": "create_new_plan/update_existing/no_action",
    "plan_updates": {{"plan_name": "...", "objectives": "...", "priority_adjustments": []}}
}}"""

        response = await self.call_llm(prompt)

        try:
            decision = self._extract_json(response)

            if decision.get("update_needed", False):
                logger.info(
                    f"Strategic assessment requires plan update: "
                    f"{decision.get('reasoning', '')}"
                )

                # Take appropriate action based on decision
                # (Implementation would create/update plans as needed)

        except Exception as e:
            logger.error(f"Error processing strategic assessment: {e}", exc_info=True)

    @requires_authority(Authority.WRITE_PLANS)
    async def _create_mission_plan(
        self,
        plan_name: str,
        objectives: str,
        drone_assignments: List[Dict[str, Any]]
    ) -> int:
        """Create a new mission plan.

        This method is protected by the WRITE_PLANS authority.

        Args:
            plan_name: Name of the plan.
            objectives: Mission objectives.
            drone_assignments: List of drone assignments.

        Returns:
            The ID of the created plan.
        """
        # Extract drone IDs from assignments
        assigned_drones = [a.get("drone_id") for a in drone_assignments]

        plan_id = await self.context_manager.create_mission_plan(
            plan_name=plan_name,
            objectives=objectives,
            assigned_drones=assigned_drones,
            created_by=self.role
        )

        # Update plan status to active
        await self.context_manager.update_mission_plan(
            plan_id=plan_id,
            status="active"
        )

        logger.debug(
            f"Created mission plan #{plan_id}: {plan_name} with "
            f"{len(assigned_drones)} drones"
        )

        return plan_id

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

    async def create_initial_plan(self) -> None:
        """Create the initial mission plan.

        This is a public method that can be called during system initialization.
        """
        logger.info("Creating initial mission plan")

        # Get current drone status
        drones = await self.context_manager.get_all_drones()

        # Create basic surveillance plan
        plan_id = await self._create_mission_plan(
            plan_name="Initial Surveillance Pattern",
            objectives="Maintain surveillance coverage of known areas Alpha, Bravo, and Charlie",
            drone_assignments=[
                {"drone_id": "UAV-001", "target_area": "Area Alpha", "task_type": "surveillance", "priority": 5},
                {"drone_id": "UAV-002", "target_area": "Area Bravo", "task_type": "surveillance", "priority": 5},
                {"drone_id": "UAV-003", "target_area": "Area Charlie", "task_type": "transit", "priority": 3},
            ]
        )

        logger.info(f"Created initial mission plan #{plan_id}")

        # Notify Collection Manager
        await self.send_message(
            recipient="collection_manager",
            message_type="new_mission_plan",
            content={
                "plan_id": plan_id,
                "plan_name": "Initial Surveillance Pattern",
                "message": "Execute initial surveillance deployment"
            }
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

You just finished planning and revising missions during the operation.
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
