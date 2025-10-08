# Quick Start Guide

## Prerequisites

- Python 3.10 or higher
- Anthropic API key

## Installation Steps

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set API Key

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 4. Verify Setup

```bash
python3 verify_setup.py
```

You should see:
```
✅ All checks passed! System is ready to run.
```

## Running the System

### Run the Test Scenario

```bash
python3 main.py
```

This will:
1. Initialize all 4 agents
2. Set up the initial Common Operating Picture (COP) with 3 drones
3. Process sensor data showing a new entity in Area Delta
4. Demonstrate autonomous agent coordination
5. Run for 30 seconds, then shutdown

### Monitor the Output

While the system runs, you'll see:
- Agent initialization messages
- LLM decision-making (agents using Claude to reason)
- Message passing between agents
- COP updates
- Authority checks
- Event logging

### Check the Logs

```bash
# View the log file
tail -f multi_agent_system.log
```

## Inspecting System State

After running (or during), use these CLI tools:

### View Common Operating Picture

```bash
python3 -m src.cli show-cop
```

Shows:
- All drones and their status
- Detected entities
- Collection tasks
- Mission plans

### View Message History

```bash
# All messages
python3 -m src.cli show-messages

# Last 20 messages
python3 -m src.cli show-messages 20

# Messages from specific agent
python3 -m src.cli show-messages --sender collection_processor
```

### View Event Log

```bash
# All events
python3 -m src.cli show-events

# Last 30 events
python3 -m src.cli show-events 30

# Events from specific agent
python3 -m src.cli show-events --agent intelligence_analyst
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## What to Expect

### The Test Scenario Flow

1. **Initial State**: 3 drones surveilling different areas
   - UAV-001: Area Alpha
   - UAV-002: Area Bravo
   - UAV-003: In transit to Area Charlie

2. **Trigger Event**: UAV-002 detects high-value entity in Area Delta (unsurveilled)

3. **Agent Coordination**:
   - **Collection Processor** processes sensor data, validates, publishes to Intelligence Analyst
   - **Intelligence Analyst** adds entity to COP, identifies coverage gap, notifies Mission Planner
   - **Mission Planner** creates revised plan to cover Area Delta, notifies Collection Manager
   - **Collection Manager** checks UAV-003 capabilities, issues command to redirect to Area Delta

4. **Result**: Autonomous mission revision without human intervention

### Files Created

After running:
- `cop.db` - SQLite database with the Common Operating Picture
- `multi_agent_system.log` - Complete system log

### Example Output

```
2024-01-01 12:00:00 - __main__ - INFO - Initializing multi-agent system...
2024-01-01 12:00:00 - src.context_manager - INFO - Context Manager initialized
2024-01-01 12:00:00 - src.message_bus - INFO - Message bus initialized
2024-01-01 12:00:01 - src.base_agent - INFO - Agent collection_processor initialized with 3 authorities
...
2024-01-01 12:00:05 - src.agents.collection_processor - INFO - Processing sensor data from UAV-002
2024-01-01 12:00:07 - src.agents.intelligence_analyst - INFO - Added 1 entities to COP
2024-01-01 12:00:08 - src.agents.mission_planner - INFO - Created mission plan #2
2024-01-01 12:00:09 - src.agents.collection_manager - INFO - Successfully sent command to UAV-003: navigate
```

## Troubleshooting

### API Key Not Set

```
Error: ANTHROPIC_API_KEY environment variable not set
```

**Solution**: Set your API key:
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

### Dependencies Missing

```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Permission Errors

```
UnauthorizedActionError: Agent 'collection_processor' lacks required authority
```

**Expected behavior** - This demonstrates the authority system working correctly!

## Next Steps

- Modify the test scenario in `main.py`
- Add new agents by extending `BaseAgent`
- Create custom sensor data files in `data/drone_telemetry/`
- Write intelligence reports in `data/intel_reports/`
- Explore the agent decision-making by reading the logs

## Cleanup

```bash
# Deactivate virtual environment
deactivate

# Remove database and logs (optional)
rm cop.db multi_agent_system.log
```

## Support

For issues or questions, refer to:
- `README.md` - Full documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `.claude/CLAUDE.md` - System specifications
