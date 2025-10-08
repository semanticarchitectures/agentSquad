# Multi-Agent Intelligence System

## Project Overview
This is a prototype multi-agent system for autonomous intelligence operations with drone fleet management. Four LLM-based agents collaborate through a shared Common Operating Picture (COP) to process information, maintain situational awareness, plan missions, and manage collection assets.

## System Architecture

### Core Components
1. **Context Manager** (`src/context_manager.py`)
   - SQLite-based shared memory for the COP
   - Stores drone status, entities, collection tasks, plans
   - Provides atomic updates with transaction support
   - Maintains complete message/event history for debugging

2. **Message Bus** (`src/message_bus.py`)
   - In-memory event system for agent communication
   - Supports pub/sub pattern for agent coordination
   - Lightweight for conversational latency requirements

3. **Base Agent** (`src/base_agent.py`)
   - Abstract base class defining agent interface
   - Enforces role-based authority model
   - Handles LLM API calls to Claude
   - Provides context access and message handling

4. **Four Specialized Agents** (`src/agents/`)
   - Collection Processor: Ingests and validates information
   - Intelligence Analyst: Updates COP with analyzed intelligence
   - Mission Planner: Creates and revises mission plans
   - Collection Manager: Manages drone tasking (within authority)

### Agent Authority Model

**Agent 1: Collection Processor**
- READ: Sensor data, documents, raw intelligence
- WRITE: Processed intelligence records to COP
- CANNOT: Modify COP directly, command drones, change plans

**Agent 2: Intelligence Analyst**
- READ: Processed intelligence, current COP state
- WRITE: COP updates (entities, coverage assessments)
- CANNOT: Command drones, create collection tasks

**Agent 3: Mission Planner**
- READ: COP, collection requirements, drone capabilities
- WRITE: Mission plans, plan revisions
- CANNOT: Command drones directly, override collection manager

**Agent 4: Collection Manager**
- READ: All COP data, plans, drone status
- WRITE: Collection tasks, drone commands (within parameters)
- Authority: Execute drone commands as authorized by role

## Technology Stack
- **Language**: Python 3.10+
- **LLM API**: Anthropic Claude API (claude-sonnet-4-20250514)
- **Database**: SQLite for context/COP storage
- **Messaging**: In-memory queues (asyncio or threading)
- **External Tools**: Mocked functions for prototype

## Common Operating Picture (COP) Schema

### Drones Table
```sql
CREATE TABLE drones (
    id TEXT PRIMARY KEY,
    lat REAL,
    lon REAL,
    altitude REAL,
    fuel_percent REAL,
    sensor_status TEXT,
    current_task TEXT,
    last_updated REAL
)
```

### Entities Table
```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    entity_type TEXT,
    lat REAL,
    lon REAL,
    confidence REAL,
    detected_by TEXT,
    detected_at REAL,
    description TEXT
)
```

### Collection Tasks Table
```sql
CREATE TABLE collection_tasks (
    id INTEGER PRIMARY KEY,
    drone_id TEXT,
    task_type TEXT,
    target_area TEXT,
    priority INTEGER,
    status TEXT,
    created_by TEXT,
    created_at REAL,
    FOREIGN KEY(drone_id) REFERENCES drones(id)
)
```

### Mission Plans Table
```sql
CREATE TABLE mission_plans (
    id INTEGER PRIMARY KEY,
    plan_name TEXT,
    objectives TEXT,
    assigned_drones TEXT,
    status TEXT,
    created_by TEXT,
    created_at REAL,
    updated_at REAL
)
```

## Mock Applications (Simulated External Tools)

Implement these as simple Python functions in `src/mock_tools.py`:

1. **analyze_sensor_data(data: dict) -> dict**
   - Simulates sensor data analysis
   - Returns confidence scores and detected entities

2. **estimate_drone_performance(drone_id: str, mission: dict) -> dict**
   - Simulates performance estimation
   - Returns fuel estimates, ETA, capability assessment

3. **plan_route(start: tuple, end: tuple, constraints: dict) -> list**
   - Simulates route planning
   - Returns waypoints and estimated time

4. **send_drone_command(drone_id: str, command: dict) -> bool**
   - Simulates command execution
   - Returns success/failure status

## Document Formats

**Agent 1 processes two types of inputs:**

1. **JSON files** (drone telemetry): `data/drone_telemetry/*.json`
```json
{
    "drone_id": "UAV-001",
    "timestamp": 1704067200,
    "position": {"lat": 34.0522, "lon": -118.2437, "alt": 500},
    "fuel": 85.5,
    "sensor_status": "operational",
    "sensor_data": {
        "type": "visual",
        "detections": [...]
    }
}
```

2. **Text files** (intelligence reports): `data/intel_reports/*.txt`
   - Plain text mission briefings
   - Target area descriptions
   - Collection priorities

## Test Scenario

