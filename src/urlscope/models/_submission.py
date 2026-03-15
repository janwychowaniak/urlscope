from typing import Any

from pydantic import BaseModel, ConfigDict


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    message: str
    uuid: str
    result: str
    api: str
    visibility: str
    url: str
    country: str | None = None
    options: dict[str, Any] | None = None
