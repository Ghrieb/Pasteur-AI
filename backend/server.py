"""PasteurAI — FastAPI Backend Server

Provides the API layer for the frontend, wrapping the existing
Python pipeline, AI interpreter, and database.
"""

import json
import logging
import os
import subprocess
import sys
import re as re_module
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from backend.pdf_generator import generate_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("pasteur-backend")

BACKEND_DIR = Path(__file__).parent
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

sys.path.insert(0, str(PROJECT_DIR))

_REF_RE = re_module.compile(r"/r/(\d+)")


def _find_qr_url(ref: str) -> str | None:
    from src.qr_reader import scan_qr_images
    qr_folder = PROJECT_DIR / "QrCodes"
    if not qr_folder.exists():
        return None
    for entry in scan_qr_images(str(qr_folder)):
        url = entry.get("url")
        if url and ref in url:
            return url
    return None


def _process_report(url: str, report_ref: str) -> dict | None:
    from src.page_retriever import retrieve_page
    from src.link_parser import find_download_link
    from src.pdf_downloader import download_pdf
    from src.pdf_parser import PdfParser
    from src.data_export import export_json
    from src.biomarker_registry import attach_codes_to_report
    from src import data_export as dx

    download_dir = PROJECT_DIR / "downloads"
    output_dir = PROJECT_DIR / "output"
    download_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    html = retrieve_page(url)
    download_link = find_download_link(html, url)
    pdf_path = download_pdf(download_link, str(download_dir), f"{report_ref}.pdf")
    if not pdf_path:
        return None

    parser = PdfParser(str(pdf_path))
    parsed = parser.parse()
    if not parsed:
        return None

    report_json = export_json(parsed)
    report_json = attach_codes_to_report(report_json)

    json_path = output_dir / "all_reports.json"
    reports = []
    if json_path.exists():
        reports = json.loads(json_path.read_text(encoding="utf-8"))
        for r in reports:
            if r.get("report_ref") == report_json.get("report_ref"):
                return r
    reports.append(report_json)
    json_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

    return report_json


# ── Models ──────────────────────────────────────────────

class InterpretRequest(BaseModel):
    reportJson: dict
    query: str = ""
    language: str = "fr"
    provider: str = "groq"
    model: str = "llama-3.1-8b-instant"


class InterpretResponse(BaseModel):
    answer: str
    provider: str
    model: str


class AnalysisRequest(BaseModel):
    reportJson: dict
    language: str = "fr"


class AnalysisFinding(BaseModel):
    title: str = ""
    test: str = ""
    value: str = ""
    range: str = ""
    severity: str = "normal"
    explanation: str = ""
    recommendation: str = ""
    confidence: int = 0


class AnalysisResponse(BaseModel):
    summary: str
    findings: list[AnalysisFinding]
    recommendations: list[str]
    confidence: str


class SummaryRequest(BaseModel):
    reportJson: dict
    language: str = "fr"


class SummaryResponse(BaseModel):
    summary: str


class ProcessRequest(BaseModel):
    url: str
    report_ref: str = ""


# ── Lifecycle ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PasteurAI backend starting...")
    yield
    logger.info("PasteurAI backend shutting down.")


app = FastAPI(title="PasteurAI Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── AI Engine wrapper ──────────────────────────────────

_ai_engine = None


def get_ai_engine():
    global _ai_engine
    if _ai_engine is None:
        from src.ai_interpreter import AIInterpreter
        _ai_engine = AIInterpreter()
    return _ai_engine


# ── Routes ─────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/interpret", response_model=InterpretResponse)
async def interpret(req: InterpretRequest):
    engine = get_ai_engine()
    answer = engine.interpret(req.reportJson, query=req.query, language=req.language)
    return InterpretResponse(answer=answer, provider=req.provider, model=req.model)


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalysisRequest):
    engine = get_ai_engine()
    result = engine.analyze(req.reportJson, language=req.language)
    return AnalysisResponse(
        summary=result.get("summary", ""),
        findings=[AnalysisFinding(**f) for f in result.get("findings", [])],
        recommendations=result.get("recommendations", []),
        confidence=result.get("confidence", "low"),
    )


@app.post("/api/summarize-dashboard", response_model=SummaryResponse)
async def summarize_dashboard(req: SummaryRequest):
    engine = get_ai_engine()
    summary = engine.summarizeDashboard(req.reportJson, language=req.language)
    return SummaryResponse(summary=summary)


def _load_all_reports():
    json_path = PROJECT_DIR / "output" / "all_reports.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    return []


