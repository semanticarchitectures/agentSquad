# SysML v2 Model Documentation: Multi-Agent Intelligence System

## Overview

This document describes the comprehensive SysML v2 model for the Multi-Agent Intelligence System, a distributed intelligence platform featuring four specialized LLM-based agents that collaborate through shared state and message passing to conduct autonomous drone operations.

## Model Structure

### 1. System Definition (`MultiAgentIntelligenceSystem`)

The top-level system definition encapsulates the entire multi-agent platform with:

- **Core Infrastructure Components**: Context Manager, Message Bus, Authority System, Mock Tools
- **Four Specialized Agents**: Collection Processor, Intelligence Analyst, Mission Planner, Collection Manager
- **External Interfaces**: Anthropic API, Drone Fleet, Sensor Systems
- **System-level Constraints**: Authority enforcement, data consistency, message ordering

### 2. Core Infrastructure Components

#### Context Manager (`ContextManager`)
- **Purpose**: SQLite-based Common Operating Picture (COP) providing shared state management
- **Key Features**: ACID transaction support, audit trail, multiple data stores
- **Data Stores**: Drones, Entities, Collection Tasks, Mission Plans, Messages, Events
- **Operations**: CRUD operations for all data types, transaction management

#### Message Bus (`MessageBus`)
- **Purpose**: In-memory publish-subscribe system for agent coordination
- **Key Features**: Queue management, message history, broadcast/targeted messaging
- **Constraints**: No self-delivery, temporal ordering, message persistence

#### Authority System (`AuthoritySystem`)
- **Purpose**: Role-based access control enforcing agent permissions
- **Key Features**: Decorator-based enforcement, runtime validation
- **Authority Types**: Read, Write, Command authorities mapped to specific roles

### 3. Agent Hierarchy

#### Base Agent (`BaseAgent`)
- **Type**: Abstract part definition
- **Purpose**: Common functionality for all specialized agents
- **Key Features**: 
  - LLM integration with Anthropic Claude
  - Message handling loop
  - Authority validation
  - Personality system integration
  - Mode switching (casual/professional/relaxed)

#### Specialized Agents

**Collection Processor Agent**
- **Authorities**: READ_SENSOR_DATA, READ_INTEL, WRITE_PROCESSED_INTEL
- **Responsibilities**: Process sensor data, validate detections, publish intelligence
- **Constraints**: Cannot modify COP directly, command drones, or change plans

**Intelligence Analyst Agent**
- **Authorities**: READ_COP, WRITE_COP
- **Responsibilities**: Analyze intelligence, update COP, assess coverage gaps
- **Constraints**: Cannot command drones or create collection tasks

**Mission Planner Agent**
- **Authorities**: READ_COP, READ_PLANS, READ_DRONE_STATUS, WRITE_PLANS, MODIFY_PLANS
- **Responsibilities**: Create mission plans, assign drones, respond to assessments
- **Constraints**: Cannot command drones directly

**Collection Manager Agent**
- **Authorities**: Full drone command authority plus all read permissions
- **Responsibilities**: Execute mission plans, command drones, create collection tasks
- **Constraints**: Must operate within mission parameters

### 4. Personality System

#### Personality Profiles (`PersonalityProfile`)
- **Purpose**: Authentic American professional personas for each agent
- **Characteristics**: Names, backgrounds, communication styles
- **Age Range**: 30-50 years (typical intelligence professionals)

#### Personality Pools
- **Collection Processor**: Mike, Sarah, Dave, Lisa (tech/data specialists)
- **Intelligence Analyst**: Tom, Jennifer, Chris, Amanda (analytical professionals)
- **Mission Planner**: Steve, Rachel, Mark, Kelly (strategic planners)
- **Collection Manager**: Jake, Nicole, Brian, Melissa (operational commanders)

### 5. Data Structures

#### Core Data Types
- **Message**: Agent communication structure
- **Entity**: Detected objects in operational environment
- **DroneStatus**: Current drone state and capabilities
- **CollectionTask**: Assigned drone missions
- **MissionPlan**: Comprehensive operational plans
- **CoverageGap**: Identified surveillance gaps

### 6. System Behaviors

#### Primary Use Cases

**Process New Detection**
1. External sensor triggers detection
2. Collection Processor validates and processes data
3. Intelligence Analyst analyzes and updates COP
4. Mission Planner creates/revises plans
5. Collection Manager executes drone commands

**Personality Introduction**
1. System assigns random personalities to agents
2. Agents introduce themselves in casual mode
3. Casual chat interaction period
4. Switch to professional mode for mission
5. Switch to relaxed mode for debrief

### 7. System Requirements

#### Authority Enforcement
- Each agent must operate only within assigned authority scope
- Runtime validation of all operations
- Clear separation of responsibilities

#### Data Consistency
- COP must maintain ACID properties
- Atomic operations for all updates
- Consistent state across concurrent access

#### Message Ordering
- FIFO processing within each agent
- No message loss during operation
- Temporal consistency maintenance

#### Personality Consistency
- Randomized assignment at startup
- Consistent traits throughout operation
- Appropriate mode transitions

## Key Design Patterns

### 1. **Separation of Concerns**
Each agent has a clearly defined role with specific authorities and responsibilities.

### 2. **Event-Driven Architecture**
Agents coordinate through asynchronous message passing rather than direct coupling.

### 3. **Shared State Management**
Common Operating Picture provides centralized, consistent state with transaction support.

### 4. **Role-Based Security**
Authority system enforces "who can do what" at runtime through decorators.

### 5. **Personality-Driven Interaction**
Randomized American professional personas create authentic, relatable agent interactions.

## Model Benefits

### 1. **Formal Specification**
SysML v2 provides precise, unambiguous system definition suitable for:
- Requirements traceability
- Architecture validation
- Implementation guidance
- Testing framework

### 2. **Scalability Design**
Modular architecture supports:
- Additional agent types
- Extended authority models
- Enhanced personality systems
- Integration with real systems

### 3. **Verification and Validation**
Formal constraints enable:
- Authority compliance checking
- Data consistency validation
- Message flow verification
- Behavioral correctness testing

### 4. **Documentation and Communication**
Model serves as:
- System blueprint for developers
- Architecture documentation for stakeholders
- Training material for operators
- Basis for system evolution

## Implementation Mapping

The SysML v2 model directly maps to the Python implementation:

- **Part definitions** → Python classes
- **Actions** → Class methods
- **Attributes** → Instance variables
- **Constraints** → Runtime assertions and decorators
- **Behaviors** → Async methods and workflows
- **Interfaces** → External API integrations

This tight coupling ensures the model remains synchronized with the actual implementation and serves as both specification and documentation.
