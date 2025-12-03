from sqlalchemy.orm import Query
from sqlalchemy import or_
from typing import List, Any, Tuple, Optional

def clean_search_string(search_item: Optional[str]) -> Optional[str]:
    if not search_item:
        return None
    
    cleaned = search_item.strip()
    
    cleaned = cleaned.strip("'").strip('"')
    
    cleaned = cleaned.strip()
    
    return cleaned if cleaned else None


def apply_search_filter(
    query: Query,
    search_item: Optional[str],
    search_columns: List[Any]
) -> Query:
    search_clean = clean_search_string(search_item)
    
    if not search_clean:
        return query

    search_pattern = f"%{search_clean}%"

    search_conditions = [col.ilike(search_pattern) for col in search_columns]

    return query.filter(or_(*search_conditions))


# Menampilkan date range filter ke query
def apply_date_range_filter(
    query: Query,
    date_column: Any,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Query:
    if start_date and end_date:
        query = query.filter(date_column >= start_date, date_column <= end_date)
    elif start_date:
        query = query.filter(date_column >= start_date)
    elif end_date:
        query = query.filter(date_column <= end_date)

    return query


def apply_pagination(
    query: Query,
    page: int,
    limit: int
) -> Tuple[Query, int]:
    total = query.count()

    offset = (page - 1) * limit

    paginated_query = query.offset(offset).limit(limit)

    return paginated_query, total


def apply_sorting(
    query: Query,
    sort_column: Any,
    sort_direction: str = "desc"
) -> Query:
    if sort_direction.lower() == "asc":
        return query.order_by(sort_column.asc())
    else:
        return query.order_by(sort_column.desc())


def apply_dynamic_filters(
    query: Query,
    filters: dict
) -> Query:
    for column, value in filters.items():
        if value is not None:
            query = query.filter(column == value)
    return query