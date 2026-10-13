"""PostgreSQL integration for PasteurAI.

Usage:
    from src.database import PasteurDB
    db = PasteurDB("postgresql://user:pass@localhost:5432/pasteurai")
    db.store_report(json_payload)
"""

import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any

from src.biomarker_registry import get_seed_rows, normalize


class PasteurDB:
    """Thin wrapper around a PostgreSQL connection for storing parsed reports."""

    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.environ.get(
            "PASTEURAI_DATABASE_URL",
            "postgresql://pasteurai:pasteurai@localhost:5432/pasteurai",
        )
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            import psycopg
            self._conn = psycopg.connect(self.dsn)
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── schema management ─────────────────────────────────

    def init_schema(self, schema_path: str | Path | None = None):
        """Create all tables from schema.sql."""
        if schema_path is None:
            schema_path = Path(__file__).parent.parent / "data" / "schema.sql"
        sql = Path(schema_path).read_text(encoding="utf-8")
        with self.conn.cursor() as cur:
            cur.execute(sql)
        self.conn.commit()

    def seed_biomarkers(self):
        """Populate the biomarkers table from the Medical Knowledge Layer."""
        rows = get_seed_rows()
        with self.conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """INSERT INTO biomarkers (code, name_fr, name_en, unit,
                                              category, system, dashboard_group, description)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (code) DO NOTHING""",
                    (row["code"], row["name_fr"], row["name_en"], row["unit"],
                     row["category"], row["system"], row["dashboard_group"], row["description"]),
                )
        self.conn.commit()
        return len(rows)

    # ── store one report ──────────────────────────────────

    def store_report(self, report: dict, raw_json: dict | None = None) -> dict:
        """Insert patient → report → tests into normalized tables.

        Returns dict with {patient_id, report_id, test_count}.
        """
        patient = report.get("patient", {})
        dates = report.get("dates", {})
        tests = report.get("tests", [])
        meta = report.get("meta", {})

        name = patient.get("name", "")
        name_norm = _normalize_name(name)

        # ── upsert patient ─────────────────────────────────
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO patients (name, name_normalized, sex)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (name_normalized) DO NOTHING
                   RETURNING id""",
                (name, name_norm, patient.get("sex", "")),
            )
            row = cur.fetchone()
            if row:
                patient_id = row[0]
            else:
                cur.execute(
                    "SELECT id FROM patients WHERE name_normalized = %s",
                    (name_norm,),
                )
                patient_id = cur.fetchone()[0]

            # ── insert report ──────────────────────────────
            cur.execute(
                """INSERT INTO reports
                       (patient_id, report_ref, demande_id,
                        date_demande, date_edition, pdf_path, raw_json)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (
                    patient_id,
                    report.get("report_ref", ""),
                    report.get("demande_id", ""),
                    _parse_date(dates.get("demande")),
                    _parse_date(dates.get("edition")),
                    meta.get("pdf_source", ""),
                    json.dumps(raw_json or report, ensure_ascii=False),
                ),
            )
            report_id = cur.fetchone()[0]

            # ── insert tests ───────────────────────────────
            for t in tests:
                bio = normalize(t.get("test_name", ""))
                cur.execute(
                    """INSERT INTO tests
                           (report_id, test_name, code, biomarker, normalization_conf,
                            category, dashboard_group,
                            value_float, value_display, unit, abnormal,
                            range_comparator, range_min, range_max,
                            sec_range_min, sec_range_max,
                            section, sub_section, methodology,
                            anteriority_value, anteriority_date, test_date)
                       VALUES (%s,%s,%s,%s,%s,
                               %s,%s,
                               %s,%s,%s,%s,
                               %s,%s,%s,
                               %s,%s,
                               %s,%s,%s,
                               %s,%s,%s)""",
                    (
                        report_id,
                        t.get("test_name", ""),
                        bio["code"],
                        bio["name_en"],
                        bio["confidence"],
                        bio.get("category", ""),
                        bio.get("dashboard_group", ""),
                        t.get("value"),
                        t.get("value_display", ""),
                        t.get("unit", ""),
                        t.get("abnormal", False),
                        t.get("range", {}).get("comparator", ""),
                        t.get("range", {}).get("min"),
                        t.get("range", {}).get("max"),
                        t.get("secondary_range", {}).get("min"),
                        t.get("secondary_range", {}).get("max"),
                        t.get("section", ""),
                        t.get("sub_section", ""),
                        t.get("methodology", ""),
                        t.get("anteriority", {}).get("value") if t.get("anteriority") else None,
                        _parse_date(t.get("anteriority", {}).get("date")) if t.get("anteriority") else None,
                        _parse_date(t.get("test_date")),
                    ),
                )

            self.conn.commit()

        return {
            "patient_id": patient_id,
            "report_id": report_id,
            "test_count": len(tests),
        }

    # ── query helpers ─────────────────────────────────────

    def get_patient_reports(self, patient_name: str) -> list[dict]:
        """Return all reports for a given patient."""
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT r.id, r.report_ref, r.date_edition, r.raw_json
                   FROM reports r
                   JOIN patients p ON p.id = r.patient_id
                   WHERE p.name_normalized LIKE %s
                   ORDER BY r.date_edition DESC""",
                (f"%{_normalize_name(patient_name)}%",),
            )
            rows = cur.fetchall()
        return [
            {"id": r[0], "report_ref": r[1], "date_edition": str(r[2]) if r[2] else "",
             "raw_json": r[3]}
            for r in rows
        ]

    def get_abnormal_tests(self, report_ref: str | None = None) -> list[dict]:
        """Return all abnormal tests, optionally filtered by report."""
        with self.conn.cursor() as cur:
            if report_ref:
                cur.execute(
                    """SELECT t.test_name, t.value_float, t.unit, t.biomarker,
                              t.range_comparator, t.range_min, t.range_max,
                              r.report_ref, p.name
                       FROM tests t
                       JOIN reports r ON r.id = t.report_id
                       JOIN patients p ON p.id = r.patient_id
                       WHERE t.abnormal = TRUE AND r.report_ref = %s
                       ORDER BY t.test_name""",
                    (report_ref,),
                )
            else:
                cur.execute(
                    """SELECT t.test_name, t.value_float, t.unit, t.biomarker,
                              t.range_comparator, t.range_min, t.range_max,
                              r.report_ref, p.name
                       FROM tests t
                       JOIN reports r ON r.id = t.report_id
                       JOIN patients p ON p.id = r.patient_id
                       WHERE t.abnormal = TRUE
                       ORDER BY r.report_ref, t.test_name""",
                )
            rows = cur.fetchall()
        return [
            {"test_name": r[0], "value": r[1], "unit": r[2], "biomarker": r[3],
             "range_comparator": r[4], "range_min": r[5], "range_max": r[6],
             "report_ref": r[7], "patient_name": r[8]}
            for r in rows
        ]


# ── internal helpers ───────────────────────────────────

def _normalize_name(name: str) -> str:
    """Fold to uppercase ASCII."""
    name = name.upper().strip()
    name = re.sub(r"[^A-Z\s]", "", name)
    return re.sub(r"\s+", " ", name).strip()


def _parse_date(val: Any) -> date | None:
    if val is None or val == "":
        return None
    s = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%y", "%d.%m.%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

