import random
from datetime import date

from agentic_alert.models.schemas import Company
from agentic_alert.sources import provider_registry as pr


def _company(company_id: str, revenue: str) -> Company:
    return Company(
        company_id=company_id,
        name=f"Company {company_id}",
        aliases=[],
        revenue_eur=revenue,
        industry_code="",
        industry_description="",
        website="",
        website_domain="",
        country="IT",
        contact_owner="",
        status="active",
    )


def test_gn_company_selection_top_revenue() -> None:
    companies = [
        _company("c001", "100"),
        _company("c002", "200"),
        _company("c003", "150"),
    ]
    selected = pr._select_gn_companies(
        companies,
        cap=2,
        mode="top_revenue",
        seed="",
    )
    assert [company.company_id for company in selected] == ["c002", "c003"]


def test_gn_company_selection_random_seeded() -> None:
    companies = [_company(f"c00{i}", str(i * 10)) for i in range(1, 6)]
    seed = "2026-02-07"
    seed_int = date.fromisoformat(seed).toordinal()
    ordered = sorted(companies, key=lambda company: company.company_id)
    rng = random.Random(seed_int)
    rng.shuffle(ordered)
    expected = [company.company_id for company in ordered[:2]]

    selected = pr._select_gn_companies(
        companies,
        cap=2,
        mode="random",
        seed=seed,
    )

    assert [company.company_id for company in selected] == expected


def test_gn_company_selection_rolling() -> None:
    companies = [_company(f"c00{i}", str(i * 10)) for i in range(1, 6)]
    seed = "2026-02-07"
    seed_int = date.fromisoformat(seed).toordinal()
    ordered = sorted(companies, key=lambda company: company.company_id)
    start = seed_int % len(ordered)
    cap = 2
    expected = ordered[start : start + cap]
    if len(expected) < cap:
        expected = expected + ordered[: cap - len(expected)]

    selected = pr._select_gn_companies(
        companies,
        cap=cap,
        mode="rolling",
        seed=seed,
    )

    assert [company.company_id for company in selected] == [
        company.company_id for company in expected
    ]