@app.get("/api/reports/{report_ref}")
async def get_report(report_ref: str):
    reports = _load_all_reports()
    for r in reports:
        if r.get("report_ref") == report_ref:
            return r
    qr_url = _find_qr_url(report_ref)
    if qr_url:
        logger.info("Report %s not cached. Auto-processing from %s", report_ref, qr_url)
        try:
            report = _process_report(qr_url, report_ref)
            if report:
                return report
        except Exception as e:
            logger.error("Auto-process failed for %s: %s", report_ref, e)
    return {"error": "Report not found"}, 404


@app.post("/api/reports/process", status_code=201)
async def process_report(req: ProcessRequest):
    ref = req.report_ref or _REF_RE.search(req.url)
    ref = ref.group(1) if isinstance(ref, re_module.Match) else ref
    if not ref:
        return {"error": "Could not determine report reference from URL"}, 400
    existing = _load_all_reports()
    for r in existing:
        if r.get("report_ref") == ref:
            return r
    try:
        report = _process_report(req.url, ref)
        if not report:
            return {"error": "Report processing failed"}, 500
        return report
    except Exception as e:
        logger.error("Process request failed: %s", e)
        return {"error": f"Processing failed: {e}"}, 500


@app.get("/api/patients/{name}/history")
async def get_patient_history(name: str):
    try:
        dsn = os.environ.get("PASTEUR_DSN")
        if dsn:
            from src.database import PasteurDB
            db = PasteurDB(dsn)
            reports = db.get_patient_reports(name)
            return {"reports": reports}
    except Exception as e:
        logger.warning("History lookup failed (DB not available): %s", e)
    return {"reports": []}


@app.post("/api/print-pdf")
async def print_pdf(data: dict):
    report_ref = data.get("report_ref", "")
    reports = _load_all_reports()
    report = next((r for r in reports if r.get("report_ref") == report_ref), None)
    if not report:
        return {"error": "Report not found"}, 404
    pdf_bytes = generate_pdf(report)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="rapport-{report_ref}.pdf"'}
    )


@app.get("/api/biomarkers/{code}")
async def get_biomarker(code: str):
    from src.biomarker_registry import CODE_TO_ENTRY
    entry = CODE_TO_ENTRY.get(code)
    if entry:
        return entry
    return {"error": "Not found"}, 404


@app.get("/api/admin/status")
async def admin_status():
    return {
        "backend": "online",
        "version": "1.0.0",
        "uptime": "0:00:00",
    }


@app.get("/api/admin/ai/status")
async def admin_ai_status():
    engine = get_ai_engine()
    return {"connected": engine.client is not None}


@app.post("/api/admin/exit-kiosk")
async def admin_exit_kiosk():
    logger.warning("Exit kiosk requested")
    return {"status": "ok"}


@app.post("/api/admin/restart")
async def admin_restart():
    logger.warning("Restart requested")
    return {"status": "ok"}


@app.post("/api/admin/shutdown")
async def admin_shutdown():
    logger.warning("Shutdown requested")
    return {"status": "ok"}


@app.get("/api/admin/logs")
async def admin_logs(type: str | None = None):
    log_file = PROJECT_DIR / "backend.log"
    logs = []
    if log_file.exists():
        with open(log_file, encoding="utf-8") as f:
            for line in f.readlines()[-200:]:
                logs.append(line.rstrip())
    if type:
        logs = [l for l in logs if f"[{type.upper()}]" in l]
    return {"logs": logs}


@app.post("/api/admin/printer/connect")
async def printer_connect():
    logger.info("Printer connect requested")
    return {"status": "connected"}


@app.post("/api/admin/printer/test")
async def printer_test():
    return {"status": "printed"}


@app.get("/api/admin/printer/status")
async def printer_status():
    return {"connected": True, "paper": "ok", "model": "Epson TM-T88"}


@app.post("/api/admin/printer/print")
async def printer_print(data: dict):
    logger.info("Print: %s", data.get("text", "")[:80])
    return {"status": "printed"}


@app.post("/api/admin/printer/print-summary")
async def printer_print_summary(data: dict):
    logger.info("Print summary for report: %s", data.get("report", {}).get("report_ref", ""))
    return {"status": "printed"}


@app.post("/api/admin/maintenance/clear-cache")
async def clear_cache():
    return {"status": "ok"}


@app.post("/api/admin/maintenance/clear-pdfs")
async def clear_pdfs():
    return {"status": "ok"}


# ── WebSocket logs ─────────────────────────────────────

@app.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_json({"type": "log", "message": "Log stream active"})
    except WebSocketDisconnect:
        pass


# ── Main ───────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
