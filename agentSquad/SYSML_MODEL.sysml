/**
 * SysML v2 Model: Multi-Agent Intelligence System
 * 
 * This model represents a distributed intelligence system with four specialized
 * LLM-based agents coordinating through shared state and message passing.
 */

package MultiAgentIntelligenceSystem {
    
    // ============================================================================
    // SYSTEM DEFINITION
    // ============================================================================
    
    part def MultiAgentIntelligenceSystem {
        doc /* 
        A distributed intelligence system for autonomous drone operations.
        Four specialized agents collaborate through a Common Operating Picture (COP)
        to process sensor data, maintain situational awareness, plan missions,
        and manage collection assets.
        */
        
        // System-level attributes
        attribute systemId : String;
        attribute operationalStatus : OperationalStatus;
        attribute missionContext : String;
        
        // Core infrastructure components
        part contextManager : ContextManager;
        part messageBus : MessageBus;
        part authoritySystem : AuthoritySystem;
        part mockTools : MockTools;
        
        // Four specialized agents
        part collectionProcessor : CollectionProcessorAgent;
        part intelligenceAnalyst : IntelligenceAnalystAgent;
        part missionPlanner : MissionPlannerAgent;
        part collectionManager : CollectionManagerAgent;
        
        // External interfaces
        interface anthropicAPI : AnthropicAPI;
        interface droneFleet : DroneFleet;
        interface sensorSystems : SensorSystems;
        
        // System constraints
        constraint authorityEnforcement {
            doc /* All agent actions must be validated against their assigned authorities */
        }
        
        constraint dataConsistency {
            doc /* COP must maintain ACID properties for all transactions */
        }
        
        constraint messageOrdering {
            doc /* Messages must be processed in temporal order within each agent */
        }
    }
    
    // ============================================================================
    // ENUMERATIONS AND VALUE TYPES
    // ============================================================================
    
    enum def OperationalStatus {
        INITIALIZING;
        CASUAL_MODE;
        PROFESSIONAL_MODE;
        RELAXED_MODE;
        SHUTDOWN;
    }
    
    enum def Authority {
        // Read authorities
        READ_SENSOR_DATA;
        READ_INTEL;
        READ_COP;
        READ_PLANS;
        READ_DRONE_STATUS;
        
        // Write authorities
        WRITE_PROCESSED_INTEL;
        WRITE_COP;
        WRITE_PLANS;
        WRITE_COLLECTION_TASKS;
        
        // Command authorities
        COMMAND_DRONES;
        CREATE_COLLECTION_TASKS;
        MODIFY_PLANS;
    }
    
    enum def MessageType {
        INTRODUCTION;
        CASUAL_CHAT;
        PROCESSED_INTELLIGENCE;
        NEW_INTELLIGENCE;
        COVERAGE_ASSESSMENT;
        STRATEGIC_ASSESSMENT;
        NEW_MISSION_PLAN;
        MISSION_DEBRIEF;
    }
    
    enum def AgentMode {
        CASUAL;
        PROFESSIONAL;
        RELAXED;
    }
    
    // ============================================================================
    // CORE INFRASTRUCTURE COMPONENTS
    // ============================================================================
    
    part def ContextManager {
        doc /* 
        SQLite-based Common Operating Picture (COP) providing shared state
        management with ACID transaction support.
        */
        
        attribute dbPath : String;
        
        // Data stores
        part droneStore : DroneStore;
        part entityStore : EntityStore;
        part taskStore : CollectionTaskStore;
        part planStore : MissionPlanStore;
        part messageStore : MessageStore;
        part eventStore : EventStore;
        
        // Operations
        action initialize();
        action close();
        action beginTransaction();
        action commitTransaction();
        action rollbackTransaction();
        
        // Drone operations
        action updateDrone(droneId: String, status: DroneStatus);
        action getDroneStatus(droneId: String) : DroneStatus;
        action getAllDrones() : DroneStatus[*];
        
        // Entity operations
        action addEntity(entityType: String, lat: Real, lon: Real, 
                        confidence: Real, detectedBy: String) : Integer;
        action getEntities() : Entity[*];
        action getEntitiesInArea(lat: Real, lon: Real, radius: Real) : Entity[*];
        
        // Task operations
        action createCollectionTask(droneId: String, taskType: String,
                                   lat: Real, lon: Real) : Integer;
        action getCollectionTasks() : CollectionTask[*];
        action updateTaskStatus(taskId: Integer, status: String);
        
        // Plan operations
        action createMissionPlan(planName: String, description: String) : Integer;
        action getMissionPlans() : MissionPlan[*];
        action updateMissionPlan(planId: Integer, description: String);
        
        // Audit operations
        action logMessage(sender: String, recipient: String, messageType: String,
                         content: String);
        action logEvent(agentRole: String, eventType: String, description: String);
    }
    
    part def MessageBus {
        doc /* 
        In-memory publish-subscribe message bus for agent coordination
        with queue management and message history.
        */
        
        attribute maxHistory : Integer = 1000;
        
        // Internal state
        part agentQueues : AgentQueue[*];
        part subscriptions : Subscription[*];
        part messageHistory : Message[*];
        
        // Operations
        action registerAgent(agentRole: String);
        action unregisterAgent(agentRole: String);
        action subscribe(agentRole: String, messageType: MessageType);
        action unsubscribe(agentRole: String, messageType: MessageType);
        action send(sender: String, recipient: String, messageType: MessageType, content: Any);
        action receive(agentRole: String) : Message;
        action getMessageHistory() : Message[*];
        
        // Message routing logic
        constraint messageDelivery {
            doc /* Messages are delivered to specific recipients and all subscribers */
        }
        
        constraint noSelfDelivery {
            doc /* Agents do not receive their own messages */
        }
    }
    
    part def AuthoritySystem {
        doc /* 
        Role-based access control system enforcing agent permissions
        through decorators and runtime validation.
        */
        
        // Authority mappings
        part roleAuthorities : RoleAuthorityMapping[*];
        
        // Operations
        action getRoleAuthorities(role: String) : Authority[*];
        action hasAuthority(role: String, authority: Authority) : Boolean;
        action checkAuthority(role: String, authority: Authority);
        action requiresAuthority(authority: Authority);
        
        // Authority definitions for each role
        constraint collectionProcessorAuthorities {
            doc /* Collection Processor: READ_SENSOR_DATA, READ_INTEL, WRITE_PROCESSED_INTEL */
        }
        
        constraint intelligenceAnalystAuthorities {
            doc /* Intelligence Analyst: READ_COP, WRITE_COP */
        }
        
        constraint missionPlannerAuthorities {
            doc /* Mission Planner: READ_COP, READ_PLANS, READ_DRONE_STATUS, WRITE_PLANS, MODIFY_PLANS */
        }
        
        constraint collectionManagerAuthorities {
            doc /* Collection Manager: READ_COP, READ_PLANS, READ_DRONE_STATUS, WRITE_COLLECTION_TASKS, CREATE_COLLECTION_TASKS, COMMAND_DRONES */
        }
    }
    
    // ============================================================================
    // BASE AGENT DEFINITION
    // ============================================================================
    
    abstract part def BaseAgent {
        doc /* 
        Abstract base class for all specialized agents providing common
        functionality for LLM interaction, message handling, and authority enforcement.
        */
        
        // Agent identity and state
        attribute role : String;
        attribute mode : AgentMode = AgentMode::CASUAL;
        attribute hasIntroduced : Boolean = false;
        attribute isRunning : Boolean = false;
        
        // Personality system
        attribute agentName : String;
        attribute personalityDescription : String;
        
        // LLM configuration
        attribute model : String = "claude-sonnet-4-20250514";
        attribute apiKey : String;
        
        // Component references
        ref contextManager : ContextManager;
        ref messageBus : MessageBus;
        ref authoritySystem : AuthoritySystem;
        
        // Core operations
        action start();
        action stop();
        action setMode(newMode: AgentMode);
        action introduceSelf();
        
        // Message handling
        abstract action handleMessage(message: Message);
        action sendMessage(recipient: String, messageType: MessageType, content: Any);
        
        // LLM interaction
        action callLLM(prompt: String, maxTokens: Integer, temperature: Real) : String;
        action makeDecision(context: String, question: String) : String;
        
        // Personality system
        action assignRandomPersonality();
        
        // Utility operations
        action logEvent(eventType: String, description: String);
        action extractJSON(response: String) : Any;
        
        // Authority validation
        constraint authorityCheck {
            doc /* All operations must be validated against agent authorities */
        }
        
        // Message processing loop
        behavior messageProcessingLoop {
            doc /* Continuous loop processing incoming messages */

            loop {
                action receiveMessage : Message = messageBus.receive(role);
                action handleMessage(receiveMessage);
            }
        }
    }

    // ============================================================================
    // SPECIALIZED AGENT DEFINITIONS
    // ============================================================================

    part def CollectionProcessorAgent :> BaseAgent {
        doc /*
        Agent 1: Processes raw sensor data and intelligence reports.
        Validates detections and publishes processed intelligence.
        */

        // Specialized attributes
        attribute confidenceThreshold : Real = 0.5;

        // Authority constraints
        constraint authorities {
            doc /* READ_SENSOR_DATA, READ_INTEL, WRITE_PROCESSED_INTEL */
        }

        // Core responsibilities
        action processSensorData(filePath: String);
        action processIntelligenceReport(filePath: String);
        action validateDetection(confidence: Real) : Boolean;
        action publishProcessedIntelligence(entities: Entity[*]);

        // Message handlers
        action handleCasualChat(message: Message);
        action handleMissionDebrief(message: Message);

        // Specialized behaviors
        behavior sensorDataProcessing {
            doc /* Process incoming sensor data files and validate detections */

            action loadSensorData(filePath: String) : SensorData;
            action analyzeSensorData(data: SensorData) : Entity[*];
            action filterValidDetections(entities: Entity[*]) : Entity[*];
            action publishIntelligence(entities: Entity[*]);
        }

        behavior intelligenceReportProcessing {
            doc /* Process intelligence reports and forward to analyst */

            action loadIntelReport(filePath: String) : IntelReport;
            action extractKeyInformation(report: IntelReport) : IntelSummary;
            action forwardToAnalyst(summary: IntelSummary);
        }
    }

    part def IntelligenceAnalystAgent :> BaseAgent {
        doc /*
        Agent 2: Analyzes processed intelligence and updates the COP.
        Identifies coverage gaps and maintains situational awareness.
        */

        // Specialized attributes
        attribute copConfidenceThreshold : Real = 0.7;

        // Authority constraints
        constraint authorities {
            doc /* READ_COP, WRITE_COP */
        }

        // Core responsibilities
        action analyzeProcessedIntelligence(intelligence: ProcessedIntelligence);
        action updateCOPWithEntities(entities: Entity[*]);
        action assessCoverageGaps() : CoverageGap[*];
        action notifyMissionPlanner(assessment: CoverageAssessment);
        action analyzeIntelligenceReport(reportId: String);

        // Message handlers
        action handleProcessedIntelligence(message: Message);
        action handleProcessedIntelReport(message: Message);
        action handleNewIntelligence(message: Message);
        action handleCasualChat(message: Message);
        action handleMissionDebrief(message: Message);

        // Specialized behaviors
        behavior intelligenceAnalysis {
            doc /* Analyze intelligence and update situational awareness */

            action evaluateSignificance(intelligence: ProcessedIntelligence) : Real;
            action correlateWithExistingIntel(entities: Entity[*]) : CorrelationResult;
            action updateCOP(entities: Entity[*]);
            action identifyHighValueTargets(entities: Entity[*]) : Entity[*];
        }

        behavior coverageAssessment {
            doc /* Assess surveillance coverage and identify gaps */

            action analyzeCoveragePatterns() : CoveragePattern[*];
            action identifyGaps(patterns: CoveragePattern[*]) : CoverageGap[*];
            action prioritizeGaps(gaps: CoverageGap[*]) : CoverageGap[*];
            action generateAssessment(gaps: CoverageGap[*]) : CoverageAssessment;
        }
    }

    part def MissionPlannerAgent :> BaseAgent {
        doc /*
        Agent 3: Creates and revises mission plans based on intelligence
        and coverage assessments. Assigns drones to missions.
        */

        // Specialized attributes
        attribute maxDronesPerMission : Integer = 4;
        attribute planRevisionThreshold : Real = 0.8;

        // Authority constraints
        constraint authorities {
            doc /* READ_COP, READ_PLANS, READ_DRONE_STATUS, WRITE_PLANS, MODIFY_PLANS */
        }

        // Core responsibilities
        action createMissionPlan(requirements: MissionRequirements) : MissionPlan;
        action reviseMissionPlan(planId: Integer, newRequirements: MissionRequirements);
        action assignDronesToMission(plan: MissionPlan) : DroneAssignment[*];
        action respondToCoverageAssessment(assessment: CoverageAssessment);
        action processStrategicAssessment(assessment: StrategicAssessment);

        // Message handlers
        action handleCoverageAssessment(message: Message);
        action handleStrategicAssessment(message: Message);
        action handleCasualChat(message: Message);
        action handleMissionDebrief(message: Message);

        // Specialized behaviors
        behavior missionPlanning {
            doc /* Create comprehensive mission plans with drone assignments */

            action analyzeMissionRequirements(requirements: MissionRequirements) : PlanningContext;
            action evaluateDroneCapabilities() : DroneCapability[*];
            action optimizeDroneAssignments(context: PlanningContext, capabilities: DroneCapability[*]) : DroneAssignment[*];
            action generateMissionPlan(assignments: DroneAssignment[*]) : MissionPlan;
        }

        behavior planRevision {
            doc /* Revise existing plans based on new intelligence or assessments */

            action evaluateRevisionNeed(assessment: Any) : Boolean;
            action identifyPlanChanges(currentPlan: MissionPlan, newRequirements: MissionRequirements) : PlanChange[*];
            action implementPlanChanges(planId: Integer, changes: PlanChange[*]);
            action notifyCollectionManager(updatedPlan: MissionPlan);
        }
    }

    part def CollectionManagerAgent :> BaseAgent {
        doc /*
        Agent 4: Executes mission plans by commanding drones and creating
        collection tasks. Has full authority over drone operations.
        */

        // Specialized attributes
        attribute maxConcurrentTasks : Integer = 10;
        attribute commandRetryLimit : Integer = 3;

        // Authority constraints
        constraint authorities {
            doc /* READ_COP, READ_PLANS, READ_DRONE_STATUS, WRITE_COLLECTION_TASKS, CREATE_COLLECTION_TASKS, COMMAND_DRONES */
        }

        // Core responsibilities
        action executeMissionPlan(plan: MissionPlan);
        action createCollectionTask(droneId: String, taskType: String, location: Location) : Integer;
        action sendDroneCommand(droneId: String, command: DroneCommand) : Boolean;
        action monitorDroneStatus();
        action manageDroneFleet();

        // Message handlers
        action handleNewMissionPlan(message: Message);
        action handleCasualChat(message: Message);
        action handleMissionDebrief(message: Message);

        // Specialized behaviors
        behavior missionExecution {
            doc /* Execute mission plans through drone tasking and command */

            action parseMissionPlan(plan: MissionPlan) : DroneTask[*];
            action validateDroneAvailability(tasks: DroneTask[*]) : Boolean;
            action executeDroneTasks(tasks: DroneTask[*]);
            action monitorTaskProgress(tasks: DroneTask[*]);
        }

        behavior droneCommandAndControl {
            doc /* Direct drone command and control operations */

            action sendNavigationCommand(droneId: String, location: Location) : Boolean;
            action sendSurveyCommand(droneId: String, area: Area) : Boolean;
            action sendTrackCommand(droneId: String, target: Target) : Boolean;
            action handleCommandFailure(droneId: String, command: DroneCommand);
        }
    }

    // ============================================================================
    // DATA STRUCTURES AND VALUE OBJECTS
    // ============================================================================

    part def Message {
        doc /* Message structure for agent communication */

        attribute sender : String;
        attribute recipient : String;
        attribute messageType : MessageType;
        attribute content : Any;
        attribute metadata : Any;
        attribute timestamp : Real;
    }

    part def Entity {
        doc /* Detected entity in the operational environment */

        attribute entityId : Integer;
        attribute entityType : String;
        attribute latitude : Real;
        attribute longitude : Real;
        attribute confidence : Real;
        attribute detectedBy : String;
        attribute detectedAt : Real;
        attribute description : String;
    }

    part def DroneStatus {
        doc /* Current status and capabilities of a drone */

        attribute droneId : String;
        attribute status : String;
        attribute latitude : Real;
        attribute longitude : Real;
        attribute altitude : Real;
        attribute batteryLevel : Real;
        attribute lastUpdate : Real;
        attribute capabilities : String[*];
    }

    part def CollectionTask {
        doc /* Task assigned to a drone for data collection */

        attribute taskId : Integer;
        attribute droneId : String;
        attribute taskType : String;
        attribute latitude : Real;
        attribute longitude : Real;
        attribute status : String;
        attribute createdAt : Real;
        attribute completedAt : Real;
        attribute description : String;
    }

    part def MissionPlan {
        doc /* Comprehensive mission plan with drone assignments */

        attribute planId : Integer;
        attribute planName : String;
        attribute description : String;
        attribute priority : String;
        attribute status : String;
        attribute createdAt : Real;
        attribute updatedAt : Real;
        attribute droneAssignments : DroneAssignment[*];
    }

    part def DroneAssignment {
        doc /* Assignment of a drone to a specific mission task */

        attribute droneId : String;
        attribute taskType : String;
        attribute location : Location;
        attribute description : String;
        attribute priority : Integer;
    }

    part def Location {
        doc /* Geographic location with coordinates */

        attribute latitude : Real;
        attribute longitude : Real;
        attribute altitude : Real;
    }

    part def CoverageGap {
        doc /* Identified gap in surveillance coverage */

        attribute gapId : String;
        attribute location : Location;
        attribute priority : String;
        attribute description : String;
        attribute recommendedAction : String;
    }

    part def CoverageAssessment {
        doc /* Assessment of surveillance coverage status */

        attribute assessmentId : String;
        attribute coverageGaps : CoverageGap[*];
        attribute priorityAreas : Location[*];
        attribute recommendations : String[*];
        attribute timestamp : Real;
    }

    // ============================================================================
    // PERSONALITY SYSTEM
    // ============================================================================

    part def PersonalityProfile {
        doc /* American personality profile for agent randomization */

        attribute name : String;
        attribute personalityDescription : String;
        attribute militaryBackground : String;
        attribute communicationStyle : String;
        attribute ageRange : String = "30-50";
    }

    part def PersonalitySystem {
        doc /* System for managing randomized American personalities */

        // Personality pools for each agent role
        part collectionProcessorPersonalities : PersonalityProfile[4] {
            // Mike, Sarah, Dave, Lisa - each with unique backgrounds
        }

        part intelligenceAnalystPersonalities : PersonalityProfile[4] {
            // Tom, Jennifer, Chris, Amanda - each with unique backgrounds
        }

        part missionPlannerPersonalities : PersonalityProfile[4] {
            // Steve, Rachel, Mark, Kelly - each with unique backgrounds
        }

        part collectionManagerPersonalities : PersonalityProfile[4] {
            // Jake, Nicole, Brian, Melissa - each with unique backgrounds
        }

        // Operations
        action assignRandomPersonality(agentRole: String) : PersonalityProfile;
        action getPersonalityPool(agentRole: String) : PersonalityProfile[*];
    }

    // ============================================================================
    // EXTERNAL INTERFACES
    // ============================================================================

    interface def AnthropicAPI {
        doc /* Interface to Anthropic Claude LLM API */

        action sendMessage(prompt: String, model: String, maxTokens: Integer, temperature: Real) : String;
        action validateAPIKey(apiKey: String) : Boolean;
    }

    interface def DroneFleet {
        doc /* Interface to external drone management system */

        action sendCommand(droneId: String, command: DroneCommand) : Boolean;
        action getDroneStatus(droneId: String) : DroneStatus;
        action getAllDroneStatuses() : DroneStatus[*];
    }

    interface def SensorSystems {
        doc /* Interface to external sensor data sources */

        action getSensorData(sensorId: String) : SensorData;
        action getIntelligenceReports() : IntelReport[*];
    }

    // ============================================================================
    // SYSTEM BEHAVIORS AND USE CASES
    // ============================================================================

    use case def ProcessNewDetection {
        doc /*
        Primary use case: Process new high-value entity detection
        and coordinate multi-agent response.
        */

        subject system : MultiAgentIntelligenceSystem;

        // Actors
        actor externalSensor : SensorSystems;
        actor droneFleet : DroneFleet;

        // Main flow
        action triggerDetection : externalSensor.getSensorData("UAV-002");
        action processData : system.collectionProcessor.processSensorData("detection.json");
        action analyzeIntelligence : system.intelligenceAnalyst.analyzeProcessedIntelligence();
        action updateCOP : system.intelligenceAnalyst.updateCOPWithEntities();
        action assessCoverage : system.intelligenceAnalyst.assessCoverageGaps();
        action createPlan : system.missionPlanner.createMissionPlan();
        action executePlan : system.collectionManager.executeMissionPlan();
        action commandDrones : system.collectionManager.sendDroneCommand();

        // Success criteria
        constraint successfulDetectionProcessing {
            doc /* Detection is processed, analyzed, planned, and executed within time constraints */
        }
    }

    use case def PersonalityIntroduction {
        doc /*
        Use case: Agents introduce themselves with randomized American personalities
        before transitioning to professional mode.
        */

        subject system : MultiAgentIntelligenceSystem;

        // Main flow
        action assignPersonalities : system.personalitySystem.assignRandomPersonality();
        action setCasualMode : system.*.setMode(AgentMode::CASUAL);
        action introduceAgents : system.*.introduceSelf();
        action casualChat : system.*.handleCasualChat();
        action switchToProfessional : system.*.setMode(AgentMode::PROFESSIONAL);
        action conductMission : system.processNewDetection();
        action switchToRelaxed : system.*.setMode(AgentMode::RELAXED);
        action missionDebrief : system.*.handleMissionDebrief();

        // Personality constraints
        constraint authenticPersonalities {
            doc /* Each agent must exhibit consistent personality traits throughout interaction */
        }

        constraint americanProfessionals {
            doc /* All personalities must represent typical American intelligence professionals aged 30-50 */
        }
    }

    // ============================================================================
    // SYSTEM CONSTRAINTS AND REQUIREMENTS
    // ============================================================================

    requirement def AuthorityEnforcement {
        doc /* All agent actions must be validated against role-based authorities */

        text "Each agent shall only perform actions within their assigned authority scope"

        constraint collectionProcessorLimitations {
            doc /* Collection Processor cannot modify COP, command drones, or change plans */
        }

        constraint intelligenceAnalystLimitations {
            doc /* Intelligence Analyst cannot command drones or create collection tasks */
        }

        constraint missionPlannerLimitations {
            doc /* Mission Planner cannot command drones directly */
        }

        constraint collectionManagerPrivileges {
            doc /* Collection Manager has full drone command authority within mission parameters */
        }
    }

    requirement def DataConsistency {
        doc /* Common Operating Picture must maintain data integrity */

        text "The COP shall provide ACID transaction properties for all data operations"

        constraint atomicOperations {
            doc /* All COP updates must be atomic */
        }

        constraint consistentState {
            doc /* COP must always be in a consistent state */
        }

        constraint isolatedTransactions {
            doc /* Concurrent agent operations must not interfere */
        }

        constraint durableStorage {
            doc /* All committed changes must be persistent */
        }
    }

    requirement def MessageOrdering {
        doc /* Message processing must maintain temporal consistency */

        text "Messages shall be processed in temporal order within each agent"

        constraint fifoProcessing {
            doc /* Each agent processes messages in FIFO order */
        }

        constraint noMessageLoss {
            doc /* No messages shall be lost during system operation */
        }
    }

    requirement def PersonalityConsistency {
        doc /* Agent personalities must remain consistent throughout operation */

        text "Each agent shall maintain consistent personality traits across all interactions"

        constraint randomizedAssignment {
            doc /* Personalities must be randomly assigned at system startup */
        }

        constraint authenticBehavior {
            doc /* Personality responses must be authentic to assigned character */
        }

        constraint modeTransitions {
            doc /* Personality must adapt appropriately to casual/professional/relaxed modes */
        }
    }

}
