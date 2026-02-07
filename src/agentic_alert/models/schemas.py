from dataclasses import dataclass


@dataclass
class Company:
    company_id: str
    name: str
    aliases: list[str]
    revenue_eur: str
    industry_code: str
    industry_description: str
    website: str
    website_domain: str
    country: str
    contact_owner: str
    status: str


@dataclass
class Trigger:
    trigger_id: str
    name: str
    keywords: list[str]
    priority: str
    description: str


@dataclass
class Provider:
    provider_id: str
    name: str
    type: str
    base_url: str
    enabled: bool


@dataclass
class NewsItem:
    article_id: str
    provider_id: str
    source_name: str
    title: str
    url: str
    published_at: str
    content_snippet: str


@dataclass
class AlertCandidate:
    candidate_id: str
    article_id: str
    company_id: str
    trigger_id: str
    match_method: str
    confidence: float


@dataclass
class Alert:
    alert_id: str
    company_id: str
    company_name: str
    trigger_id: str
    trigger_name: str
    contact_owner: str
    source: str
    article_url: str
    published_at: str
    dedupe_key: str
    created_at: str
    status: str
