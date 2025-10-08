#!/usr/bin/env python3
"""
Demo script to showcase the new personality feature without requiring API keys.
This demonstrates the agent personality switching functionality.
"""

import asyncio
import logging
from src.agents.collection_processor import CollectionProcessorAgent
from src.agents.intelligence_analyst import IntelligenceAnalystAgent
from src.agents.mission_planner import MissionPlannerAgent
from src.agents.collection_manager import CollectionManagerAgent
from src.context_manager import ContextManager
from src.message_bus import MessageBus

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockAgent:
    """Mock agent that demonstrates personality features without API calls."""
    
    def __init__(self, agent_class, role):
        self.agent_class = agent_class
        self.role = role
        self.mode = "casual"
        self.has_introduced = False
        
        # Create a mock instance to get personality info
        self.mock_instance = agent_class.__new__(agent_class)
        
    @property
    def agent_callsign(self):
        return self.mock_instance.agent_callsign
        
    @property
    def casual_personality(self):
        return self.mock_instance.casual_personality
        
    def set_mode(self, mode):
        self.mode = mode
        logger.info(f"🎭 {self.agent_callsign} switched to {mode} mode")
        
    async def introduce_self(self):
        """Mock introduction without API call."""
        if self.has_introduced:
            return
            
        self.has_introduced = True
        
        # Mock introduction based on personality
        introductions = {
            "DataHawk": "Hey everyone! DataHawk here - I'll be handling all your sensor data and making sure the numbers add up. Fair warning: I'm a bit of a perfectionist when it comes to data quality!",
            "Overwatch": "Hello team, Overwatch reporting in. I'll be your intelligence analyst today, keeping track of the big picture and making sure we don't miss any important connections.",
            "Chessmaster": "Greetings squad! Chessmaster at your service. I'll be planning our moves and thinking several steps ahead. Ready to play some tactical chess with real stakes!",
            "Skywatch": "What's up team? Skywatch here - your friendly neighborhood drone commander. My birds are fueled up and ready to fly. Let's get this show in the air!"
        }
        
        intro = introductions.get(self.agent_callsign, f"Hi, I'm {self.agent_callsign}")
        logger.info(f"🗣️  {self.agent_callsign}: {intro}")
        
    async def mock_professional_communication(self):
        """Mock professional military communication."""
        professional_messages = {
            "DataHawk": "Collection Processor ready. All sensor feeds nominal. Standing by for data processing tasks.",
            "Overwatch": "Intelligence Analyst online. COP updated and monitoring for new intelligence. Ready to assess threats.",
            "Chessmaster": "Mission Planner operational. Current tactical situation assessed. Awaiting coverage gaps for planning.",
            "Skywatch": "Collection Manager standing by. All drone assets ready for deployment. Awaiting mission parameters."
        }
        
        msg = professional_messages.get(self.agent_callsign, f"{self.agent_callsign} ready")
        logger.info(f"📋 {self.agent_callsign}: {msg}")
        
    async def mock_relaxed_debrief(self):
        """Mock relaxed post-mission chat."""
        relaxed_messages = {
            "DataHawk": "Well, that was a solid run! The data quality was actually pretty good this time - only had to clean up a few sensor glitches. Nice work everyone!",
            "Overwatch": "Good mission, team. The intelligence picture came together nicely. I especially liked how quickly we identified those coverage gaps.",
            "Chessmaster": "Excellent execution! The plan adapted well to the changing situation. That's what I call a winning strategy. Ready for the next round?",
            "Skywatch": "Sweet! My drones performed flawlessly - no hiccups, perfect coordination. That's how we get things done! Who's buying the first round?"
        }
        
        msg = relaxed_messages.get(self.agent_callsign, f"{self.agent_callsign} - good job team!")
        logger.info(f"🍻 {self.agent_callsign}: {msg}")

async def demo_personality_feature():
    """Demonstrate the personality feature."""
    
    logger.info("=" * 80)
    logger.info("🎭 AGENT PERSONALITY FEATURE DEMONSTRATION")
    logger.info("=" * 80)
    
    # Create mock agents
    agents = [
        MockAgent(CollectionProcessorAgent, "collection_processor"),
        MockAgent(IntelligenceAnalystAgent, "intelligence_analyst"), 
        MockAgent(MissionPlannerAgent, "mission_planner"),
        MockAgent(CollectionManagerAgent, "collection_manager")
    ]
    
    # Phase 1: Casual Introductions
    logger.info("\n🎭 PHASE 1: CASUAL INTRODUCTIONS")
    logger.info("-" * 50)
    logger.info("Agents introducing themselves in casual mode...")
    
    for agent in agents:
        await agent.introduce_self()
        await asyncio.sleep(1)
    
    # Show personality descriptions
    logger.info("\n📝 AGENT PERSONALITIES:")
    logger.info("-" * 50)
    for agent in agents:
        logger.info(f"\n{agent.agent_callsign} ({agent.role}):")
        logger.info(f"  {agent.casual_personality}")
    
    await asyncio.sleep(2)
    
    # Phase 2: Professional Mode
    logger.info("\n📋 PHASE 2: PROFESSIONAL MILITARY MODE")
    logger.info("-" * 50)
    logger.info("Mission briefing starting - switching to professional mode...")
    
    for agent in agents:
        agent.set_mode("professional")
        
    await asyncio.sleep(1)
    
    logger.info("\nProfessional communications:")
    for agent in agents:
        await agent.mock_professional_communication()
        await asyncio.sleep(0.5)
    
    await asyncio.sleep(2)
    
    # Phase 3: Relaxed Post-Mission
    logger.info("\n🎉 PHASE 3: RELAXED POST-MISSION CHAT")
    logger.info("-" * 50)
    logger.info("Mission complete - switching to relaxed mode...")
    
    for agent in agents:
        agent.set_mode("relaxed")
        
    await asyncio.sleep(1)
    
    logger.info("\nPost-mission debrief:")
    for agent in agents:
        await agent.mock_relaxed_debrief()
        await asyncio.sleep(0.5)
    
    logger.info("\n" + "=" * 80)
    logger.info("🎭 PERSONALITY FEATURE DEMONSTRATION COMPLETE")
    logger.info("=" * 80)
    logger.info("\nKey Features Demonstrated:")
    logger.info("✅ Agent callsigns and unique personalities")
    logger.info("✅ Casual introduction phase")
    logger.info("✅ Professional military communication mode")
    logger.info("✅ Relaxed post-mission chat mode")
    logger.info("✅ Dynamic mode switching")
    logger.info("\nTo see this in action with real LLM calls:")
    logger.info("1. Set ANTHROPIC_API_KEY environment variable")
    logger.info("2. Run: python main.py --scenario test")

if __name__ == "__main__":
    asyncio.run(demo_personality_feature())
