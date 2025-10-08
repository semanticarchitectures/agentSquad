# Quick Setup Guide for Claude Code

## Step-by-Step Instructions

### 1. Create Your Project Directory
```bash
mkdir multi-agent-intelligence
cd multi-agent-intelligence
```

### 2. Copy These Files

Create the following directory structure and copy the artifact contents:

```bash
# Create directories
mkdir -p .claude data/drone_telemetry data/intel_reports

# Copy these files from the artifacts:
# - .claude/CLAUDE.md
# - .claude/settings.json  
# - PROJECT_SPEC.md
# - requirements.txt
# - README.md
# - data/drone_telemetry/sample_trigger_event.json
```

**File locations:**
```
multi-agent-intelligence/
├── .claude/
│   ├── CLAUDE.md              ← Copy artifact "CLAUDE.md"
│   └── settings.json          ← Copy artifact "settings.json"
├── data/
│   └── drone_telemetry/
│       └── sample_trigger_event.json  ← Copy artifact "sample_trigger_event.json"
├── PROJECT_SPEC.md            ← Copy artifact "PROJECT_SPEC.md"
├── requirements.txt           ← Copy artifact "requirements.txt"
├── README.md                  ← Copy artifact "README.md"
└── SETUP_GUIDE.md            ← This file
```

### 3. Set Your Anthropic API Key
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 4. Initialize Claude Code
```bash
cd multi-agent-intelligence
claude
```

### 5. Start Building

When Claude Code starts, say:

```
Please implement this multi-agent intelligence system according to CLAUDE.md.

Follow this implementation order:
1. Create the project structure
2. Implement ContextManager (SQLite COP storage)
3. Implement MessageBus (in-memory event system)
4. Implement BaseAgent with authority enforcement
5. Implement mock_tools.py
6. Implement the 4 specialized agents
7. Implement main.py orchestrator
8. Create CLI tools for observability
9. Create the integration test with the test scenario
10. Add sample data files

Use the test scenario described in CLAUDE.md to validate the system works correctly.
```

## What Claude Code Will Build

Claude Code will create approximately **15-20 Python files** implementing:

### Core Infrastructure
- `src/context_manager.py` - SQLite database for the Common Operating Picture
- `src/message_bus.py` - Event system for agent communication
- `src/base_agent.py` - Abstract base class with authority enforcement
- `src/authorities.py` - Permission decorators and enforcement
- `src/mock_tools.py` - Simulated external applications

### The Four Agents
- `src/agents/collection_processor.py` - Processes incoming sensor data
- `src/agents/intelligence_analyst.py` - Updates situational awareness
- `src/agents/mission_planner.py` - Creates mission plans
- `src/agents/collection_manager.py` - Manages drone tasking

### Testing & Observability
- `tests/test_context_manager.py` - Unit tests for database
- `tests/test_agents.py` - Unit tests for each agent
- `tests/test_integration.py` - Full scenario test
- `src/cli.py` - Command-line tools to inspect system state
- `main.py` - Orchestrator that runs the system

### Sample Data
- `data/drone_telemetry/*.json` - Sample sensor data
- `data/intel_reports/*.txt` - Sample intelligence reports

## Expected Timeline

With Claude Code, implementation should take:
- **Phase 1 (Foundation)**: 30-45 minutes
- **Phase 2 (Agents)**: 45-60 minutes  
- **Phase 3 (Testing)**: 30 minutes
- **Total**: ~2-3 hours of Claude Code interaction

## Verification Steps

After Claude Code finishes, verify the system works:

### 1. Run Unit Tests
```bash
pytest tests/ -v
```

### 2. Run Integration Test
```bash
python main.py --scenario test
```

You should see output showing:
- Agent 1 processing sensor data
- Agent 2 updating COP with new entity
- Agent 3 revising mission plan
- Agent 4 retasking drone

### 3. Inspect Results
```bash
# View the Common Operating Picture
python -m src.cli show-cop

# View agent message history
python -m src.cli show-messages

# View what happened to drones
python -m src.cli show-drones
```

## Troubleshooting

### If Claude Code asks for clarification:
- Point it to CLAUDE.md for all specifications
- Refer to PROJECT_SPEC.md for detailed requirements
- The test scenario is fully defined in both documents

### If imports fail:
```bash
pip install -r requirements.txt
```

### If API calls fail:
Check your API key is set:
```bash
echo $ANTHROPIC_API_KEY
```

### If you want to reset and start over:
```bash
rm -rf src/ tests/ main.py *.db
claude
# Then restart from step 5 above
```

## Tips for Working with Claude Code

1. **Let it work in phases**: Don't interrupt between major components
2. **Review key files**: Check CLAUDE.md is being followed for critical components
3. **Use Plan Mode**: Press Shift+Tab twice for planning mode on complex components
4. **Test incrementally**: Ask Claude Code to test after each phase
5. **Use /agents**: You can create sub-agents for testing or code review

## What You'll Have When Done

A working prototype demonstrating:
- ✅ Four autonomous LLM agents with specialized roles
- ✅ Shared situational awareness (Common Operating Picture)
- ✅ Role-based authority enforcement
- ✅ Inter-agent coordination through events
- ✅ Complete audit trail of decisions
- ✅ Observable system state via CLI tools
- ✅ Automated test scenario

## Next Steps After Implementation

Once the system works:

1. **Experiment**: Modify the test scenario to try different situations
2. **Extend**: Add a 5th agent with different responsibilities
3. **Integrate**: Connect to real data sources via MCP
4. **Visualize**: Build a web dashboard to watch agents work
5. **Scale**: Move from SQLite to distributed database

## Questions?

Everything Claude Code needs to know is in:
- `.claude/CLAUDE.md` - Complete technical documentation
- `PROJECT_SPEC.md` - Requirements and specifications

If Claude Code seems confused, remind it to check these files.

Good luck! You're building something cool. 🚁🤖