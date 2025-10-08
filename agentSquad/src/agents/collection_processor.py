"""Collection Processor Agent (Agent 1).

This agent is responsible for:
- Processing raw sensor data and intelligence reports
- Validating detections and intelligence
- Writing processed intelligence to the COP
- Cannot modify COP directly, command drones, or change plans
"""

import json
import logging
from typing import Dict, Any

from ..base_agent import BaseAgent
from ..message_bus import Message
from ..authorities import Authority, requires_authority
from .. import mock_tools

logger = logging.getLogger(__name__)


class CollectionProcessorAgent(BaseAgent):
    """Agent 1: Processes incoming sensor data and intelligence reports."""



    @property
    def system_prompt(self) -> str:
        """System prompt defining the Collection Processor role."""
        return """You are Agent 1: Collection Processor in a multi-agent intelligence system.

Your role and authorities:
- READ: Sensor data, documents, raw intelligence
- WRITE: Processed intelligence records (only)
- CANNOT: Modify COP directly, command drones, or change plans

Your responsibilities:
1. Process incoming sensor data from drones
2. Analyze and validate intelligence reports
3. Extract relevant information (entities, positions, confidence scores)
4. Publish processed intelligence for other agents

Decision-making criteria:
- Only process intelligence with confidence > 0.5
- Flag anomalies or quality issues
- Provide clear entity descriptions
- Always include source attribution

When you receive sensor data or intelligence:
1. Validate the data quality
2. Extract key information
3. Assess confidence levels
4. Decide whether to publish to other agents
5. Explain your reasoning clearly

Respond in JSON format with your analysis and decisions."""

    async def handle_message(self, message: Message) -> None:
        """Handle incoming messages.

        Args:
            message: The message to handle.
        """
        if message.message_type == "sensor_data":
            await self._process_sensor_data(message.content)
        elif message.message_type == "intel_report":
            await self._process_intel_report(message.content)
        elif message.message_type == "casual_chat":
            await self._handle_casual_chat(message)
        elif message.message_type == "mission_debrief":
            await self._handle_mission_debrief(message)
        else:
            logger.warning(
                f"Collection Processor received unknown message type: "
                f"{message.message_type}"
            )

    async def _process_sensor_data(self, data: Dict[str, Any]) -> None:
        """Process sensor data from a drone.

        Args:
            data: Sensor data dictionary.
        """
        drone_id = data.get("drone_id", "unknown")

        logger.info(f"Processing sensor data from {drone_id}")

        await self.log_event(
            event_type="processing_start",
            description=f"Started processing sensor data from {drone_id}",
            data={"drone_id": drone_id}
        )

        # Use mock tool to analyze sensor data
        sensor_data = data.get("sensor_data", {})
        analysis = mock_tools.analyze_sensor_data(sensor_data)

        # Validate the intelligence
        validation = mock_tools.validate_intelligence({
            "source": drone_id,
            "timestamp": data.get("timestamp"),
            "confidence": analysis.get("quality", 0.5),
            "data": analysis
        })

        # Get COP context
        cop_summary = await self.get_cop_summary()

        # Build LLM prompt
        prompt = f"""Analyze this sensor data and decide what action to take:

SENSOR DATA FROM: {drone_id}
Timestamp: {data.get('timestamp')}
Position: {data.get('position')}

ANALYSIS RESULTS:
{json.dumps(analysis, indent=2)}

VALIDATION RESULTS:
{json.dumps(validation, indent=2)}

CURRENT COP STATE:
{cop_summary}

Based on this information:
1. Should we publish this intelligence? (only if confidence > 0.5 and valid)
2. What entities should be reported?
3. What should other agents be informed about?

Respond in JSON format:
{{
    "should_publish": true/false,
    "reasoning": "your reasoning",
    "entities_to_report": [list of entities with type, position, confidence],
    "notify_agents": true/false,
    "notification_message": "message for other agents"
}}"""

        # Get LLM decision
        response = await self.call_llm(prompt)

        # Parse LLM response
        try:
            # Extract JSON from response
            decision = self._extract_json(response)

            if decision.get("should_publish", False):
                # Publish processed intelligence
                await self._publish_intelligence(
                    drone_id=drone_id,
                    entities=decision.get("entities_to_report", []),
                    analysis=analysis,
                    validation=validation
                )

                # Notify other agents if needed
                if decision.get("notify_agents", False):
                    await self.send_message(
                        recipient="all",
                        message_type="new_intelligence",
                        content={
                            "source": drone_id,
                            "entities_count": len(decision.get("entities_to_report", [])),
                            "message": decision.get("notification_message", "")
                        }
                    )

                logger.info(
                    f"Published intelligence from {drone_id}: "
                    f"{len(decision.get('entities_to_report', []))} entities"
                )

            else:
                logger.info(
                    f"Intelligence from {drone_id} not published: "
                    f"{decision.get('reasoning', 'no reason given')}"
                )

            await self.log_event(
                event_type="processing_complete",
                description=f"Completed processing sensor data from {drone_id}",
                data={
                    "drone_id": drone_id,
                    "published": decision.get("should_publish", False),
                    "entities_count": len(decision.get("entities_to_report", []))
                }
            )

        except Exception as e:
            logger.error(f"Error processing LLM response: {e}", exc_info=True)

    @requires_authority(Authority.WRITE_PROCESSED_INTEL)
    async def _publish_intelligence(
        self,
        drone_id: str,
        entities: list,
        analysis: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> None:
        """Publish processed intelligence.

        This method is protected by the WRITE_PROCESSED_INTEL authority.

        Args:
            drone_id: Source drone ID.
            entities: List of entities to publish.
            analysis: Analysis results.
            validation: Validation results.
        """
        # Note: This agent cannot add entities directly to COP
        # It can only publish processed intelligence for the Intelligence Analyst
        # to review and add to COP

        await self.send_message(
            recipient="intelligence_analyst",
            message_type="processed_intelligence",
            content={
                "source": drone_id,
                "entities": entities,
                "analysis": analysis,
                "validation": validation,
                "confidence": validation.get("confidence", 0.0)
            }
        )

        logger.debug(f"Published processed intelligence from {drone_id} to analyst")

    async def _process_intel_report(self, data: Dict[str, Any]) -> None:
        """Process a text-based intelligence report.

        Args:
            data: Intelligence report data.
        """
        report_id = data.get("report_id", "unknown")

        logger.info(f"Processing intelligence report {report_id}")

        await self.log_event(
            event_type="processing_start",
            description=f"Started processing intel report {report_id}",
            data={"report_id": report_id}
        )

        # Validate the report
        validation = mock_tools.validate_intelligence(data)

        # Get COP context
        cop_summary = await self.get_cop_summary()

        # Build LLM prompt
        prompt = f"""Analyze this intelligence report and extract key information:

REPORT ID: {report_id}
SOURCE: {data.get('source', 'unknown')}
TIMESTAMP: {data.get('timestamp')}

REPORT CONTENT:
{data.get('content', '')}

VALIDATION RESULTS:
{json.dumps(validation, indent=2)}

CURRENT COP STATE:
{cop_summary}

Extract and analyze:
1. Key entities mentioned (with positions if available)
2. Collection priorities
3. Target areas
4. Confidence assessment

Respond in JSON format:
{{
    "should_publish": true/false,
    "reasoning": "your reasoning",
    "key_findings": ["list of key findings"],
    "collection_priorities": ["list of priorities"],
    "notify_analyst": true/false
}}"""

        # Get LLM decision
        response = await self.call_llm(prompt)

        try:
            decision = self._extract_json(response)

            if decision.get("should_publish", False) or decision.get("notify_analyst", False):
                await self.send_message(
                    recipient="intelligence_analyst",
                    message_type="processed_intel_report",
                    content={
                        "report_id": report_id,
                        "findings": decision.get("key_findings", []),
                        "priorities": decision.get("collection_priorities", []),
                        "validation": validation
                    }
                )

                logger.info(f"Forwarded processed report {report_id} to analyst")

            await self.log_event(
                event_type="processing_complete",
                description=f"Completed processing intel report {report_id}",
                data={"report_id": report_id}
            )

        except Exception as e:
            logger.error(f"Error processing intel report: {e}", exc_info=True)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response.

        Args:
            text: Text potentially containing JSON.

        Returns:
            Parsed JSON dictionary.
        """
        # Try to find JSON in the response
        import re

        # Look for JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        # If no JSON found, return empty dict
        return {}

    async def process_file(self, file_path: str, file_type: str) -> None:
        """Process a file (sensor data or intelligence report).

        This is a public method that can be called to trigger file processing.

        Args:
            file_path: Path to the file to process.
            file_type: Type of file ("sensor_data" or "intel_report").
        """
        logger.info(f"Processing file: {file_path} (type: {file_type})")

        try:
            if file_type == "sensor_data":
                # Load JSON sensor data
                with open(file_path, 'r') as f:
                    data = json.load(f)
                await self._process_sensor_data(data)

            elif file_type == "intel_report":
                # Load text report
                with open(file_path, 'r') as f:
                    content = f.read()

                data = {
                    "report_id": file_path,
                    "source": "file",
                    "content": content,
                    "timestamp": None
                }
                await self._process_intel_report(data)

            else:
                logger.error(f"Unknown file type: {file_type}")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}", exc_info=True)

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

You just finished processing sensor data and intelligence during the mission.
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
