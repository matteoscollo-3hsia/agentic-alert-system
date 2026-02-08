from pathlib import Path

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


def test_gn_universe_top_revenue() -> None:
    companies = [
        _company("c001", "100"),
        _company("c002", "200"),
        _company("c003", "150"),
    ]
    universe = pr._build_gn_universe(companies, universe_size=2)
    assert [company.company_id for company in universe] == ["c002", "c003"]


def test_gn_batch_wraps() -> None:
    universe = [_company(f"c00{i}", str(i * 10)) for i in range(1, 6)]
    selected, pointer_after = pr._select_gn_batch(
        universe,
        batch_size=2,
        pointer=4,
    )
    assert [company.company_id for company in selected] == ["c005", "c001"]
    assert pointer_after == 1


def test_gn_rotation_state_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "gn_rotation_state.json"
    pr._save_rotation_pointer(path, 7)
    assert pr._load_rotation_pointer(path) == 7
