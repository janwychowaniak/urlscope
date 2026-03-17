from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field


class QuotaWindow(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    scope: str | None = None
    action: str
    window: str
    limit: int
    used: int | None = None
    remaining: int | None = None
    percent: float | int | None = None


class _QuotaPeriod(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    limit: int
    used: int | None = None
    remaining: int | None = None
    percent: float | int | None = None


class QuotaInfo(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    scope: str | None = Field(
        default=None,
        validation_alias=AliasChoices("scope", "source"),
    )
    limits: dict[str, Any]

    @computed_field
    @property
    def quotas(self) -> list[QuotaWindow]:
        windows: list[QuotaWindow] = []

        for action, value in self.limits.items():
            if not isinstance(value, dict):
                continue

            for window_name in ("minute", "hour", "day"):
                raw_window = value.get(window_name)
                if not isinstance(raw_window, dict):
                    continue

                period = _QuotaPeriod.model_validate(raw_window)
                windows.append(
                    QuotaWindow(
                        scope=self.scope,
                        action=action,
                        window=window_name,
                        limit=period.limit,
                        used=period.used,
                        remaining=period.remaining,
                        percent=period.percent,
                    )
                )

        return windows
