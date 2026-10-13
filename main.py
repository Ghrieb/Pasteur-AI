#!/usr/bin/env python3
"""PasteurAI — Pipeline CLI

Usage:
    python main.py                  # Full pipeline (download → parse → export)
    python main.py download         # Phase 1: QR → PDF
    python main.py parse            # Phase 2: PDF → CSV + MD + JSON
    python main.py json             # Phase 2b: PDF → JSON only (AI-ready)
    python main.py filter           # Phase 3: filter combined CSV
    python main.py db-init          # Phase 3: init PostgreSQL schema
    python main.py db-store         # Phase 3: store parsed JSON into PostgreSQL
    python main.py ai               # Phase D: AI explanation of lab report
    python main.py ai "..." --lang ar --dsn postgresql://...  # Ask in Arabic with history
"""

import argparse
import io
import json
import logging
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd

from src.pipeline import run_pipeline, parse_pdfs
from src import data_export
from src import data_filter
from src.biomarker_registry import attach_codes_to_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _prompt_yes_no(prompt: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter Y or N.")


def _count_success(results: list[dict]) -> int:
    return sum(1 for r in results if r["status"] == "success")


# ── Phase 1: Download ──────────────────────────────────

def cmd_download(args):
    qr_folder = Path(getattr(args, "qr_folder", "QrCodes"))
    download_dir = Path(getattr(args, "download_dir", "downloads"))
    output_path = Path(getattr(args, "output", "output/results.csv"))

    download_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("PasteurAI — Starting download pipeline from %s", qr_folder.resolve())
    results = run_pipeline(str(qr_folder), str(download_dir))

    if not results:
        logger.warning("No results to report.")
        return results

    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info("Download log written to %s", output_path.resolve())

    success = _count_success(results)
    errors = len(results) - success
    total = len(results)
    logger.info("Done — %d/%d succeeded, %d/%d failed", success, total, errors, total)

    if errors > 0:
        for f in (r for r in results if r["status"] == "error"):
            logger.info("  %s → %s", f["source_image"], f["error_message"])
    return results


# ── Phase 2: Parse + Export ────────────────────────────

def cmd_parse(args):
    download_dir = Path(getattr(args, "download_dir", "downloads"))
    output_dir = Path(getattr(args, "output_dir", "output"))
    export_json = getattr(args, "json", False)

    include_normes = getattr(args, "include_normes", None)
    if include_normes is None:
        include_normes = _prompt_yes_no("Include Normes in CSV?", default=True)
    include_anteriors = getattr(args, "include_anteriors", None)
    if include_anteriors is None:
        include_anteriors = _prompt_yes_no("Include Antériorités in CSV?", default=False)

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("PasteurAI — Parsing PDFs from %s", download_dir.resolve())

    parsed_list = parse_pdfs(
        str(download_dir), str(output_dir),
        include_normes=include_normes,
        include_anteriors=include_anteriors,
    )

    if not parsed_list:
        logger.warning("No reports parsed.")
        return

    # ── Combined JSON (AI‑ready) ─────────────────────────
    json_path = output_dir / "all_reports.json"
    payload = []
    for p in parsed_list:
        report_json = data_export.export_json(p)
        report_json = attach_codes_to_report(report_json)
        payload.append(report_json)

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("  → JSON: %s (%d reports, %d total tests)",
                json_path.resolve(), len(payload),
                sum(len(r["tests"]) for r in payload))

    # ── Optional: store into PostgreSQL ─────────────────
    dsn = getattr(args, "dsn", None)
    if dsn:
        from src.database import PasteurDB
        db = PasteurDB(dsn)
        for r in payload:
            result = db.store_report(r, raw_json=r)
            logger.info("  Stored report %s → patient_id=%s report_id=%s (%d tests)",
                        r["report_ref"], result["patient_id"], result["report_id"],
                        result["test_count"])
        logger.info("Stored %d report(s) into PostgreSQL.", len(payload))

    # ── Per-patient JSON ─────────────────────────────────
    if export_json:
        reports_dir = output_dir / "reports"
        for p, parsed in zip(payload, parsed_list):
            folder = data_export._make_patient_folder_name(parsed)
            jpath = reports_dir / folder / "report.json"
            jpath.parent.mkdir(parents=True, exist_ok=True)
            jpath.write_text(
                json.dumps(p, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        logger.info("  → Per-patient JSON: %s/reports/*/report.json", output_dir)

    logger.info("Parse pipeline finished — %d report(s) processed", len(parsed_list))


def cmd_json(args):
    """Shortcut: parse + JSON export only."""
    args.include_normes = True
    args.include_anteriors = True
    args.json = True
    cmd_parse(args)


# ── Phase 3: Filter ────────────────────────────────────

def cmd_filter(args):
    output_dir = Path(getattr(args, "output_dir", "output"))
    input_path = output_dir / "all_reports.csv"

    if not input_path.exists():
        logger.error("No combined CSV at %s. Run 'parse' first.", input_path.resolve())
        return

    df = data_filter.read_combined_csv(str(input_path))
    logger.info("Loaded %d rows from %d patient(s)", len(df), df["patient_name"].nunique())

    pipeline = data_filter.build_pipeline_from_args(args)
    if pipeline.empty():
        logger.info("No filters specified. Use --abnormal-only, --section, etc.")
        return

    filtered = pipeline.run(df)
    logger.info("Filtered to %d rows", len(filtered))

    if len(filtered) == 0:
        logger.warning("No rows match.")
        return

    custom_output = getattr(args, "output", None)
    if custom_output:
        output_path = Path(custom_output)
    else:
        filtered_dir = output_dir / "filtered"
        filtered_dir.mkdir(parents=True, exist_ok=True)
        output_path = filtered_dir / pipeline.suggest_filename()
    data_filter.write_filtered_csv(filtered, str(output_path))
    logger.info("Filtered CSV → %s", output_path.resolve())


# ── Phase 3: Database ──────────────────────────────────

def cmd_db_init(args):
    dsn = getattr(args, "dsn", None) or input("PostgreSQL DSN: ").strip()
    from src.database import PasteurDB
    db = PasteurDB(dsn)
    db.init_schema()
    logger.info("PostgreSQL schema initialized.")
    count = db.seed_biomarkers()
    logger.info("Seeded %d biomarker(s) into reference table.", count)


def cmd_db_store(args):
    dsn = getattr(args, "dsn", None)
    json_path = Path(getattr(args, "json_path", "output/all_reports.json"))

    if not json_path.exists():
        logger.error("JSON not found at %s", json_path.resolve())
        return

    reports = json.loads(json_path.read_text(encoding="utf-8"))
    from src.database import PasteurDB
    db = PasteurDB(dsn)

    stored = []
    for r in reports:
        result = db.store_report(r, raw_json=r)
        stored.append(result)
        logger.info("  Stored report %s → patient_id=%s report_id=%s (%d tests)",
                    r["report_ref"], result["patient_id"], result["report_id"],
                    result["test_count"])

    logger.info("Stored %d report(s) into PostgreSQL.", len(stored))


# ── Phase D: AI Interpreter ────────────────────────────

def cmd_ai(args):
    json_path = Path(getattr(args, "json_path", "output/all_reports.json"))
    report_ref = getattr(args, "report_ref", None)
    query = args.query or ""
    language = getattr(args, "lang", "fr")

    if not json_path.exists():
        logger.error("JSON not found at %s", json_path.resolve())
        return

    reports = json.loads(json_path.read_text(encoding="utf-8"))

    if report_ref:
        report = next((r for r in reports if r["report_ref"] == report_ref), None)
        if not report:
            logger.error("Report %s not found in JSON", report_ref)
            return
    elif len(reports) == 1:
        report = reports[0]
    else:
        report = reports[-1]
        logger.info("Using most recent report: %s (--report-ref to specify)", report["report_ref"])

    dsn = getattr(args, "dsn", None)
    db = None
    if dsn:
        from src.database import PasteurDB
        db = PasteurDB(dsn)

    from src.ai_interpreter import AIInterpreter
    interpreter = AIInterpreter(db=db)
    answer = interpreter.interpret(report, query=query, language=language)
    print(answer)


# ── Full pipeline ──────────────────────────────────────

def cmd_full(args):
    cmd_download(args)
    args.include_normes = _prompt_yes_no("Include Normes in CSV?", default=True)
    args.include_anteriors = _prompt_yes_no("Include Antériorités in CSV?", default=False)
    args.json = True
    cmd_parse(args)

    output_dir = Path(getattr(args, "output_dir", "output"))
    csv_path = output_dir / "all_reports.csv"
    if csv_path.exists():
        df = data_filter.read_combined_csv(str(csv_path))
        if _prompt_yes_no("Apply filters?", default=False):
            pipeline = data_filter.build_pipeline_from_interactive(df)
            if not pipeline.empty():
                filtered = pipeline.run(df)
                if len(filtered) > 0:
                    default_name = pipeline.suggest_filename()
                    out_path = data_filter._prompt_output_path(default_name, output_dir)
                    data_filter.write_filtered_csv(filtered, str(out_path))
                    logger.info("Filtered CSV → %s", out_path.resolve())


# ── CLI ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PasteurAI — Institut Pasteur report processing pipeline"
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # download
    dl = sub.add_parser("download", help="Phase 1: QR → PDF")
    dl.add_argument("--qr-folder", default="QrCodes")
    dl.add_argument("--download-dir", default="downloads")
    dl.add_argument("--output", default="output/results.csv")

    # parse
    pr = sub.add_parser("parse", help="Phase 2: PDF → CSV + MD + JSON")
    pr.add_argument("--download-dir", default="downloads")
    pr.add_argument("--output-dir", default="output")
    pr.add_argument("--include-normes", action=argparse.BooleanOptionalAction, default=None)
    pr.add_argument("--include-anteriors", action=argparse.BooleanOptionalAction, default=None)
    pr.add_argument("--json", action="store_true", help="Write per-patient JSON")
    pr.add_argument("--dsn", default=None, help="PostgreSQL DSN (auto-store if set)")

    # json shortcut
    js = sub.add_parser("json", help="Phase 2b: PDF → JSON (AI-ready)")
    js.add_argument("--download-dir", default="downloads")
    js.add_argument("--output-dir", default="output")
    js.add_argument("--dsn", default=None, help="PostgreSQL DSN (auto-store if set)")

    # filter
    fl = sub.add_parser("filter", help="Phase 3: filter CSV")
    fl.add_argument("--output-dir", default="output")
    fl.add_argument("--output", default=None)
    scope_grp = fl.add_argument_group("scope")
    scope_grp.add_argument("--patient", default=None)
    scope_grp.add_argument("--report-ref", nargs="+", default=None)
    scope_grp.add_argument("--demande-id", nargs="+", default=None)
    filt_grp = fl.add_argument_group("row filters")
    filt_grp.add_argument("--abnormal-only", action="store_true")
    filt_grp.add_argument("--section", nargs="+", default=None)
    filt_grp.add_argument("--test-name", default=None)
    filt_grp.add_argument("--sex", choices=["Male", "Female"], default=None)
    filt_grp.add_argument("--min-age", type=int, default=None)
    filt_grp.add_argument("--max-age", type=int, default=None)
    filt_grp.add_argument("--anteriority-only", action="store_true")

    # database
    db = sub.add_parser("db-init", help="Initialize PostgreSQL schema")
    db.add_argument("--dsn", default=None)

    ds = sub.add_parser("db-store", help="Store parsed JSON into PostgreSQL")
    ds.add_argument("--dsn", default=None)
    ds.add_argument("--json-path", default="output/all_reports.json")

    # ai
    ai = sub.add_parser("ai", help="Phase D: AI explanation of lab report")
    ai.add_argument("query", nargs="?", default="", help="Patient's question")
    ai.add_argument("--report-ref", default=None, help="Specific report reference to explain")
    ai.add_argument("--json-path", default="output/all_reports.json")
    ai.add_argument("--lang", default="fr", choices=["fr", "ar", "en"],
                    help="Answer language")
    ai.add_argument("--dsn", default=None, help="PostgreSQL DSN (for history)")

    args = parser.parse_args()

    commands = {
        None: cmd_full,
        "download": cmd_download,
        "parse": cmd_parse,
        "json": cmd_json,
        "filter": cmd_filter,
        "db-init": cmd_db_init,
        "db-store": cmd_db_store,
        "ai": cmd_ai,
    }
    cmd = commands.get(args.command, cmd_full)
    cmd(args)


if __name__ == "__main__":
    main()
