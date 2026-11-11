"""Export observed food-aroma column values as a JSON reference file."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

import config

OUTPUT_PATH = Path(__file__).resolve().with_name("aroma_criteria.json")

COLUMN_INFO = {
    "aroma_id": ("string", False),
    "nom": ("string", True),
    "famille": ("string", True),
    "notes": ("string", False),
    "applications": ("array[string]", True),
    "sucrosite": ("number", True),
    "tenue_chaleur": ("string", True),
    "certifications": ("array[string]", True),
    "prix_indicatif_eur_kg": ("number", False),
    "delai_jours": ("integer", False),
    "volume_minimum_kg": ("number", False),
    "is_synthetic": ("boolean", True),
    "source_information": ("string", False),
}

ENUM_CANDIDATES = {
    "famille",
    "applications",
    "sucrosite",
    "tenue_chaleur",
    "certifications",
}


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def _sort_values(values: set[Any]) -> list[Any]:
    def sort_key(value: Any) -> tuple[str, Any]:
        value = _json_value(value)
        if isinstance(value, bool):
            return ("bool", value)
        if isinstance(value, (int, float)):
            return ("number", value)
        return ("string", str(value).casefold())

    return sorted(
        (_json_value(value) for value in values),
        key=sort_key,
    )


def export_criteria() -> dict[str, Any]:
    if not config.DATABASE_URL:
        raise RuntimeError(
            "La variable DATABASE_URL n'est pas définie. Configurez-la dans "
            "PowerShell avant de lancer ce script."
        )

    with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as connection:
        rows = connection.execute(
            """
            SELECT aroma_id, nom, famille, notes, applications, sucrosite,
                   tenue_chaleur, certifications, prix_indicatif_eur_kg,
                   delai_jours, volume_minimum_kg, is_synthetic,
                   source_information
            FROM food_aromas
            ORDER BY aroma_id
            """
        ).fetchall()

    columns: dict[str, dict[str, Any]] = {}
    for column, (value_type, filterable) in COLUMN_INFO.items():
        values: set[Any] = set()
        null_count = 0
        empty_count = 0
        for row in rows:
            value = row[column]
            if value is None:
                null_count += 1
            elif value_type.startswith("array["):
                if not value:
                    empty_count += 1
                for item in value:
                    if item is None:
                        null_count += 1
                    else:
                        values.add(item)
            else:
                values.add(value)

        if column == "is_synthetic":
            values.update((False, True))

        column_info: dict[str, Any] = {
            "type": value_type,
            "filterable": filterable,
            "values": _sort_values(values),
            "null_count": null_count,
        }
        if value_type.startswith("array["):
            column_info["empty_count"] = empty_count
        if column in ENUM_CANDIDATES:
            column_info["values_status"] = (
                "observed_candidates_review_before_treating_as_closed_list"
            )
        elif column == "is_synthetic":
            column_info["values_status"] = "boolean_domain"
        else:
            column_info["values_status"] = "observed_values_not_a_closed_domain"
        columns[column] = column_info

    return {
        "table": "food_aromas",
        "record_count": len(rows),
        "description": (
            "Distinct values currently present in food_aromas. For enum candidates, "
            "review and approve this list before treating it as a closed domain."
        ),
        "columns": columns,
    }


def main() -> None:
    try:
        data = export_criteria()
    except (psycopg.Error, RuntimeError) as exc:
        print(f"Erreur lors de l'export des critères : {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    OUTPUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"OK : {data['record_count']} arômes exportés vers {OUTPUT_PATH}",
        flush=True,
    )


if __name__ == "__main__":
    main()
