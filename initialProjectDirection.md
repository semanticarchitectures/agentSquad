This project is a exploration into AI assisted coding, looking to find effective TTPs

Starting 10/8/2025

There is a broad vision for a collaborative autonomy capability but what is needed now is a proof of concept.  This project is to build a proof of concept for a collaborative autonomy capability. 

The first step is going to be to create a set of 4 agents that work together to accomplish missions.  These agents are modeled on the OODA loop and execute a simplified intelligence production process.  The agents are:
- Observe
- Orient
- Decide
- Act

The Observe agent is responsible for gathering data from a variety of sources.  The Orient agent is responsible for processing the data and creating a situational awareness.  The Decide agent is responsible for making decisions based on the situational awareness.  The Act agent is responsible for executing the decisions.

To configure each agent there is a configuration file that contains the following:
- The name of the agent
- The type of agent (Observe, Orient, Decide, Act) including its roles and responsibilities
- Reference materials for each agent
- The data sources for the Observe agent
- The processing steps for the Orient agent
- The decision making steps for the Decide agent
- The execution steps for the Act agent

Each agent can be individually evaluated using a script with a scenario and questions.  A future goal for test and evaluation is to have auto-generated scenarios and questions based on the agent's configuration, and automated evaluation of responses, and learning from responses over time.

Model inter-agent communication using a messaging system that enables agents to subscribe to topics and publish to topics.  This will allow for a more dynamic and flexible system.

Using a web interface a person can monitor the status of the agents and the progress of the mission.  The web interface will also allow for the configuration of the agents and the creation of new agents.  It will also allow the user to inject messages into the system to interact with and test the agents.

