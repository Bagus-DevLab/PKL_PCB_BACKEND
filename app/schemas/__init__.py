# Device schemas
from .device import (
    DeviceClaim, DeviceResponse, DeviceRegister, DeviceUpdate,
    DeviceAssignmentCreate, DeviceAssignmentResponse,
)

# User schemas
from .user import UserResponse, UpdateUserRole, UpdateUserName

# Sensor schemas
from .sensor import LogResponse

# Pagination
from .pagination import PaginatedResponse

__all__ = [
    # Device
    "DeviceClaim",
    "DeviceResponse",
    "DeviceRegister",
    "DeviceUpdate",
    "DeviceAssignmentCreate",
    "DeviceAssignmentResponse",
    # User
    "UserResponse",
    "UpdateUserRole",
    "UpdateUserName",
    # Sensor
    "LogResponse",
    # Pagination
    "PaginatedResponse",
]
