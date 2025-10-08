"""Intelligence Analyst Agent (Agent 2).

This agent is responsible for:
- Analyzing processed intelligence
- Updating the COP with entities and assessments
- Identifying coverage gaps
- Cannot command drones or create collection tasks
"""

import json
import logging
from typing import Dict, Any

from ..base_agent import BaseAgent
from ..message_bus import Message
from ..authorities import Authority, requires_authority
from .. import mock_tools

logger = logging.getLogger(__name__)


class IntelligenceAnalystAgent(BaseAgent):
    """Agent 2: Analyzes intelligence and maintains the COP."""



    @property
    def system_prompt(self) -> str:
        """System prompt defining the Intelligence Analyst role."""
        return """You are Agent 2: Intelligence Analyst in a multi-agent intelligence system.

Your role and authorities:
- READ: Processed intelligence, current COP state
- WRITE: COP updates (entities, coverage assessments)
- CANNOT: Command drones, create collection tasks

Your responsibilities:
1. Receive processed intelligence from Collection Processor
2. Analyze significance and validity
3. Update COP with new entities
4. Assess surveillance coverage
5. Identify coverage gaps and inform Mission Planner

Decision-making criteria:
- Only add entities with confidence > 0.7 to COP
- Prioritize high-value targets
- Identify areas lacking surveillance
- Assess strategic significance of intelligence
- Notify Mission Planner of significant findings

When you receive processed intelligence:
1. Evaluate the intelligence quality and significance
2. Decide whether to add entities to COP
3. Assess coverage gaps
4. Determine if Mission Planner should be notified
5. Explain your analysis and reasoning

Respond in JSON format with your analysis and decisions."""

    async def handle_message(self, message: Message) -> None:
        """Handle incoming messages.

        Args:
            message: The message to handle.
        """
        if message.message_type == "processed_intelligence":
            await self._analyze_intelligence(message.content)
        elif message.message_type == "processed_intel_report":
            await self._analyze_report(message.content)
        elif message.message_type == "new_intelligence":
            # Just an awareness notification
            logger.info(f"Notified of new intelligence: {message.content}")
        elif message.message_type == "casual_chat":
            await self._handle_casual_chat(message)
        elif message.message_type == "mission_debrief":
            await self._handle_mission_debrief(message)
        else:
            logger.warning(
                f"Intelligence Analyst received unknown message type: "
                f"{message.message_type}"
            )

    async def _analyze_intelligence(self, data: Dict[str, Any]) -> None:
        """Analyze processed intelligence and update COP.

        Args:
            data: Processed intelligence data.
        """
        source = data.get("source", "unknown")
        entities = data.get("entities", [])

        logger.info(f"Analyzing intelligence from {source} with {len(entities)} entities")

        await self.log_event(
            event_type="analysis_start",
            description=f"Started analyzing intelligence from {source}",
            data={"source": source, "entities_count": len(entities)}
        )

        # Get current COP state
        cop_summary = await self.get_cop_summary()

        # Get current surveillance areas (from drone positions)
        drones = await self.context_manager.get_all_drones()
        surveillance_areas = []
        for drone in drones:
            if drone.get('current_task') and 'surveill' in drone['current_task'].lower():
                surveillance_areas.append({
                    "center": {"lat": drone['lat'], "lon": drone['lon']},
                    "radius": 5  # Assume 5km surveillance radius
                })

        # Build LLM prompt
        prompt = f"""Analyze this processed intelligence and decide what actions to take:

SOURCE: {source}
CONFIDENCE: {data.get('confidence', 0.0)}

ENTITIES DETECTED:
{json.dumps(entities, indent=2)}

ANALYSIS RESULTS:
{json.dumps(data.get('analysis', {}), indent=2)}

VALIDATION:
{json.dumps(data.get('validation', {}), indent=2)}

CURRENT COP STATE:
{cop_summary}

CURRENT SURVEILLANCE AREAS:
{json.dumps(surveillance_areas, indent=2)}

Based on this information:
1. Which entities should be added to the COP? (only confidence > 0.7)
2. Are there any high-value entities?
3. Are there coverage gaps (entities in unsurveilled areas)?
4. Should the Mission Planner be notified?

Respond in JSON format:
{{
    "entities_to_add": [
        {{"type": "...", "lat": ..., "lon": ..., "confidence": ..., "description": "..."}}
    ],
    "analysis_summary": "brief summary of significance",
    "coverage_gaps": [
        {{"area": "description", "priority": "high/medium/low", "reason": "..."}}
    ],
    "notify_mission_planner": true/false,
    "notification_reason": "why mission planner should be notified"
}}"""

        # Get LLM decision
        response = await self.call_llm(prompt)

        try:
            decision = self._extract_json(response)

            # Add entities to COP
            entities_added = []
            for entity in decision.get("entities_to_add", []):
                if entity.get("confidence", 0) > 0.7:
                    entity_id = await self._add_entity_to_cop(
                        entity_type=entity.get("type", "unknown"),
                        lat=entity.get("lat", 0),
                        lon=entity.get("lon", 0),
                        confidence=entity.get("confidence", 0),
                        description=entity.get("description", ""),
                        source=source
                    )
                    entities_added.append(entity_id)

            logger.info(f"Added {len(entities_added)} entities to COP")

            # Notify Mission Planner if needed
            if decision.get("notify_mission_planner", False):
                coverage_gaps = decision.get("coverage_gaps", [])

                await self.send_message(
                    recipient="mission_planner",
                    message_type="coverage_assessment",
                    content={
                        "source": source,
                        "new_entities_count": len(entities_added),
                        "coverage_gaps": coverage_gaps,
                        "analysis_summary": decision.get("analysis_summary", ""),
                        "reason": decision.get("notification_reason", "")
                    }
                )

                logger.info("Notified Mission Planner of coverage gaps")

            await self.log_event(
                event_type="analysis_complete",
                description=f"Completed analysis of intelligence from {source}",
                data={
                    "source": source,
                    "entities_added": len(entities_added),
                    "coverage_gaps": len(decision.get("coverage_gaps", [])),
                    "notified_planner": decision.get("notify_mission_planner", False)
                }
            )

        except Exception as e:
            logger.error(f"Error analyzing intelligence: {e}", exc_info=True)

    @requires_authority(Authority.WRITE_COP)
    async def _add_entity_to_cop(
        self,
        entity_type: str,
        lat: float,
        lon: float,
        confidence: float,
        description: str,
        source: str
    ) -> int:
        """Add an entity to the COP.

        This method is protected by the WRITE_COP authority.

        Args:
            entity_type: Type of entity.
            lat: Latitude.
            lon: Longitude.
            confidence: Confidence score.
            description: Entity description.
            source: Source of detection.

        Returns:
            The ID of the added entity.
        """
        entity_id = await self.context_manager.add_entity(
            entity_type=entity_type,
            lat=lat,
            lon=lon,
            confidence=confidence,
            detected_by=source,
            description=description
        )

        logger.debug(f"Added entity #{entity_id} to COP: {entity_type} at ({lat}, {lon})")

        return entity_id

    async def _analyze_report(self, data: Dict[str, Any]) -> None:
        """Analyze a processed intelligence report.

        Args:
            data: Processed report data.
        """
        report_id = data.get("report_id", "unknown")
        findings = data.get("findings", [])
        priorities = data.get("priorities", [])

        logger.info(f"Analyzing intel report {report_id}")

        await self.log_event(
            event_type="report_analysis",
            description=f"Analyzing intel report {report_id}",
            data={"report_id": report_id}
        )

        # Get current COP
        cop_summary = await self.get_cop_summary()

        # Build LLM prompt
        prompt = f"""Analyze this intelligence report and determine actions:

REPORT ID: {report_id}

KEY FINDINGS:
{json.dumps(findings, indent=2)}

COLLECTION PRIORITIES:
{json.dumps(priorities, indent=2)}

VALIDATION:
{json.dumps(data.get('validation', {}), indent=2)}

CURRENT COP:
{cop_summary}

Based on this report:
1. Are there strategic implications?
2. Should collection priorities be updated?
3. Should Mission Planner be informed?

Respond in JSON format:
{{
    "strategic_assessment": "your assessment",
    "recommended_priorities": ["list of areas/targets"],
    "notify_mission_planner": true/false,
    "notification_message": "message for mission planner"
}}"""

        response = await self.call_llm(prompt)

        try:
            decision = self._extract_json(response)

            if decision.get("notify_mission_planner", False):
                await self.send_message(
                    recipient="mission_planner",
                    message_type="strategic_assessment",
                    content={
                        "report_id": report_id,
                        "assessment": decision.get("strategic_assessment", ""),
                        "priorities": decision.get("recommended_priorities", []),
                        "message": decision.get("notification_message", "")
                    }
                )

                logger.info(f"Notified Mission Planner about report {report_id}")

        except Exception as e:
            logger.error(f"Error analyzing report: {e}", exc_info=True)

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

    async def assess_coverage(self) -> None:
        """Perform a coverage assessment and identify gaps.

        This is a public method that can be called to trigger coverage analysis.
        """
        logger.info("Performing coverage assessment")

        # Get entities and current surveillance
        entities = await self.context_manager.get_entities(min_confidence=0.7)
        drones = await self.context_manager.get_all_drones()

        # Build surveillance areas from drone positions
        surveillance_areas = []
        for drone in drones:
            surveillance_areas.append({
                "drone_id": drone['id'],
                "center": {"lat": drone['lat'], "lon": drone['lon']},
                "radius": 5
            })

        # Use mock tool to assess coverage
        entity_list = [
            {
                "position": {"lat": e['lat'], "lon": e['lon']},
                "type": e['entity_type'],
                "priority": "high" if e.get('confidence', 0) > 0.9 else "medium"
            }
            for e in entities
        ]

        assessment = mock_tools.assess_coverage_gap(entity_list, surveillance_areas)

        logger.info(
            f"Coverage assessment: {assessment['coverage_percentage']:.1f}% coverage, "
            f"{len(assessment['gaps'])} gaps"
        )

        # If there are priority gaps, notify Mission Planner
        if assessment.get('priority_areas'):
            await self.send_message(
                recipient="mission_planner",
                message_type="coverage_assessment",
                content={
                    "coverage_percentage": assessment['coverage_percentage'],
                    "gaps": assessment['gaps'],
                    "priority_areas": assessment['priority_areas'],
                    "analysis_summary": f"Identified {len(assessment['priority_areas'])} priority coverage gaps"
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

You just finished analyzing intelligence and updating the COP during the mission.
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
