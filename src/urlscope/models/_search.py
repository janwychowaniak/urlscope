from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SearchResultItem(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(alias="_id")
    sort: list[Any] | None = None
    page: dict[str, Any] | None = None
    task: dict[str, Any] | None = None
    stats: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    results: list[SearchResultItem]
    total: int
    has_more: bool
