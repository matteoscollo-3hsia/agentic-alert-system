import csv
from pathlib import Path
from typing import Iterable, List, Dict


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def write_csv(
    path: Path,
    rows: Iterable[Dict[str, str]],
    fieldnames: List[str],
    append: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not append or path.stat().st_size == 0:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
