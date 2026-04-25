import math
from sqlalchemy.orm import Query


def paginate(query: Query, page: int = 1, limit: int = 20) -> dict:
    """
    Apply pagination ke SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Nomor halaman (1-indexed)
        limit: Jumlah item per halaman
    
    Returns:
        dict dengan keys: data, total, page, limit, total_pages
    """
    # Hitung total sebelum pagination
    total = query.count()
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    # Apply offset dan limit
    offset = (page - 1) * limit
    data = query.offset(offset).limit(limit).all()

    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }
