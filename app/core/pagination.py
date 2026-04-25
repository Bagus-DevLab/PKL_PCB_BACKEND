import math
from typing import Type
from pydantic import BaseModel
from sqlalchemy.orm import Query


def paginate(query: Query, page: int = 1, limit: int = 20, schema: Type[BaseModel] = None) -> dict:
    """
    Apply pagination ke SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Nomor halaman (1-indexed)
        limit: Jumlah item per halaman
        schema: Pydantic schema untuk serialization (opsional).
                Jika diberikan, ORM objects akan di-serialize via schema
                sehingga hanya field yang didefinisikan di schema yang dikembalikan.
    
    Returns:
        dict dengan keys: data, total, page, limit, total_pages
    """
    total = query.count()
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    # Serialize via schema jika diberikan
    if schema:
        data = [schema.model_validate(item).model_dump() for item in items]
    else:
        data = items

    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }
