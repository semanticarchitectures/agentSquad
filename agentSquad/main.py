"""Main orchestrator for the multi-agent intelligence system.

This module initializes all components and runs the test scenario.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from src.context_manager import ContextManager
from src.message_bus import MessageBus
from src.agents.collection_processor import CollectionProcessorAgent
from src.agents.intelligence_analyst import IntelligenceAnalystAgent
from src.agents.mission_planner import MissionPlannerAgent
from src.agents.collection_manager import CollectionManagerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_agent_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Orchestrates the multi-agent intelligence system."""

    def __init__(self, db_path: str = "cop.db"):
        """Initialize the orchestrator.

        Args:
            db_path: Path to the COP database.
        """
        self.db_path = db_path
        self.context_manager = None
        self.message_bus = None
        self.agents = {}

    async def initialize(self) -> None:
        """Initialize all system components."""
        logger.info("Initializing multi-agent system...")

        # Initialize Context Manager
        self.context_manager = ContextManager(self.db_path)
        await self.context_manager.initialize()
        logger.info("Context Manager initialized")

        # Initialize Message Bus
        self.message_bus = MessageBus()
        logger.info("Message Bus initialized")

        # Create agents
        self.agents = {
            "collection_processor": CollectionProcessorAgent(
                role="collection_processor",
                context_manager=self.context_manager,
                message_bus=self.message_bus
            ),
            "intelligence_analyst": IntelligenceAnalystAgent(
                role="intelligence_analyst",
                context_manager=self.context_manager,
                message_bus=self.message_bus
            ),
            "mission_planner": MissionPlannerAgent(
                role="mission_planner",
                context_manager=self.context_manager,
                message_bus=self.message_bus
            ),
            "collection_manager": CollectionManagerAgent(
                role="collection_manager",
                context_manager=self.context_manager,
                message_bus=self.message_bus
            ),
        }

        logger.info(f"Created {len(self.agents)} agents")

        # Subscribe agents to relevant message types
        self.message_bus.subscribe("intelligence_analyst", "new_intelligence")
        self.message_bus.subscribe("intelligence_analyst", "processed_intelligence")
        self.message_bus.subscribe("intelligence_analyst", "processed_intel_report")

        self.message_bus.subscribe("mission_planner", "coverage_assessment")
        self.message_bus.subscribe("mission_planner", "strategic_assessment")
        self.message_bus.subscribe("mission_planner", "drone_status_alert")

        self.message_bus.subscribe("collection_manager", "new_mission_plan")

        logger.info("Agent subscriptions configured")

    async def start_agents(self) -> None:
        """Start all agents."""
        logger.info("Starting all agents...")

        for role, agent in self.agents.items():
            await agent.start()
            logger.info(f"Started agent: {role}")

    async def stop_agents(self) -> None:
        """Stop all agents."""
        logger.info("Stopping all agents...")

        for role, agent in self.agents.items():
            await agent.stop()
            logger.info(f"Stopped agent: {role}")

    async def setup_initial_state(self) -> None:
        """Set up the initial COP state for the test scenario."""
        logger.info("Setting up initial COP state...")

        # Add initial drones
        await self.context_manager.update_drone(
            drone_id="UAV-001",
            lat=34.0522,
            lon=-118.2437,
            altitude=450,
            fuel_percent=85.5,
            sensor_status="operational",
            current_task="Surveilling Area Alpha"
        )

        await self.context_manager.update_drone(
            drone_id="UAV-002",
            lat=34.08,
            lon=-118.30,
            altitude=500,
            fuel_percent=82.5,
            sensor_status="operational",
            current_task="Surveilling Area Bravo"
        )

        await self.context_manager.update_drone(
            drone_id="UAV-003",
            lat=34.065,
            lon=-118.255,
            altitude=400,
            fuel_percent=68.5,
            sensor_status="operational",
            current_task="In transit to Area Charlie"
        )

        # Add initial entities in Area Alpha
        await self.context_manager.add_entity(
            entity_type="structure",
            lat=34.053,
            lon=-118.244,
            confidence=0.85,
            detected_by="UAV-001",
            description="Known facility in Area Alpha"
        )

        await self.context_manager.add_entity(
            entity_type="vehicle",
            lat=34.054,
            lon=-118.245,
            confidence=0.75,
            detected_by="UAV-001",
            description="Mobile unit in Area Alpha"
        )

        logger.info("Initial COP state configured")

    async def run_introduction_phase(self) -> None:
        """Run the casual introduction phase."""
        logger.info("=" * 80)
        logger.info("SQUAD INTRODUCTION PHASE")
        logger.info("=" * 80)

        # Give agents time to initialize
        await asyncio.sleep(2)

        logger.info("\n🎭 Agents introducing themselves in casual mode...\n")

        # Have each agent introduce themselves with some delay
        agent_names = list(self.agents.keys())
        for i, agent_name in enumerate(agent_names):
            agent = self.agents[agent_name]
            await agent.introduce_self()
            await asyncio.sleep(3)  # Stagger introductions

        # Let them chat for a bit
        logger.info("\n💬 Letting agents chat casually...")
        await asyncio.sleep(8)

        logger.info("\n📋 Mission briefing starting - switching to professional mode...\n")

        # Switch all agents to professional mode
        for agent in self.agents.values():
            agent.set_mode("professional")

        await asyncio.sleep(2)

    async def run_test_scenario(self) -> None:
        """Run the test scenario from CLAUDE.md."""
        logger.info("=" * 80)
        logger.info("STARTING OPERATIONAL TEST SCENARIO")
        logger.info("=" * 80)

        # Trigger Event: UAV-002 detects new high-value entity in Area Delta
        logger.info("\n>>> TRIGGER EVENT: UAV-002 detects high-value entity in Area Delta <<<\n")

        # Process the sensor data file
        sensor_data_file = "data/drone_telemetry/uav_002_detection.json"
        processor = self.agents["collection_processor"]
        await processor.process_file(sensor_data_file, "sensor_data")

        # Wait for agent chain reaction
        logger.info("\nWaiting for agents to process and coordinate...")
        await asyncio.sleep(10)

        # Also process the intelligence report
        logger.info("\n>>> Processing intelligence report <<<\n")
        intel_file = "data/intel_reports/mission_brief_001.txt"
        await processor.process_file(intel_file, "intel_report")

        # Wait for additional processing
        await asyncio.sleep(10)

        logger.info("\n" + "=" * 80)
        logger.info("TEST SCENARIO COMPLETE")
        logger.info("=" * 80)

    async def run_relaxed_phase(self) -> None:
        """Run the post-mission relaxed chat phase."""
        logger.info("\n" + "=" * 80)
        logger.info("POST-MISSION RELAXED PHASE")
        logger.info("=" * 80)

        # Switch all agents to relaxed mode
        logger.info("\n🎉 Mission complete - agents switching to relaxed mode...\n")
        for agent in self.agents.values():
            agent.set_mode("relaxed")

        # Let them chat about the mission
        await asyncio.sleep(3)

        # Send a mission debrief prompt to get them talking
        await self.message_bus.send(
            sender="system",
            recipient="all",
            message_type="mission_debrief",
            content={
                "message": "Mission complete! How did everyone feel about that operation? Any thoughts on how the team performed?"
            }
        )

        logger.info("💬 Agents debriefing in relaxed mode...")
        await asyncio.sleep(8)

    async def shutdown(self) -> None:
        """Shutdown the system."""
        logger.info("Shutting down system...")

        await self.stop_agents()

        if self.context_manager:
            await self.context_manager.close()

        logger.info("System shutdown complete")


async def main():
    """Main entry point."""
    # Check for ANTHROPIC_API_KEY
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Create orchestrator
    orchestrator = MultiAgentOrchestrator()

    try:
        # Initialize system
        await orchestrator.initialize()

        # Set up initial state
        await orchestrator.setup_initial_state()

        # Start agents
        await orchestrator.start_agents()

        # Phase 1: Casual introductions
        await orchestrator.run_introduction_phase()

        # Phase 2: Professional mission execution
        await orchestrator.run_test_scenario()

        # Phase 3: Relaxed post-mission chat
        await orchestrator.run_relaxed_phase()

        # Show final results
        logger.info("\nSystem running. Check logs and COP for results.")
        logger.info("Use 'python -m src.cli show-cop' to view COP")
        logger.info("Use 'python -m src.cli show-messages' to view messages")
        logger.info("Use 'python -m src.cli show-events' to view events\n")

        # Run for a bit more to see final interactions
        await asyncio.sleep(15)

    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal")

    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)

    finally:
        await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
