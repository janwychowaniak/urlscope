from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class TaskInfo(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    uuid: str
    url: str
    domain: str | None = None
    apex_domain: str | None = Field(default=None, alias="apexDomain")
    time: datetime
    method: str | None = None
    visibility: str
    source: str | None = None
    user_agent: str | None = Field(default=None, alias="userAgent")
    report_url: str | None = Field(default=None, alias="reportURL")
    screenshot_url: str | None = Field(default=None, alias="screenshotURL")
    dom_url: str | None = Field(default=None, alias="domURL")
    tags: list[str] | None = None
    options: dict[str, Any] | None = None


class PageInfo(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    url: str
    domain: str | None = None
    apex_domain: str | None = Field(default=None, alias="apexDomain")
    domain_age_days: int | None = Field(default=None, alias="domainAgeDays")
    apex_domain_age_days: int | None = Field(
        default=None,
        alias="apexDomainAgeDays",
    )
    ip: str | None = None
    asn: str | None = None
    asnname: str | None = None
    country: str | None = None
    city: str | None = None
    language: str | None = None
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


class VerdictGroup(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    score: int | None = None
    categories: list[str] | None = None
    brands: list[str] | None = None
    tags: list[str] | None = None
    malicious: bool | None = None
    has_verdicts: bool | None = Field(default=None, alias="hasVerdicts")


class UrlscanVerdictGroup(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    score: int | None = None
    categories: list[str] | None = None
    brands: list[BrandMatch] | None = None
    tags: list[str] | None = None
    malicious: bool | None = None
    has_verdicts: bool | None = Field(default=None, alias="hasVerdicts")


class EnginesVerdictGroup(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    score: int | None = None
    malicious: bool | None = None
    categories: list[str] | None = None
    engines_total: int | None = Field(default=None, alias="enginesTotal")
    malicious_total: int | None = Field(default=None, alias="maliciousTotal")
    benign_total: int | None = Field(default=None, alias="benignTotal")
    malicious_verdicts: list[Any] | None = Field(
        default=None,
        alias="maliciousVerdicts",
    )
    benign_verdicts: list[Any] | None = Field(default=None, alias="benignVerdicts")
    tags: list[str] | None = None
    has_verdicts: bool | None = Field(default=None, alias="hasVerdicts")


class CommunityVerdictGroup(VerdictGroup):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    votes_total: int | None = Field(default=None, alias="votesTotal")
    votes_malicious: int | None = Field(default=None, alias="votesMalicious")
    votes_benign: int | None = Field(default=None, alias="votesBenign")


class Verdicts(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    overall: VerdictGroup | None = None
    urlscan: UrlscanVerdictGroup | None = None
    engines: EnginesVerdictGroup | None = None
    community: CommunityVerdictGroup | None = None


class CertificateInfo(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    subject_name: str | None = Field(
        default=None,
        alias="subjectName",
        validation_alias=AliasChoices("subjectName", "subject"),
    )
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
