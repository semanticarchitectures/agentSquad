# Agent Personality Feature

## Overview

The multi-agent intelligence system now includes a comprehensive personality feature that gives each agent a unique character and enables dynamic communication mode switching. This feature adds human-like interaction patterns while maintaining professional operational capabilities.

## Key Features

### 1. Agent Callsigns and Personalities

Each agent has been given a unique callsign and personality:

- **DataHawk** (Collection Processor): Methodical data analyst with dry humor and perfectionist tendencies
- **Overwatch** (Intelligence Analyst): Calm strategic thinker with excellent memory and big-picture perspective  
- **Chessmaster** (Mission Planner): Tactical genius who thinks several moves ahead and uses strategy metaphors
- **Skywatch** (Collection Manager): Practical drone operator with pilot confidence and action-oriented approach

### 2. Communication Modes

The system supports three distinct communication modes:

#### Casual Mode
- Used during initial introductions and informal interactions
- Agents show their personalities and speak in relaxed, friendly manner
- Includes humor, personal quirks, and informal language

#### Professional Mode  
- Activated during mission operations
- Military-style communication with clear, concise language
- Formal protocols and professional terminology
- Agents address each other by callsigns

#### Relaxed Mode
- Used for post-mission debriefing and casual chat
- Combines personality with mission reflection
- Informal but mission-focused discussions

### 3. Dynamic Mode Switching

The system automatically manages mode transitions:

1. **Startup**: Agents begin in casual mode and introduce themselves
2. **Mission Brief**: All agents switch to professional mode for operations
3. **Post-Mission**: Agents switch to relaxed mode for debriefing

## Implementation Details

### BaseAgent Enhancements

New abstract methods added to `BaseAgent`:
- `agent_callsign`: Returns the agent's unique callsign
- `casual_personality`: Returns personality description for casual interactions

New functionality:
- `set_mode(mode)`: Changes communication mode
- `introduce_self()`: Handles casual self-introductions
- `call_llm()` enhanced with `use_personality` parameter for mode-aware prompting

### Agent-Specific Implementations

Each agent implements:
- Unique callsign and personality traits
- Handlers for `casual_chat` and `mission_debrief` message types
- Mode-appropriate response generation

### Orchestrator Integration

The main orchestrator now runs three phases:
1. `run_introduction_phase()`: Casual introductions
2. `run_test_scenario()`: Professional mission execution  
3. `run_relaxed_phase()`: Post-mission casual chat

## Usage

### Running the Full System

```bash
# Set API key
export ANTHROPIC_API_KEY='your-key-here'

# Run with personality features
python main.py --scenario test
```

### Demo Mode (No API Key Required)

```bash
# Run personality demonstration
python demo_personality.py
```

## Example Interactions

### Casual Introduction
```
DataHawk: Hey everyone! DataHawk here - I'll be handling all your sensor data and making sure the numbers add up. Fair warning: I'm a bit of a perfectionist when it comes to data quality!
```

### Professional Communication
```
DataHawk: Collection Processor ready. All sensor feeds nominal. Standing by for data processing tasks.
```

### Relaxed Debrief
```
DataHawk: Well, that was a solid run! The data quality was actually pretty good this time - only had to clean up a few sensor glitches. Nice work everyone!
```

## Technical Architecture

### Message Types
- `introduction`: Agent self-introductions
- `casual_chat`: Informal agent-to-agent communication
- `mission_debrief`: Post-mission discussion prompts

### Mode Management
- Each agent tracks current mode (`casual`, `professional`, `relaxed`)
- System prompts adapt based on current mode
- Temperature and response style adjust per mode

### Personality Integration
- Personality descriptions guide LLM behavior in casual/relaxed modes
- Professional mode overrides personality for military communication
- Consistent character traits maintained across all modes

## Benefits

1. **Enhanced User Experience**: More engaging and human-like agent interactions
2. **Realistic Military Simulation**: Proper communication protocols during operations
3. **Team Dynamics**: Agents feel like a cohesive squad with individual personalities
4. **Operational Clarity**: Clear distinction between casual and professional communications
5. **Demonstration Value**: Showcases advanced multi-agent coordination capabilities

## Future Enhancements

Potential extensions to the personality system:
- Agent-specific response patterns and vocabulary
- Relationship dynamics between agents
- Stress/fatigue effects on communication style
- Customizable personality profiles
- Voice synthesis with personality-matched characteristics
