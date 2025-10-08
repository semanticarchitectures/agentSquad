"""Context Manager for the Common Operating Picture (COP).

This module provides SQLite-based storage and management for the shared
Common Operating Picture used by all agents in the system.
"""

import aiosqlite
import json
import time
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages the Common Operating Picture using SQLite.

    The COP stores:
    - Drone status and telemetry
    - Detected entities
    - Collection tasks
    - Mission plans
    - Message/event history for audit trail
    """

    def __init__(self, db_path: str = "cop.db"):
        """Initialize the context manager.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        await self._create_tables()
        logger.info(f"Context manager initialized with database: {self.db_path}")

    async def _create_tables(self) -> None:
        """Create all required tables for the COP."""
        async with self._db.execute("BEGIN TRANSACTION"):
            # Drones table
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS drones (
                    id TEXT PRIMARY KEY,
                    lat REAL,
                    lon REAL,
                    altitude REAL,
                    fuel_percent REAL,
                    sensor_status TEXT,
                    current_task TEXT,
                    last_updated REAL
                )
            """)

            # Entities table
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT,
                    lat REAL,
                    lon REAL,
                    confidence REAL,
                    detected_by TEXT,
                    detected_at REAL,
                    description TEXT
                )
            """)

            # Collection tasks table
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS collection_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drone_id TEXT,
                    task_type TEXT,
                    target_area TEXT,
                    priority INTEGER,
                    status TEXT,
                    created_by TEXT,
                    created_at REAL,
                    FOREIGN KEY(drone_id) REFERENCES drones(id)
                )
            """)

            # Mission plans table
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS mission_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_name TEXT,
                    objectives TEXT,
                    assigned_drones TEXT,
                    status TEXT,
                    created_by TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)

            # Message history table for audit trail
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS message_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    sender TEXT,
                    recipient TEXT,
                    message_type TEXT,
                    content TEXT,
                    metadata TEXT
                )
            """)

            # Event log table
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    agent_role TEXT,
                    event_type TEXT,
                    description TEXT,
                    data TEXT
                )
            """)

            await self._db.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            logger.info("Context manager closed")

    @asynccontextmanager
    async def transaction(self):
        """Provide a transaction context manager for atomic operations.

        Example:
            async with context_manager.transaction():
                await context_manager.update_drone(...)
                await context_manager.add_entity(...)
        """
        async with self._db.execute("BEGIN TRANSACTION"):
            try:
                yield
                await self._db.commit()
            except Exception as e:
                await self._db.rollback()
                logger.error(f"Transaction failed, rolled back: {e}")
                raise

    # ============================================================================
    # Drone operations
    # ============================================================================

    async def update_drone(
        self,
        drone_id: str,
        lat: float,
        lon: float,
        altitude: float,
        fuel_percent: float,
        sensor_status: str,
        current_task: Optional[str] = None,
    ) -> None:
        """Update or insert drone status.

        Args:
            drone_id: Unique drone identifier.
            lat: Latitude.
            lon: Longitude.
            altitude: Altitude in meters.
            fuel_percent: Fuel percentage remaining.
            sensor_status: Status of sensors (e.g., "operational", "degraded").
            current_task: Description of current task.
        """
        await self._db.execute(
            """
            INSERT INTO drones (id, lat, lon, altitude, fuel_percent, sensor_status, current_task, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                lat=excluded.lat,
                lon=excluded.lon,
                altitude=excluded.altitude,
                fuel_percent=excluded.fuel_percent,
                sensor_status=excluded.sensor_status,
                current_task=excluded.current_task,
                last_updated=excluded.last_updated
            """,
            (drone_id, lat, lon, altitude, fuel_percent, sensor_status, current_task, time.time()),
        )
        await self._db.commit()
        logger.debug(f"Updated drone {drone_id}")

    async def get_drone(self, drone_id: str) -> Optional[Dict[str, Any]]:
        """Get drone status by ID.

        Args:
            drone_id: Unique drone identifier.

        Returns:
            Dictionary with drone status or None if not found.
        """
        async with self._db.execute(
            "SELECT * FROM drones WHERE id = ?", (drone_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_drones(self) -> List[Dict[str, Any]]:
        """Get status of all drones.

        Returns:
            List of dictionaries with drone status.
        """
        async with self._db.execute("SELECT * FROM drones") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ============================================================================
    # Entity operations
    # ============================================================================

    async def add_entity(
        self,
        entity_type: str,
        lat: float,
        lon: float,
        confidence: float,
        detected_by: str,
        description: Optional[str] = None,
    ) -> int:
        """Add a detected entity to the COP.

        Args:
            entity_type: Type of entity (e.g., "vehicle", "structure").
            lat: Latitude.
            lon: Longitude.
            confidence: Confidence score (0-1).
            detected_by: Agent or sensor that detected the entity.
            description: Optional description.

        Returns:
            The ID of the newly created entity.
        """
        cursor = await self._db.execute(
            """
            INSERT INTO entities (entity_type, lat, lon, confidence, detected_by, detected_at, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (entity_type, lat, lon, confidence, detected_by, time.time(), description),
        )
        await self._db.commit()
        entity_id = cursor.lastrowid
        logger.debug(f"Added entity {entity_id} of type {entity_type}")
        return entity_id

    async def get_entities(
        self, entity_type: Optional[str] = None, min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Get entities from the COP.

        Args:
            entity_type: Filter by entity type (optional).
            min_confidence: Minimum confidence threshold.

        Returns:
            List of entity dictionaries.
        """
        query = "SELECT * FROM entities WHERE confidence >= ?"
        params = [min_confidence]

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ============================================================================
    # Collection task operations
    # ============================================================================

    async def create_collection_task(
        self,
        drone_id: str,
        task_type: str,
        target_area: str,
        priority: int,
        created_by: str,
    ) -> int:
        """Create a new collection task.

        Args:
            drone_id: Drone to assign the task to.
            task_type: Type of collection task.
            target_area: Description of target area.
            priority: Task priority (higher = more important).
            created_by: Agent that created the task.

        Returns:
            The ID of the newly created task.
        """
        cursor = await self._db.execute(
            """
            INSERT INTO collection_tasks (drone_id, task_type, target_area, priority, status, created_by, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """,
            (drone_id, task_type, target_area, priority, created_by, time.time()),
        )
        await self._db.commit()
        task_id = cursor.lastrowid
        logger.debug(f"Created collection task {task_id} for drone {drone_id}")
        return task_id

    async def update_task_status(self, task_id: int, status: str) -> None:
        """Update the status of a collection task.

        Args:
            task_id: Task ID.
            status: New status (e.g., "pending", "in_progress", "completed").
        """
        await self._db.execute(
            "UPDATE collection_tasks SET status = ? WHERE id = ?", (status, task_id)
        )
        await self._db.commit()
        logger.debug(f"Updated task {task_id} status to {status}")

    async def get_collection_tasks(
        self, drone_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get collection tasks.

        Args:
            drone_id: Filter by drone ID (optional).
            status: Filter by status (optional).

        Returns:
            List of task dictionaries.
        """
        query = "SELECT * FROM collection_tasks WHERE 1=1"
        params = []

        if drone_id:
            query += " AND drone_id = ?"
            params.append(drone_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ============================================================================
    # Mission plan operations
    # ============================================================================

    async def create_mission_plan(
        self,
        plan_name: str,
        objectives: str,
        assigned_drones: List[str],
        created_by: str,
    ) -> int:
        """Create a new mission plan.

        Args:
            plan_name: Name of the plan.
            objectives: Mission objectives.
            assigned_drones: List of drone IDs assigned to the plan.
            created_by: Agent that created the plan.

        Returns:
            The ID of the newly created plan.
        """
        drones_json = json.dumps(assigned_drones)
        current_time = time.time()

        cursor = await self._db.execute(
            """
            INSERT INTO mission_plans (plan_name, objectives, assigned_drones, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'draft', ?, ?, ?)
            """,
            (plan_name, objectives, drones_json, created_by, current_time, current_time),
        )
        await self._db.commit()
        plan_id = cursor.lastrowid
        logger.debug(f"Created mission plan {plan_id}: {plan_name}")
        return plan_id

    async def update_mission_plan(
        self,
        plan_id: int,
        objectives: Optional[str] = None,
        assigned_drones: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update a mission plan.

        Args:
            plan_id: Plan ID.
            objectives: New objectives (optional).
            assigned_drones: New drone assignments (optional).
            status: New status (optional).
        """
        updates = []
        params = []

        if objectives:
            updates.append("objectives = ?")
            params.append(objectives)

        if assigned_drones:
            updates.append("assigned_drones = ?")
            params.append(json.dumps(assigned_drones))

        if status:
            updates.append("status = ?")
            params.append(status)

        if updates:
            updates.append("updated_at = ?")
            params.append(time.time())
            params.append(plan_id)

            query = f"UPDATE mission_plans SET {', '.join(updates)} WHERE id = ?"
            await self._db.execute(query, params)
            await self._db.commit()
            logger.debug(f"Updated mission plan {plan_id}")

    async def get_mission_plans(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get mission plans.

        Args:
            status: Filter by status (optional).

        Returns:
            List of plan dictionaries.
        """
        query = "SELECT * FROM mission_plans"
        params = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            plans = []
            for row in rows:
                plan = dict(row)
                # Parse JSON drone list
                plan['assigned_drones'] = json.loads(plan['assigned_drones'])
                plans.append(plan)
            return plans

    # ============================================================================
    # Message and event logging
    # ============================================================================

    async def log_message(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a message between agents.

        Args:
            sender: Sending agent role.
            recipient: Recipient agent role or "all" for broadcast.
            message_type: Type of message.
            content: Message content.
            metadata: Additional metadata as dictionary.
        """
        metadata_json = json.dumps(metadata) if metadata else None

        await self._db.execute(
            """
            INSERT INTO message_history (timestamp, sender, recipient, message_type, content, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (time.time(), sender, recipient, message_type, content, metadata_json),
        )
        await self._db.commit()

    async def log_event(
        self,
        agent_role: str,
        event_type: str,
        description: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an agent event.

        Args:
            agent_role: Role of the agent logging the event.
            event_type: Type of event.
            description: Human-readable description.
            data: Additional event data as dictionary.
        """
        data_json = json.dumps(data) if data else None

        await self._db.execute(
            """
            INSERT INTO event_log (timestamp, agent_role, event_type, description, data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (time.time(), agent_role, event_type, description, data_json),
        )
        await self._db.commit()

    async def get_message_history(
        self, limit: int = 100, sender: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get message history.

        Args:
            limit: Maximum number of messages to return.
            sender: Filter by sender (optional).

        Returns:
            List of message dictionaries, newest first.
        """
        query = "SELECT * FROM message_history"
        params = []

        if sender:
            query += " WHERE sender = ?"
            params.append(sender)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_event_log(
        self, limit: int = 100, agent_role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get event log.

        Args:
            limit: Maximum number of events to return.
            agent_role: Filter by agent role (optional).

        Returns:
            List of event dictionaries, newest first.
        """
        query = "SELECT * FROM event_log"
        params = []

        if agent_role:
            query += " WHERE agent_role = ?"
            params.append(agent_role)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
