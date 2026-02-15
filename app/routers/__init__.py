from .auth import router as auth_router
from .user import router as user_router
from .device import router as device_router

__all__ = ["auth_router", "user_router", "device_router"]
