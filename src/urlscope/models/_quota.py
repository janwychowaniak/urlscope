from pydantic import BaseModel, ConfigDict


class QuotaWindow(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    scope: str
    action: str
    window: str
    limit: int
    remaining: int
    reset: str | None = None


class QuotaInfo(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    quotas: list[QuotaWindow]