**Initial State:**
- 3 drones (UAV-001, UAV-002, UAV-003) operational
- UAV-001: Surveilling Area Alpha (34.05°N, 118.24°W)
- UAV-002: Surveilling Area Bravo (34.08°N, 118.30°W)
- UAV-003: In transit to Area Charlie
- COP shows 2 known entities in Area Alpha

**Trigger Event:**
Agent 1 receives sensor data from UAV-002 detecting a new high-value entity in Area Delta (34.10°N, 118.35°W) - an area not currently under surveillance.

**Expected Agent Behavior:**

1. **Agent 1 (Collection Processor):**
   - Processes the sensor data
   - Validates the detection (confidence > 0.7)
   - Writes processed intelligence to COP

2. **Agent 2 (Intelligence Analyst):**
   - Reads new intelligence
   - Analyzes significance (high-value entity in unsurveilled area)
   - Updates COP with new entity
   - Identifies coverage gap in Area Delta

3. **Agent 3 (Mission Planner):**
   - Detects COP change (new high-value entity + coverage gap)
   - Evaluates current mission plan
   - Determines plan needs revision
   - Creates revised plan: redirect UAV-003 to Area Delta

4. **Agent 4 (Collection Manager):**
   - Reads revised mission plan
   - Checks UAV-003 status and capabilities
   - Determines it has authority to retask UAV-003
   - Issues collection task to UAV-003 for Area Delta surveillance
   - Updates COP with new task assignment

## Implementation Requirements

### Code Quality
- Use type hints for all function parameters and returns
- Write docstrings in Google style for all classes and functions
- Follow PEP 8 style guidelines
- Use async/await for agent operations where appropriate

### Error Handling
- All LLM API calls must have retry logic (exponential backoff)
- Database operations must use transactions
- Agents must handle malformed inputs gracefully
- Log all agent decisions and actions

### Authority Enforcement
- Implement a permissions decorator: `@requires_authority("command_drones")`
- Raise `UnauthorizedActionError` if agent attempts unauthorized action
- Log all authority checks for audit trail

### Testing
- Create unit tests for each component
- Create integration test that runs the full test scenario
- Mock LLM API calls for testing (use predefined responses)

### Observability
- Log all agent-to-agent messages
- Log all COP updates with timestamps
- Create a simple CLI tool to view COP state: `python -m src.cli show-cop`
- Create a CLI tool to view agent message history: `python -m src.cli show-messages`

## Project Structure
```
multi-agent-intelligence/
├── .claude/
│   ├── CLAUDE.md              (this file)
│   └── settings.json
├── src/
│   ├── __init__.py
│   ├── context_manager.py     # SQLite COP management
│   ├── message_bus.py         # Event system
│   ├── base_agent.py          # Abstract agent class
│   ├── mock_tools.py          # Simulated external applications
│   ├── authorities.py         # Permission system
│   ├── cli.py                 # Command-line tools
│   └── agents/
│       ├── __init__.py
│       ├── collection_processor.py
│       ├── intelligence_analyst.py
│       ├── mission_planner.py
│       └── collection_manager.py
├── data/
│   ├── drone_telemetry/       # Sample JSON files
│   └── intel_reports/         # Sample text files
├── tests/
│   ├── test_context_manager.py
│   ├── test_agents.py
│   └── test_integration.py
├── main.py                    # Orchestrator/entry point
├── requirements.txt
└── README.md
```

## Key Development Notes

### LLM Prompt Engineering for Agents
Each agent needs a carefully crafted system prompt that:
- Clearly defines its role and authorities
- Specifies its decision-making criteria
- Provides context on how to use available tools
- Emphasizes when to act vs. when to wait for more information

### Context Management Strategy
- Agents should read relevant COP state before making decisions
- Update COP atomically (use database transactions)
- Include "last_updated" timestamps on all entities
- Maintain an audit log of who changed what and when

### Message Flow
1. Agent detects trigger (new data, COP change, message from another agent)
2. Agent reads current context from COP
3. Agent calls LLM with: role prompt + current context + trigger
4. Agent parses LLM response for actions
5. Agent executes actions (within authority) and updates COP
6. Agent publishes message to message bus for other agents

### Performance Targets
- Agent decision latency: < 5 seconds (conversational)
- COP query latency: < 100ms
- Support 10+ messages/second between agents
- SQLite sufficient for prototype (single machine, 4 agents)

## Next Steps for Implementation

1. Set up project structure and install dependencies
2. Implement ContextManager with COP schema
3. Implement MessageBus for agent communication
4. Implement BaseAgent with authority checking
5. Implement mock tools
6. Implement each of the 4 specialized agents
7. Create sample data files for test scenario
8. Implement main orchestrator
9. Create CLI tools for observability
10. Run integration test with test scenario
11. Document results and agent behaviors

## Important Reminders

- This is a PROTOTYPE - prioritize working functionality over production robustness
- Mock external tools - don't build real drone interfaces
- Focus on demonstrating the multi-agent coordination pattern
- Agents should explain their reasoning in logs (helps debug LLM decisions)
- Keep LLM prompts concise but provide necessary context
- Test with the scenario above before adding complexity
