from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SearchResultItem(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(alias="_id")
    score: float | None = Field(default=None, alias="_score")
    sort: list[Any] | None = None
    page: dict[str, Any] | None = None
    task: dict[str, Any] | None = None
    stats: dict[str, Any] | None = None
    submitter: dict[str, Any] | None = None
    result: str | None = None
    screenshot: str | None = None


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    results: list[SearchResultItem]
    total: int
    took: int | None = None
    has_more: bool
