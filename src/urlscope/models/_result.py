from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskInfo(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    uuid: str
    url: str
    domain: str | None = None
    apex_domain: str | None = Field(default=None, alias="apexDomain")
    time: datetime
    method: str | None = None
    visibility: str
    tags: list[str] | None = None
    options: dict[str, Any] | None = None


class PageInfo(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    url: str
    domain: str | None = None
    apex_domain: str | None = Field(default=None, alias="apexDomain")
    ip: str | None = None
    asn: str | None = None
    asnname: str | None = None
    country: str | None = None
    city: str | None = None
    server: str | None = None
    title: str | None = None
    status: str | None = None
    mime_type: str | None = Field(default=None, alias="mimeType")
    tls_issuer: str | None = Field(default=None, alias="tlsIssuer")
    tls_valid_from: datetime | None = Field(default=None, alias="tlsValidFrom")
    tls_valid_days: int | None = Field(default=None, alias="tlsValidDays")
    tls_age_days: int | None = Field(default=None, alias="tlsAgeDays")
    umbrella_rank: int | None = Field(default=None, alias="umbrellaRank")
    redirected: str | None = None
    ptr: str | None = None


class BrandMatch(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    key: str
    name: str
    country: list[str] | None = None
    vertical: list[str] | None = None


class Verdicts(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    score: int | None = None
    categories: list[str] | None = None
    brands: list[BrandMatch] | None = None
    malicious: bool | None = None


class CertificateInfo(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    subject: str | None = None
    issuer: str | None = None
    valid_from: datetime | None = Field(default=None, alias="validFrom")
    valid_to: datetime | None = Field(default=None, alias="validTo")
    san_list: list[str] | None = Field(default=None, alias="sanList")


class ScanLists(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    ips: list[str] | None = None
    domains: list[str] | None = None
    urls: list[str] | None = None
    countries: list[str] | None = None
    asns: list[int] | None = None
    servers: list[str] | None = None
    hashes: list[str] | None = None
    certificates: list[CertificateInfo] | None = None
    link_domains: list[str] | None = Field(default=None, alias="linkDomains")


class ScanResult(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    task: TaskInfo
    page: PageInfo
    verdicts: Verdicts | None = None
    stats: dict[str, Any] | None = None
    lists: ScanLists | None = None
    data: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None
