"""Command-line interface tools for observability.

Provides CLI commands to view COP state, message history, and event logs.
"""

import asyncio
import sys
import json
from datetime import datetime
from typing import Optional

from .context_manager import ContextManager


async def show_cop(db_path: str = "cop.db") -> None:
    """Display the current Common Operating Picture.

    Args:
        db_path: Path to the COP database.
    """
    context_manager = ContextManager(db_path)
    await context_manager.initialize()

    print("=" * 80)
    print("COMMON OPERATING PICTURE")
    print("=" * 80)
    print()

    # Show drones
    drones = await context_manager.get_all_drones()
    print(f"DRONES ({len(drones)}):")
    print("-" * 80)
    for drone in drones:
        print(f"  ID: {drone['id']}")
        print(f"    Position: ({drone['lat']:.4f}, {drone['lon']:.4f}) @ {drone['altitude']}m")
        print(f"    Fuel: {drone['fuel_percent']:.1f}%")
        print(f"    Sensors: {drone['sensor_status']}")
        print(f"    Current Task: {drone.get('current_task', 'None')}")
        if drone['last_updated']:
            dt = datetime.fromtimestamp(drone['last_updated'])
            print(f"    Last Updated: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    # Show entities
    entities = await context_manager.get_entities()
    print(f"ENTITIES ({len(entities)}):")
    print("-" * 80)
    for entity in entities[:20]:  # Limit to 20
        print(f"  #{entity['id']} - {entity['entity_type']}")
        print(f"    Position: ({entity['lat']:.4f}, {entity['lon']:.4f})")
        print(f"    Confidence: {entity['confidence']:.2f}")
        print(f"    Detected By: {entity['detected_by']}")
        if entity['detected_at']:
            dt = datetime.fromtimestamp(entity['detected_at'])
            print(f"    Detected At: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        if entity['description']:
            print(f"    Description: {entity['description']}")
        print()

    if len(entities) > 20:
        print(f"  ... and {len(entities) - 20} more entities")
        print()

    # Show collection tasks
    tasks = await context_manager.get_collection_tasks()
    print(f"COLLECTION TASKS ({len(tasks)}):")
    print("-" * 80)
    for task in tasks:
        print(f"  Task #{task['id']} - {task['task_type']}")
        print(f"    Drone: {task['drone_id']}")
        print(f"    Target Area: {task['target_area']}")
        print(f"    Priority: {task['priority']}")
        print(f"    Status: {task['status']}")
        print(f"    Created By: {task['created_by']}")
        if task['created_at']:
            dt = datetime.fromtimestamp(task['created_at'])
            print(f"    Created At: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    # Show mission plans
    plans = await context_manager.get_mission_plans()
    print(f"MISSION PLANS ({len(plans)}):")
    print("-" * 80)
    for plan in plans:
        print(f"  Plan #{plan['id']} - {plan['plan_name']}")
        print(f"    Status: {plan['status']}")
        print(f"    Objectives: {plan['objectives']}")
        print(f"    Assigned Drones: {', '.join(plan['assigned_drones'])}")
        print(f"    Created By: {plan['created_by']}")
        if plan['created_at']:
            dt = datetime.fromtimestamp(plan['created_at'])
            print(f"    Created At: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        if plan['updated_at']:
            dt = datetime.fromtimestamp(plan['updated_at'])
            print(f"    Updated At: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    await context_manager.close()


async def show_messages(db_path: str = "cop.db", limit: int = 50, sender: Optional[str] = None) -> None:
    """Display message history.

    Args:
        db_path: Path to the COP database.
        limit: Maximum number of messages to show.
        sender: Filter by sender (optional).
    """
    context_manager = ContextManager(db_path)
    await context_manager.initialize()

    messages = await context_manager.get_message_history(limit=limit, sender=sender)

    print("=" * 80)
    print(f"MESSAGE HISTORY (showing {len(messages)} messages)")
    if sender:
        print(f"Filtered by sender: {sender}")
    print("=" * 80)
    print()

    for msg in messages:
        dt = datetime.fromtimestamp(msg['timestamp'])
        print(f"[{dt.strftime('%Y-%m-%d %H:%M:%S')}] {msg['sender']} -> {msg['recipient']}")
        print(f"  Type: {msg['message_type']}")
        print(f"  Content: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
        if msg['metadata']:
            print(f"  Metadata: {msg['metadata']}")
        print()

    await context_manager.close()


async def show_events(db_path: str = "cop.db", limit: int = 50, agent: Optional[str] = None) -> None:
    """Display event log.

    Args:
        db_path: Path to the COP database.
        limit: Maximum number of events to show.
        agent: Filter by agent role (optional).
    """
    context_manager = ContextManager(db_path)
    await context_manager.initialize()

    events = await context_manager.get_event_log(limit=limit, agent_role=agent)

    print("=" * 80)
    print(f"EVENT LOG (showing {len(events)} events)")
    if agent:
        print(f"Filtered by agent: {agent}")
    print("=" * 80)
    print()

    for event in events:
        dt = datetime.fromtimestamp(event['timestamp'])
        print(f"[{dt.strftime('%Y-%m-%d %H:%M:%S')}] {event['agent_role']} - {event['event_type']}")
        print(f"  {event['description']}")
        if event['data']:
            try:
                data = json.loads(event['data'])
                print(f"  Data: {json.dumps(data, indent=4)}")
            except:
                print(f"  Data: {event['data']}")
        print()

    await context_manager.close()


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli <command> [options]")
        print()
        print("Commands:")
        print("  show-cop              Show the Common Operating Picture")
        print("  show-messages [N]     Show last N messages (default: 50)")
        print("  show-events [N]       Show last N events (default: 50)")
        print()
        print("Options:")
        print("  --db PATH            Database path (default: cop.db)")
        print("  --sender AGENT       Filter messages by sender")
        print("  --agent AGENT        Filter events by agent")
        sys.exit(1)

    command = sys.argv[1]
    db_path = "cop.db"
    limit = 50
    sender = None
    agent = None

    # Parse options
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--db" and i + 1 < len(sys.argv):
            db_path = sys.argv[i + 1]
            i += 2
        elif arg == "--sender" and i + 1 < len(sys.argv):
            sender = sys.argv[i + 1]
            i += 2
        elif arg == "--agent" and i + 1 < len(sys.argv):
            agent = sys.argv[i + 1]
            i += 2
        else:
            try:
                limit = int(arg)
                i += 1
            except ValueError:
                i += 1

    if command == "show-cop":
        asyncio.run(show_cop(db_path))
    elif command == "show-messages":
        asyncio.run(show_messages(db_path, limit, sender))
    elif command == "show-events":
        asyncio.run(show_events(db_path, limit, agent))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
