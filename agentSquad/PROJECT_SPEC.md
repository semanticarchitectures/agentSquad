# Multi-Agent Intelligence System - Project Specification

## Executive Summary

Build a prototype multi-agent system that demonstrates autonomous intelligence operations using four collaborating LLM agents managing a drone fleet through a shared Common Operating Picture (COP).

## Problem Statement

Intelligence operations require continuous processing of information from multiple sources, maintaining situational awareness, planning missions, and managing collection assets. This system demonstrates how multiple AI agents with different roles and authorities can collaborate autonomously to perform these functions.

## Success Criteria

The prototype is successful if it can demonstrate the test scenario:

1. **Input**: New sensor data arrives showing an unplanned high-value entity
2. **Expected**: System autonomously coordinates across 4 agents to:
   - Process and validate the information
   - Update the shared situational awareness model
   - Revise mission plans to address the new information
   - Retask a drone asset to collect on the new entity
3. **Output**: Observable agent coordination with full audit trail

## System Requirements

### Functional Requirements

**FR-1: Information Processing**
- System shall ingest drone telemetry (JSON format)
- System shall ingest intelligence reports (text format)
- System shall validate incoming information before updating COP

**FR-2: Situational Awareness**
- System shall maintain current state of all drone assets
- System shall track detected entities with confidence scores
- System shall identify coverage gaps in surveillance

**FR-3: Mission Planning**
- System shall generate mission plans based on COP state
- System shall revise plans when significant changes occur
- System shall assign drones to collection tasks

**FR-4: Asset Management**
- System shall track drone capabilities and status
- System shall task drones within defined authorities
- System shall respect role-based authority constraints

**FR-5: Collaboration**
- Agents shall communicate through message bus
- Agents shall access shared COP for coordination
- System shall maintain complete audit trail

### Non-Functional Requirements

**NFR-1: Latency**
- Agent decision-making: < 5 seconds
- COP queries: < 100ms
- Message delivery: < 50ms

**NFR-2: Observability**
- All agent decisions must be logged with reasoning
- All COP updates must be timestamped and attributed
- System must provide CLI tools to inspect state

**NFR-3: Authority Enforcement**
- System must prevent unauthorized agent actions
- System must log all authority checks
- System must raise errors on authority violations

**NFR-4: Maintainability**
- Code must follow PEP 8
- All functions must have type hints
- All classes must have docstrings

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         User / Simulation Driver        │
│  (Injects scenarios, observes results)  │
└────────────────┬────────────────────────┘
                 │
    ┌────────────▼────────────┐
    │   Message Bus           │
    │   (In-memory events)    │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │   Context Manager       │
    │   (SQLite COP)          │
    └────────────┬────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
┌────▼─────┐           ┌────▼─────┐
│ Agent 1  │           │ Agent 2  │
│ Collect  │◄─────────►│ Analyst  │
└────┬─────┘           └────┬─────┘
     │                      │
     └──────────┬───────────┘
                │
     ┌──────────┴───────────┐
     │                      │
┌────▼─────┐           ┌───▼──────┐
│ Agent 3  │           │ Agent 4  │
│ Planner  │◄─────────►│ Manager  │
└──────────┘           └──────────┘
     │                      │
     └──────────┬───────────┘
                │
    ┌───────────▼────────────┐
    │   Mock Applications    │
    │  (Simulated tools)     │
    └────────────────────────┘
