"""Pagination primitives."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from sqlnocturne.core.result import Result


@dataclass(frozen=True, slots=True)
class PageRequest:
    page: int = 1
    per_page: int = 20
    max_per_page: int = 100

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be greater than zero")
        if self.per_page < 1:
            raise ValueError("per_page must be greater than zero")
        if self.max_per_page < 1:
            raise ValueError("max_per_page must be greater than zero")

    @property
    def safe_per_page(self) -> int:
        return min(self.per_page, self.max_per_page)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.safe_per_page

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "per_page": self.safe_per_page,
            "offset": self.offset,
            "max_per_page": self.max_per_page,
        }


@dataclass(slots=True)
class Page:
    items: list[dict]
    total: int
    request: PageRequest

    @property
    def pages(self) -> int:
        if self.total <= 0:
            return 0
        return int(math.ceil(self.total / self.request.safe_per_page))

    @property
    def has_next(self) -> bool:
        return self.request.page < self.pages

    @property
    def has_prev(self) -> bool:
        return self.request.page > 1 and self.pages > 0

    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "pagination": {
                **self.request.to_dict(),
                "total": self.total,
                "pages": self.pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
            },
        }


def paginate_query(query, *, page: int = 1, per_page: int = 20, max_per_page: int = 100) -> Result:
    request = PageRequest(page=page, per_page=per_page, max_per_page=max_per_page)
    total = query.count()
    items = query.clone().limit(request.safe_per_page).offset(request.offset).all()
    payload = Page(items, total, request).to_dict()
    return Result.success(
        payload,
        message="Page selected",
        meta={
            "rows": len(items),
            "page": request.page,
            "per_page": request.safe_per_page,
            "total": total,
            "pages": payload["pagination"]["pages"],
        },
    )


def cursor_from_row(row: dict, key: str = "id") -> Any:
    if row is None:
        return None
    return row.get(key)


def cursor_page(query, *, after: Any = None, key: str = "id", limit: int = 20) -> Result:
    working = query.clone()
    if after is not None:
        working.where(key, ">", after)
    rows = working.order(key, "ASC").limit(limit + 1).all()
    has_next = len(rows) > limit
    items = rows[:limit]
    next_cursor = cursor_from_row(items[-1], key) if has_next and items else None
    return Result.success(
        {
            "items": items,
            "cursor": {
                "key": key,
                "after": after,
                "next": next_cursor,
                "has_next": has_next,
                "limit": limit,
            },
        },
        message="Cursor page selected",
        meta={"rows": len(items), "has_next": has_next},
    )
