import re
from pathlib import Path
import logging
from datetime import datetime, timezone

from .qr_reader import scan_qr_images
from .page_retriever import retrieve_page
from .link_parser import find_download_link
from .pdf_downloader import download_pdf
from .pdf_parser import PdfParser
from . import data_export

logger = logging.getLogger(__name__)

_REF_RE = re.compile(r"/r/(\d+)")


def _extract_ref(url: str) -> str | None:
    m = _REF_RE.search(url)
    return m.group(1) if m else None


def run_pipeline(qr_folder: str, download_dir: str) -> list[dict]:
    qr_results = scan_qr_images(qr_folder)
    if not qr_results:
        logger.warning("No QR images found in %s", qr_folder)
        return []

    overall = []
    for entry in qr_results:
        filename = entry["filename"]
        url = entry["url"]
        qr_error = entry["error"]

        report_ref = _extract_ref(url) if url else None

        record = {
            "source_image": filename,
            "qr_url": url,
            "report_ref": report_ref or "",
            "status": "error",
            "pdf_path": "",
            "error_message": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if qr_error:
            record["error_message"] = f"QR scan failed: {qr_error}"
            overall.append(record)
            logger.warning("[%s] %s", filename, record["error_message"])
            continue

        if not url:
            record["error_message"] = "No URL extracted from QR code"
            overall.append(record)
            continue

        logger.info("[%s] Processing URL: %s", filename, url)

        try:
            html = retrieve_page(url)
        except Exception as e:
            record["error_message"] = f"Page retrieval failed: {e}"
            overall.append(record)
            logger.error("[%s] %s", filename, record["error_message"])
            continue

        try:
            download_link = find_download_link(html, url)
        except Exception as e:
            record["error_message"] = f"Link parsing failed: {e}"
            overall.append(record)
            logger.error("[%s] %s", filename, record["error_message"])
            continue

        pdf_filename = f"{report_ref}.pdf" if report_ref else f"{Path(filename).stem}.pdf"

        try:
            pdf_path = download_pdf(download_link, download_dir, pdf_filename)
            record["status"] = "success"
            record["pdf_path"] = str(pdf_path.resolve())
            logger.info("[%s] PDF saved to %s", filename, pdf_path)
        except Exception as e:
            record["error_message"] = f"PDF download failed: {e}"
            overall.append(record)
            logger.error("[%s] %s", filename, record["error_message"])
            continue

        overall.append(record)

    return overall


def parse_pdfs(
    download_dir: str,
    output_dir: str,
    include_normes: bool = True,
    include_anteriors: bool = False,
) -> list[dict]:
    download_dir = Path(download_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(download_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDFs found in %s", download_dir)
        return []

    all_parsed = []
    for pdf_path in pdf_files:
        logger.info("Parsing: %s", pdf_path.name)
        parser = PdfParser(pdf_path)
        try:
            result = parser.parse()
        except Exception as e:
            logger.error("Failed to parse %s: %s", pdf_path.name, e)
            continue

        meta = result.get("metadata", {})
        n_tests = len(result.get("tests", []))
        n_abnormal = sum(1 for t in result.get("tests", []) if t.get("abnormal"))
        logger.info(
            "  \u2192 %s | %s | %s | %d tests, %d abnormal",
            meta.get("patient_name", "?"),
            meta.get("age", "?"),
            meta.get("sex", "?"),
            n_tests,
            n_abnormal,
        )

        all_parsed.append(result)

    # ── Per-patient output (one folder per patient) ──────────
    reports_dir = output_dir / "reports"
    for result in all_parsed:
        md_path, csv_path = data_export.write_patient_output(
            result, reports_dir,
            include_normes=include_normes,
            include_anteriors=include_anteriors,
        )
        logger.info("  \u2192 Patient folder: %s", md_path.parent.resolve())

    # ── Combined CSV ─────────────────────────────────────────
    csv_path = output_dir / "all_reports.csv"
    df = data_export.write_combined_csv(
        all_parsed, csv_path,
        include_normes=include_normes,
        include_anteriors=include_anteriors,
    )
    logger.info("  \u2192 CSV: %s (%d rows)", csv_path.resolve(), len(df))

    # ── Combined Markdown ────────────────────────────────────
    md_path = output_dir / "all_reports.md"
    data_export.write_combined_markdown(all_parsed, md_path)
    logger.info("  \u2192 Combined MD: %s", md_path.resolve())

    return all_parsed