```

## Agent Specifications

### Agent 1: Collection Processor
**Role**: Process and validate incoming information

**Inputs:**
- Drone telemetry files (JSON)
- Intelligence reports (text)

**Outputs:**
- Validated intelligence records in COP
- Alerts to other agents on significant information

**Authority:**
- READ: All incoming data
- WRITE: Processed intelligence table only
- CANNOT: Update entity tracking, command drones

**Decision Logic:**
1. Receive new information
2. Parse and validate format
3. Assess information quality/confidence
4. Write to COP if validated
5. Notify Agent 2 if significant

### Agent 2: Intelligence Analyst
**Role**: Maintain situational awareness and entity tracking

**Inputs:**
- Processed intelligence from Agent 1
- Current COP state

**Outputs:**
- Updated entity tracking
- Coverage gap assessments
- Significance assessments

**Authority:**
- READ: Processed intelligence, COP
- WRITE: Entities table, coverage assessments
- CANNOT: Create plans, command drones

**Decision Logic:**
1. Monitor for new intelligence
2. Correlate with existing entities
3. Update entity database
4. Assess coverage gaps
5. Notify Agent 3 if significant changes

### Agent 3: Mission Planner
**Role**: Create and revise mission plans

**Inputs:**
- COP state (entities, coverage, priorities)
- Drone capabilities and status

**Outputs:**
- Mission plans
- Plan revisions
- Task assignments

**Authority:**
- READ: Full COP, drone status
- WRITE: Mission plans table
- CANNOT: Command drones directly

**Decision Logic:**
1. Monitor for COP changes
2. Evaluate current plan effectiveness
3. Identify need for revision
4. Generate revised plan using planning tools
5. Notify Agent 4 of new plan

### Agent 4: Collection Manager
**Role**: Manage drone tasking and collection operations

**Inputs:**
- Mission plans from Agent 3
- Drone status and capabilities
- Collection requirements

**Outputs:**
- Collection tasks
- Drone commands (within authority)

**Authority:**
- READ: Full COP, all plans
- WRITE: Collection tasks, drone commands
- CAN: Execute approved drone commands

**Decision Logic:**
1. Monitor for new mission plans
2. Evaluate drone availability
3. Match drones to tasks
4. Verify authority for commands
5. Execute drone tasking
6. Update COP with task status

## Data Models

### Drone Status
```python
@dataclass
class DroneStatus:
    id: str
    lat: float
    lon: float
    altitude: float
    fuel_percent: float
    sensor_status: str
    current_task: Optional[str]
    last_updated: float
```

### Entity
```python
@dataclass
class Entity:
    id: int
    entity_type: str
    lat: float
    lon: float
    confidence: float
    detected_by: str
    detected_at: float
    description: str
```

### Collection Task
```python
@dataclass
class CollectionTask:
    id: int
    drone_id: str
    task_type: str
    target_area: str
    priority: int
    status: str
    created_by: str
    created_at: float
```

### Mission Plan
```python
@dataclass
class MissionPlan:
    id: int
    plan_name: str
    objectives: str
    assigned_drones: List[str]
    status: str
    created_by: str
    created_at: float
    updated_at: float
