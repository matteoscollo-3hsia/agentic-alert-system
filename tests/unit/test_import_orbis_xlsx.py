import csv
import sys
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from scripts.import_orbis_xlsx import import_orbis_xlsx  # noqa: E402


def test_import_orbis_xlsx(tmp_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active

    headers = [
        "Ragione socialeCaratteri latini",
        "Numero BvD ID",
        "Paese",
        "NACE Rev. 2, codici/e primari/o - descrizione",
        "Codice NACE Rev. 2, core code (4 cifre)",
        "Totale valore della produzione mil EUR\nUltimo anno disp.",
        "Indirizzo sito web",
    ]
    sheet.append(headers)
    sheet.append(
        [
            "Azienda S.p.A.",
            "BVD123",
            "Italia",
            "Manufacturing",
            "1234",
            12.5,
            "www.azienda.it",
        ]
    )
    sheet.append(
        [
            None,
            "BVD999",
            "Italia",
            "Services",
            "4321",
            5.0,
            "https://www.example.it",
        ]
    )

    input_path = tmp_path / "orbis_export.xlsx"
    workbook.save(input_path)

    output_path = tmp_path / "companies.csv"
    report_path = tmp_path / "report.csv"

    summary = import_orbis_xlsx(
        input_path=input_path,
        output_path=output_path,
        report_path=report_path,
        sheet_name=None,
    )

    assert summary["rows_in"] == 2
    assert summary["rows_written"] == 1
    assert summary["missing_website"] == 0
    assert summary["missing_revenue"] == 0

    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]
    assert row["company_id"] == "BVD123"
    assert row["revenue_eur"] == "12500000"
    assert row["website"] == "https://www.azienda.it"
    assert row["website_domain"] == "azienda.it"
    assert "Azienda SpA" in row["aliases"]

    with report_path.open(newline="", encoding="utf-8") as handle:
        report_rows = list(csv.DictReader(handle))

    assert len(report_rows) == 1
    assert report_rows[0]["reason"] == "missing_name"
