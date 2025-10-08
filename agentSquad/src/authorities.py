"""Authority and permission system for multi-agent operations.

This module defines the permission system that enforces role-based access control
for agent actions. Each agent has specific authorities defined by their role.
"""

from enum import Enum
from typing import Set
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class Authority(Enum):
    """Enumeration of all possible agent authorities."""

    # Read authorities
    READ_SENSOR_DATA = "read_sensor_data"
    READ_INTEL = "read_intel"
    READ_COP = "read_cop"
    READ_PLANS = "read_plans"
    READ_DRONE_STATUS = "read_drone_status"

    # Write authorities
    WRITE_PROCESSED_INTEL = "write_processed_intel"
    WRITE_COP = "write_cop"
    WRITE_PLANS = "write_plans"
    WRITE_COLLECTION_TASKS = "write_collection_tasks"

    # Command authorities
    COMMAND_DRONES = "command_drones"
    CREATE_COLLECTION_TASKS = "create_collection_tasks"
    MODIFY_PLANS = "modify_plans"


class UnauthorizedActionError(Exception):
    """Raised when an agent attempts an action outside its authority."""

    def __init__(self, agent_role: str, required_authority: Authority):
        self.agent_role = agent_role
        self.required_authority = required_authority
        super().__init__(
            f"Agent '{agent_role}' lacks required authority: {required_authority.value}"
        )


# Define role-based authority mappings
ROLE_AUTHORITIES: dict[str, Set[Authority]] = {
    "collection_processor": {
        Authority.READ_SENSOR_DATA,
        Authority.READ_INTEL,
        Authority.WRITE_PROCESSED_INTEL,
    },
    "intelligence_analyst": {
        Authority.READ_COP,
        Authority.WRITE_COP,
    },
    "mission_planner": {
        Authority.READ_COP,
        Authority.READ_PLANS,
        Authority.READ_DRONE_STATUS,
        Authority.WRITE_PLANS,
        Authority.MODIFY_PLANS,
    },
    "collection_manager": {
        Authority.READ_COP,
        Authority.READ_PLANS,
        Authority.READ_DRONE_STATUS,
        Authority.WRITE_COLLECTION_TASKS,
        Authority.CREATE_COLLECTION_TASKS,
        Authority.COMMAND_DRONES,
    },
}


def get_role_authorities(role: str) -> Set[Authority]:
    """Get the set of authorities for a given role.

    Args:
        role: The agent role identifier.

    Returns:
        Set of authorities granted to this role.

    Raises:
        ValueError: If the role is not recognized.
    """
    if role not in ROLE_AUTHORITIES:
        raise ValueError(f"Unknown role: {role}")
    return ROLE_AUTHORITIES[role]


def has_authority(role: str, authority: Authority) -> bool:
    """Check if a role has a specific authority.

    Args:
        role: The agent role identifier.
        authority: The authority to check.

    Returns:
        True if the role has the authority, False otherwise.
    """
    try:
        role_auths = get_role_authorities(role)
        return authority in role_auths
    except ValueError:
        return False


def requires_authority(authority: Authority):
    """Decorator to enforce authority requirements on agent methods.

    This decorator checks if the agent has the required authority before
    executing the method. If not, it raises UnauthorizedActionError.

    Args:
        authority: The authority required to execute the method.

    Returns:
        Decorated function that enforces authority check.

    Example:
        @requires_authority(Authority.COMMAND_DRONES)
        async def send_drone_command(self, drone_id: str, command: dict):
            # Method implementation
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Check if the instance has a 'role' attribute
            if not hasattr(self, 'role'):
                raise AttributeError(
                    f"{self.__class__.__name__} must have a 'role' attribute"
                )

            # Verify authority
            if not has_authority(self.role, authority):
                logger.warning(
                    f"Authority check failed: {self.role} attempted to use "
                    f"{authority.value} without permission",
                    extra={
                        "agent_role": self.role,
                        "required_authority": authority.value,
                        "method": func.__name__,
                    }
                )
                raise UnauthorizedActionError(self.role, authority)

            # Log successful authority check
            logger.debug(
                f"Authority check passed: {self.role} authorized for {authority.value}",
                extra={
                    "agent_role": self.role,
                    "authority": authority.value,
                    "method": func.__name__,
                }
            )

            return await func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Check if the instance has a 'role' attribute
            if not hasattr(self, 'role'):
                raise AttributeError(
                    f"{self.__class__.__name__} must have a 'role' attribute"
                )

            # Verify authority
            if not has_authority(self.role, authority):
                logger.warning(
                    f"Authority check failed: {self.role} attempted to use "
                    f"{authority.value} without permission",
                    extra={
                        "agent_role": self.role,
                        "required_authority": authority.value,
                        "method": func.__name__,
                    }
                )
                raise UnauthorizedActionError(self.role, authority)

            # Log successful authority check
            logger.debug(
                f"Authority check passed: {self.role} authorized for {authority.value}",
                extra={
                    "agent_role": self.role,
                    "authority": authority.value,
                    "method": func.__name__,
                }
            )

            return func(self, *args, **kwargs)

        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