```

## Test Scenario Details

### Initial Setup

**Drones:**
- UAV-001: Position (34.05°N, 118.24°W), Fuel 85%, Status: Active, Task: Survey Area Alpha
- UAV-002: Position (34.08°N, 118.30°W), Fuel 72%, Status: Active, Task: Survey Area Bravo
- UAV-003: Position (34.06°N, 118.26°W), Fuel 90%, Status: In-transit, Task: Transit to Charlie

**Known Entities:**
- Entity-001: Type "vehicle", Position (34.051°N, 118.241°W), Confidence 0.85, Detected by UAV-001
- Entity-002: Type "structure", Position (34.052°N, 118.243°W), Confidence 0.92, Detected by UAV-001

**Current Mission Plan:**
- Plan: "Routine Surveillance"
- Objectives: "Maintain coverage of Areas Alpha, Bravo, Charlie"
- Status: "Active"

### Trigger Event

**New Sensor Data from UAV-002:**
```json
{
    "drone_id": "UAV-002",
    "timestamp": 1704067200,
    "position": {"lat": 34.08, "lon": -118.30, "alt": 500},
    "sensor_data": {
        "type": "visual",
        "detections": [{
            "entity_type": "high_value_target",
            "position": {"lat": 34.10, "lon": -118.35},
            "confidence": 0.88,
            "description": "Unidentified vehicle convoy in Area Delta"
        }]
    }
}
```

**Key Factors:**
- Area Delta (34.10°N, 118.35°W) is NOT currently under surveillance
- Entity confidence (0.88) exceeds threshold (0.7)
- Entity type "high_value_target" is significant
- No drone currently assigned to Area Delta

### Expected Agent Responses

**Agent 1 Response:**
- Validates sensor data format and confidence
- Creates processed intelligence record
- Publishes message: "High confidence detection in unsurveilled area"

**Agent 2 Response:**
- Receives processed intelligence
- Creates new entity (Entity-003) in COP
- Identifies coverage gap in Area Delta
- Assesses significance: HIGH (HVT in gap area)
- Publishes message: "Significant entity detected, coverage gap identified"

**Agent 3 Response:**
- Receives significance assessment
- Evaluates current plan (doesn't cover Area Delta)
- Determines plan revision needed
- Checks drone availability (UAV-003 available)
- Creates revised plan: "Emergency Response - Area Delta Coverage"
- Publishes message: "Plan revised to address Area Delta"

**Agent 4 Response:**
- Receives revised plan
- Evaluates UAV-003: Available, sufficient fuel, capable
- Checks authority: Has authority to retask drones per plan
- Creates collection task for UAV-003 to Area Delta
- Executes command to retask UAV-003
- Updates COP with new task
- Publishes message: "UAV-003 retasked to Area Delta"

### Success Metrics

The scenario succeeds if:
1. All 4 agents process information in correct sequence
2. Entity-003 created in COP with correct attributes
3. Mission plan revised and persisted
4. UAV-003 receives new collection task
5. Complete audit trail captured in logs
6. All authority checks pass
7. Total time < 20 seconds (4 agents × 5 seconds max)

## Development Phases

### Phase 1: Foundation (Day 1)
- Set up project structure
- Implement ContextManager with COP schema
- Implement MessageBus
- Create mock tools
- Write initial tests

### Phase 2: Base Agent (Day 1-2)
- Implement BaseAgent class
- Add authority enforcement
- Add LLM API integration
- Create agent factory

### Phase 3: Specialized Agents (Day 2-3)
- Implement all 4 agent types
- Write agent-specific prompts
- Test individual agent behavior
- Integrate with message bus

### Phase 4: Integration (Day 3-4)
- Implement main orchestrator
- Create test scenario runner
- Build CLI observability tools
- End-to-end testing

### Phase 5: Refinement (Day 4-5)
- Optimize agent prompts
- Add error handling
- Improve logging
- Documentation

## Risk Mitigation

**Risk: LLM non-determinism**
- Mitigation: Clear, structured prompts; request JSON responses; validate outputs

**Risk: Race conditions in COP updates**
- Mitigation: Use database transactions; implement optimistic locking

**Risk: Agent authority violations**
- Mitigation: Decorator-based enforcement; comprehensive logging; unit tests

**Risk: Message delivery failures**
- Mitigation: Simple retry logic; timeout handling; dead letter queue

**Risk: Scenario doesn't demonstrate coordination**
- Mitigation: Well-designed test scenario; observable intermediate states

## Deliverables

1. **Working Code**: All components implemented and tested
2. **Test Scenario**: Automated test that runs the scenario
3. **Documentation**: README with setup and usage instructions
4. **Observability**: CLI tools to inspect system state
5. **Logs**: Complete audit trail of test scenario execution

## Getting Started

1. Create project directory: `mkdir multi-agent-intelligence && cd multi-agent-intelligence`
2. Copy these files:
   - `.claude/CLAUDE.md`
   - `.claude/settings.json`
   - `PROJECT_SPEC.md` (this file)
3. Run: `claude` (initializes Claude Code in project)
4. Say: "Please implement this multi-agent intelligence system according to CLAUDE.md. Start with the project structure and foundation components."
