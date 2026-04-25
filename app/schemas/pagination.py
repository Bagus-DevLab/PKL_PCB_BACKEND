from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Schema response dengan pagination.
    
    Contoh response:
    {
        "data": [...],
        "total": 100,
        "page": 1,
        "limit": 20,
        "total_pages": 5
    }
    """
    data: List[T]
    total: int
    page: int
    limit: int
    total_pages: int

    class Config:
        from_attributes = True
