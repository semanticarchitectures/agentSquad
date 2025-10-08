# Multi-Agent Intelligence System

A prototype demonstrating autonomous intelligence operations using four collaborating LLM agents managing a drone fleet through a shared Common Operating Picture (COP).

## Quick Start

### Prerequisites
- Python 3.10+
- Anthropic API key
- Claude Code CLI installed

### Setup

1. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set your API key:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

4. **Verify setup:**
```bash
python3 verify_setup.py
```

See [QUICKSTART.md](QUICKSTART.md) for detailed installation and usage instructions.

## System Architecture

Four autonomous agents collaborate through a shared database (Common Operating Picture):

- **Agent 1 (Collection Processor)**: Ingests and validates sensor data
- **Agent 2 (Intelligence Analyst)**: Updates situational awareness model
- **Agent 3 (Mission Planner)**: Creates and revises mission plans
- **Agent 4 (Collection Manager)**: Manages drone tasking operations

Each agent has specific authorities enforced by the system.

## Test Scenario

The system demonstrates autonomous coordination:

1. New sensor data arrives showing high-value entity in unmonitored area
2. Agent 1 processes and validates the information
3. Agent 2 updates the COP and identifies coverage gap
4. Agent 3 revises mission plan to address the gap
5. Agent 4 retasks available drone to the new area

All coordination happens autonomously with full audit trail.

## Usage

### Running the Test Scenario
```bash
# Install dependencies first
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY='your-api-key-here'

# Run the main scenario
python main.py
```

The system will:
1. Initialize all 4 agents
2. Set up initial COP state with 3 drones
3. Process sensor data from UAV-002 detecting entity in Area Delta
4. Demonstrate autonomous agent coordination
5. Run for 30 seconds showing agent activity

### Inspecting System State
```bash
# View current Common Operating Picture
python -m src.cli show-cop

# View agent message history
python -m src.cli show-messages

# View event log (all agents)
python -m src.cli show-events

# Filter by specific agent
python -m src.cli show-events --agent intelligence_analyst

# Specify different database
python -m src.cli show-cop --db cop.db
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=src
```

## Project Structure

```
multi-agent-intelligence/
├── .claude/
│   ├── CLAUDE.md              # System documentation for Claude Code
│   └── settings.json          # Project configuration
├── src/
│   ├── context_manager.py     # SQLite-based COP management
│   ├── message_bus.py         # Agent communication system
│   ├── base_agent.py          # Base agent class with authorities
│   ├── mock_tools.py          # Simulated external applications
│   ├── authorities.py         # Permission enforcement
│   ├── cli.py                 # Command-line observability tools
│   └── agents/
│       ├── collection_processor.py
│       ├── intelligence_analyst.py
│       ├── mission_planner.py
│       └── collection_manager.py
├── data/
│   ├── drone_telemetry/       # Sample JSON sensor data
│   └── intel_reports/         # Sample text reports
├── tests/
│   ├── test_context_manager.py
│   ├── test_agents.py
│   └── test_integration.py
├── main.py                    # System orchestrator
├── requirements.txt
├── PROJECT_SPEC.md           # Detailed specifications
└── README.md                 # This file
```

## Key Features

- **Role-Based Authority**: Each agent has specific permissions enforced by decorators
- **Shared Context**: SQLite-based Common Operating Picture for agent coordination
- **Event-Driven**: Agents react to COP changes and messages from other agents
- **Observable**: Complete audit trail with CLI inspection tools
- **Testable**: Mock external tools for deterministic testing

## Development Guide

### Adding New Agents

1. Extend `BaseAgent` class
2. Define agent authorities in constructor
3. Implement `process_message()` method
4. Add agent-specific LLM prompts
5. Register with message bus

### Adding New Tools

1. Add mock function in `src/mock_tools.py`
2. Update relevant agent to call the tool
3. Add tool documentation to agent prompts

### Modifying COP Schema

1. Update schema in `src/context_manager.py`
2. Update data models in `PROJECT_SPEC.md`
3. Regenerate database with migration

## Configuration

Configuration is in `.claude/settings.json`:
- Agent authorities and permissions
- Environment variables
- Post-processing hooks (e.g., code formatting)

## Observability

All agent actions are logged:
- Decision reasoning
- COP updates
- Authority checks
- Messages sent/received

Use CLI tools to inspect system state at any time.

## Limitations

This is a **prototype** with intentional simplifications:
- Mock external applications (not real drone interfaces)
- Single-machine deployment
- SQLite storage (not distributed database)
- No real-time streaming (batch processing)
- Simplified authority model

## Future Enhancements

- Real drone integration via MCP connectors
- Distributed deployment with proper message queuing
- Real-time streaming sensor data
- Advanced planning algorithms
- Web-based visualization dashboard
- Multi-user collaboration features

## License

[Your license here]

## Contributing

[Your contribution guidelines here]

## Support

[Your support information here]