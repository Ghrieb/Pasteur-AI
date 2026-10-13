"""Capture purpose-built demo GIFs + screenshots of PasteurAI for the docs.

Scenario persona: Karim Benali arrives at the Institut Pasteur d'Algerie kiosk,
scans the QR code of his lab report, lets the AI analyse it, explores the
dashboard, asks the AI about his results, checks his history, and prints the
report. Each GIF is one chapter of that journey, with smooth scrolling and a
visible cursor so the viewer can follow along.

Prereqs:
    1. Frontend running:   cd frontend && npx vite --host   (port 5173)
    2. Run:                .venv\\Scripts\\python scripts\\capture.py

The backend is NOT required - every API call is mocked in the browser, and the
camera is replaced by a synthetic canvas stream that presents a real QR code
(so the actual scan -> detect -> process flow runs end to end).

Flags:
    --only 1,3,5   capture only these GIF scenarios (1-8)
    --no-gifs      skip GIF capture
    --no-shots     skip screenshot pass
    --fps N        GIF capture rate (default 10)
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import io
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import qrcode
from PIL import Image, ImageDraw, ImageStat, ImageChops
from playwright.async_api import async_playwright, Page, Route, BrowserContext

ROOT = Path(__file__).resolve().parent.parent
SHOTS_DIR = ROOT / "docs" / "screenshots"
GIFS_DIR = ROOT / "docs" / "gifs"
REPORT_JSON = ROOT / "output" / "all_reports.json"

BASE_URL = "http://localhost:5173"
REF = "53980"

VIEWPORT = {"width": 1280, "height": 800}
GIF_WIDTH = 800
GIF_COLORS = 255
DEDUP_THRESHOLD = 1.2  # mean abs diff (0-255) below which frames merge

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

AI_FINDINGS: list[dict[str, Any]] = [
    {
        "title": "Cytolyse hépatique modérée",
        "test": "Gamma GT",
        "value": "134 U/L",
        "range": "12 - 64 U/L",
        "severity": "critical",
        "explanation": (
            "Gamma GT nettement au-dessus de la normale (2x ULN), évoquant une "
            "choléstase ou une atteinte hépatocytaire médicamenteuse ou alcoolique."
        ),
        "recommendation": (
            "Consultation hépatologique, bilan biliaire complet et échographie "
            "abdominale sous 2 à 4 semaines."
        ),
        "confidence": 95,
    },
    {
        "title": "Carence en vitamine D",
        "test": "Vitamine D (25-OH Vit D)",
        "value": "23 ng/mL",
        "range": "> 30 ng/mL",
        "severity": "low",
        "explanation": (
            "25-OH vitamine D insuffisante au regard des seuils de l'OMS, associée "
            "à un risque accru d'ostéoporose."
        ),
        "recommendation": (
            "Supplémentation en cholécalciférol (100 000 UI/mois) et recontrôle à 3 mois."
        ),
        "confidence": 92,
    },
    {
        "title": "Pré-diabète (HbA1c)",
        "test": "HbA1c (Hb glyquée)",
        "value": "5,8 %",
        "range": "4 - 5,7 %",
        "severity": "elevated",
        "explanation": (
            "HbA1c légèrement au-dessus de la normale, en faveur d'une hyperglycémie "
            "modérée compatible avec un pré-diabète."
        ),
        "recommendation": (
            "Maintien du régime, activité physique et contrôle de la glycémie à jeun "
            "tous les 3 mois."
        ),
        "confidence": 88,
    },
    {
        "title": "Lymphocytose relative",
        "test": "P. Lymphocytes %",
        "value": "43 %",
        "range": "25 - 40 %",
        "severity": "elevated",
        "explanation": (
            "Part relative des lymphocytes légèrement élevée, souvent transitoire "
            "après infection virale récente."
        ),
        "recommendation": "NFS de contrôle dans 4 à 6 semaines.",
        "confidence": 84,
    },
    {
        "title": "Neutropénie relative",
        "test": "P. Neutrophiles %",
        "value": "48 %",
        "range": "50 - 75 %",
        "severity": "low",
        "explanation": (
            "Pourcentage de neutrophiles légèrement bas, en rapport avec la "
            "lymphocytose relative."
        ),
        "recommendation": "Pas de traitement; contrôle de la formule leucocytaire.",
        "confidence": 82,
    },
    {
        "title": "Hypophosphatasémie",
        "test": "Phosphatases alcalines",
        "value": "34 U/L",
        "range": "40 - 150 U/L",
        "severity": "low",
        "explanation": (
            "Phosphatases alcalines légèrement basses, souvent sans significativité "
            "clinique en l'absence d'autres anomalies."
        ),
        "recommendation": "Pas de prise en charge particulière.",
        "confidence": 80,
    },
    {
        "title": "Éosinopénie",
        "test": "P. Eosinophiles %",
        "value": "1,6 %",
        "range": "2 - 4 %",
        "severity": "low",
        "explanation": (
            "Éosinophiles légèrement bas, sans signification pathologique isolée."
        ),
        "recommendation": "Aucune action nécessaire.",
        "confidence": 78,
    },
]

SAMPLE_ANALYSIS = {
    "summary": (
        "7 anomalies détectées sur 45 biomarqueurs, dont une cytolyse hépatique "
        "marquée (Gamma GT à 134 U/L, 2x la normale), une carence en vitamine D "
        "et une HbA1c compatible avec un pré-diabète. Un contrôle hépatique dans "
        "3 mois est recommandé."
    ),
    "findings": AI_FINDINGS,
    "recommendations": [
        "Consultation hépatologique pour bilan de la cytolyse",
        "Supplémentation en vitamine D",
        "Surveillance régulière de l'HbA1c",
    ],
    "confidence": "high",
}

SAMPLE_SUMMARY = SAMPLE_ANALYSIS["summary"]

INTERPRET_ANSWERS = [
    (
        r"gamma|cytolyse|foie|hepat",
        (
            "Votre Gamma GT est à 134 U/L, soit 2 fois la normale (12-64 U/L). "
            "C'est le marqueur le plus inquiétant de ce bilan: il oriente vers une "
            "choléstase ou une irritation du foie (médicaments, alcool, stéatose). "
            "Bilan recommandé: bilan biliaire complet, échographie abdominale, et "
            "consultation hépatologique sous 2 à 4 semaines."
        ),
    ),
    (
        r"alt|alat",
        (
            "Votre ALAT (ALT) est à 18 U/L, dans les normes (< 55 U/L). Elle était "
            "cependant élevée lors des bilans précédents (72 U/L en janvier): la "
            "tendance est donc nettement à l'amélioration, à poursuivre avec le "
            "contrôle dans 3 mois."
        ),
    ),
    (
        r"vitamine",
        (
            "Votre 25-OH vitamine D est à 23 ng/mL (norme > 30 ng/mL): carence "
            "modérée selon l'OMS, associée à un risque accru d'ostéoporose. "
            "Supplémentation: 100 000 UI de cholécalciférol par mois pendant 3 mois, "
            "puis recontrôle."
        ),
    ),
    (
        r"hba1c|glyc|diab|sucre",
        (
            "Votre HbA1c est à 5,8 % (norme 4-5,7 %): c'est le stade pré-diabète. "
            "Avec une glycémie à jeun à 0,97 g/L, le risque de diabète de type 2 "
            "est réel mais réversible: activité physique régulière (150 min/semaine) "
            "et alimentation équilibrée suffisent souvent à normaliser cette valeur."
        ),
    ),
    (
        r"cholest|ldl|lipid",
        (
            "Votre profil lipidique est globalement rassurant: cholestérol total "
            "1,87 g/L (norme < 2,0), LDL 1,00 g/L (< 1,6), triglycérides 1,39 g/L "
            "(< 1,5). Rien d'urgent; maintenez une alimentation pauvre en graisses "
            "saturées."
        ),
    ),
]

DEFAULT_ANSWER = (
    "D'après votre rapport, 7 paramètres sortent des normes sur 45 analyses. "
    "Le point principal est la cytolyse hépatique (Gamma GT 134 U/L) à bilanter "
    "en priorité; viennent ensuite la carence en vitamine D et le pré-diabète "
    "(HbA1c 5,8 %). Voulez-vous que je détaille l'un de ces points?"
)

MINI_PDF = (
    b"%PDF-1.1\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)

HISTORY_PLAN = [
    ("2026-01-15", 180, {"GLU", "CHOL", "TG", "HBA1C", "CA", "UREA"}),
    ("2026-03-10", 158, {"CHOL", "TG", "HBA1C", "CA"}),
    ("2026-05-08", 145, {"HBA1C", "VITD"}),
    ("2026-06-08", 134, set()),
]


def make_report(base: dict) -> dict:
    r = copy.deepcopy(base)
    r["report_ref"] = REF
    return r


def make_history(base: dict) -> list[dict]:
    entries = []
    for i, (date, ggt, extra_abnormal) in enumerate(HISTORY_PLAN):
        r = copy.deepcopy(base)
        r["report_ref"] = REF
        r["dates"] = {"demande": date, "edition": date}
        for t in r["tests"]:
            if t.get("code") == "GGT":
                t["value"] = ggt
                t["value_display"] = f"{ggt}*"
                t["abnormal"] = True
            elif t.get("code") in extra_abnormal:
                t["abnormal"] = True
        entries.append(
            {
                "id": i + 1,
                "report_ref": REF,
                "date_edition": date,
                "raw_json": r,
            }
        )
    return entries


def qr_data_url(payload: str) -> str:
    import base64

    img = qrcode.make(payload, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def interpret_answer(query: str) -> str:
    q = (query or "").lower()
    for pattern, answer in INTERPRET_ANSWERS:
        if re.search(pattern, q):
            return answer
    return DEFAULT_ANSWER


# ---------------------------------------------------------------------------
# Fake camera (canvas stream presenting a real QR code to jsQR)
# ---------------------------------------------------------------------------

FAKE_CAMERA_JS = r"""
(() => {
  const QR_URL = "__QR_URL__";
  const canvas = document.createElement("canvas");
  canvas.width = 480; canvas.height = 360;
  const ctx = canvas.getContext("2d");
  const qrImg = new Image();
  qrImg.src = QR_URL;
  window.__showQr = false;
  window.__qrReady = false;
  qrImg.onload = () => { window.__qrReady = true; };
  let t = 0;
  function draw() {
    t += 1;
    const g = ctx.createLinearGradient(0, 0, 480, 360);
    g.addColorStop(0, "#0b1a2b"); g.addColorStop(1, "#071220");
    ctx.fillStyle = g; ctx.fillRect(0, 0, 480, 360);
    ctx.strokeStyle = "rgba(26,127,212,0.08)";
    ctx.lineWidth = 1;
    for (let x = 0; x < 480; x += 40) { ctx.beginPath(); ctx.moveTo(x + .5, 0); ctx.lineTo(x + .5, 360); ctx.stroke(); }
    for (let y = 0; y < 360; y += 40) { ctx.beginPath(); ctx.moveTo(0, y + .5); ctx.lineTo(480, y + .5); ctx.stroke(); }
    const sx = ((t * 2) % 580) - 50;
    const sg = ctx.createLinearGradient(sx, 0, sx + 100, 0);
    sg.addColorStop(0, "rgba(26,127,212,0)");
    sg.addColorStop(0.5, "rgba(26,127,212,0.10)");
    sg.addColorStop(1, "rgba(26,127,212,0)");
    ctx.fillStyle = sg; ctx.fillRect(0, 0, 480, 360);
    if (window.__showQr && window.__qrReady) {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(110, 45, 260, 260);
      ctx.drawImage(qrImg, 122, 57, 236, 236);
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
  const stream = canvas.captureStream(24);
  const fake = async () => stream;
  try {
    Object.defineProperty(navigator.mediaDevices, "getUserMedia", { value: fake, configurable: true });
  } catch (e) {
    navigator.mediaDevices.getUserMedia = fake;
  }
  try { delete window.SpeechRecognition; } catch (e) {}
  try { delete window.webkitSpeechRecognition; } catch (e) {}
})();
"""


# ---------------------------------------------------------------------------
# API mocks
# ---------------------------------------------------------------------------

class MockApi:
    def __init__(self, report: dict, history: list[dict], speed: dict):
        self.report = report
        self.history = history
        self.speed = speed  # {"process": 0.3, "ai": 0.3}

    async def handle(self, route: Route) -> None:
        req = route.request
        parsed = urlparse(req.url)
        path = parsed.path
        method = req.method.upper()

        async def ok(body: Any, content_type: str = "application/json", delay: float | None = None) -> None:
            wait = self.speed["ai"] if delay is None else delay
            await asyncio.sleep(wait)
            if isinstance(body, (bytes, bytearray)):
                await route.fulfill(status=200, content_type=content_type, body=bytes(body))
            else:
                await route.fulfill(
                    status=200, content_type=content_type, body=json.dumps(body)
                )

        if path == "/api/reports/process" and method == "POST":
            await ok(make_report(self.report), delay=self.speed["process"])
        elif path.startswith("/api/reports/") and method == "GET":
            await ok(make_report(self.report), delay=self.speed["process"])
        elif path == "/api/summarize-dashboard":
            await ok({"summary": SAMPLE_SUMMARY})
        elif path == "/api/analyze":
            await ok(SAMPLE_ANALYSIS)
        elif path == "/api/interpret":
            query = ""
            try:
                payload = json.loads(req.post_data or "{}")
                query = payload.get("query") or ""
            except Exception:
                pass
            await ok(
                {
                    "answer": interpret_answer(query),
                    "provider": "mock",
                    "model": "pasteurai-v3.1",
                }
            )
        elif path.endswith("/history"):
            await ok({"reports": self.history})
        elif path == "/api/print-pdf":
            await ok(MINI_PDF, content_type="application/pdf", delay=0.5)
        elif path == "/api/health":
            await ok({"status": "ok", "timestamp": ""})
        else:
            await asyncio.sleep(0.05)
            await route.fulfill(
                status=404, content_type="application/json", body='{"detail":"not mocked"}'
            )


# ---------------------------------------------------------------------------
# Cursor overlay + GIF encoding
# ---------------------------------------------------------------------------

CURSOR_PTS = [(0, 0), (0, 17), (4.2, 13.5), (7, 19.5), (9.5, 18.3), (6.7, 12.9), (11.5, 12.5)]


def _draw_cursor(img: Image.Image, x: float, y: float, s: float) -> None:
    pts = [(x + px * s, y + py * s) for px, py in CURSOR_PTS]
    draw = ImageDraw.Draw(img)
    outline = [(x + (px - 0.4) * s, y + (py - 0.4) * s) for px, py in CURSOR_PTS]
    draw.polygon(outline, fill=(255, 255, 255, 255))
    draw.polygon(pts, fill=(18, 28, 42, 255))


def _draw_ripples(img: Image.Image, x: float, y: float, age: float, s: float) -> None:
    if age < 0 or age > 0.5:
        return
    k = age / 0.5
    radius = (10 + 38 * k) * s
    alpha = int(200 * (1 - k))
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse(
        [x - radius, y - radius, x + radius, y + radius],
        outline=(120, 200, 255, alpha),
        width=max(2, int(3 * s)),
    )
    d.ellipse(
        [x - 3.5 * s, y - 3.5 * s, x + 3.5 * s, y + 3.5 * s],
        fill=(120, 200, 255, max(60, alpha)),
    )
    img.alpha_composite(overlay)


def build_gif(frames: list[tuple[Image.Image, float, tuple, list]], out_path: Path) -> tuple[int, int]:
    """frames: (RGB image at 1280px, timestamp s, mouse xy, clicks [(x,y,t)])"""
    if not frames:
        raise RuntimeError("no frames captured")

    rgb_kept: list[Image.Image] = []
    durations: list[int] = []
    prev_thumb: Image.Image | None = None
    pending_ms = 0

    w = GIF_WIDTH
    last_t = frames[0][1]
    for img, t, mouse, clicks in frames:
        pending_ms += max(40, int((t - last_t) * 1000))
        last_t = t
        h = int(img.height * w / img.width)
        resized = img.resize((w, h), Image.LANCZOS).convert("RGBA")
        s = (w / img.width)
        mx, my = mouse[0] * s, mouse[1] * s
        _draw_cursor(resized, mx, my, s * 1.1)
        for cx, cy, ct in clicks:
            _draw_ripples(resized, cx * s, cy * s, t - ct, s)
        flat = resized.convert("RGB")

        thumb = flat.convert("L").resize((96, 60))
        if prev_thumb is not None:
            diff = ImageStat.Stat(ImageChops.difference(thumb, prev_thumb)).mean[0]
        else:
            diff = 999.0

        if diff >= DEDUP_THRESHOLD or not rgb_kept:
            rgb_kept.append(flat)
            durations.append(pending_ms)
            prev_thumb = thumb
            pending_ms = 0
        else:
            # near-duplicate: keep previous image, remember to extend its slot
            durations[-1] += pending_ms
            pending_ms = 0

    # Shared palette across all frames, built with MAXCOVERAGE: median-cut
    # allocates palette entries by pixel population, so the UI's rare accent
    # colors (green ring, red/amber badges, ~1% of pixels) got mapped to navy
    # and the GIFs looked colorless. MAXCOVERAGE maximizes covered color
    # volume instead, so those accents earn palette entries. Frames are then
    # remapped with Floyd-Steinberg dithering, which keeps the dark gradient
    # backgrounds smooth (banding-free) while text stays crisp.
    sw = 400
    sh = int(rgb_kept[0].height * sw / rgb_kept[0].width)
    sheet = Image.new("RGB", (sw * len(rgb_kept), sh))
    for i, f in enumerate(rgb_kept):
        sheet.paste(f.resize((sw, sh), Image.LANCZOS), (i * sw, 0))
    palette = sheet.quantize(
        colors=GIF_COLORS, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE
    )

    images = [f.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG) for f in rgb_kept]
    durations = [max(60, d) for d in durations]
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"[debug] raw={len(frames)} kept={len(images)}", flush=True)
    return len(images), out_path.stat().st_size // 1024


# ---------------------------------------------------------------------------
# Recorder
# ---------------------------------------------------------------------------

class Recorder:
    def __init__(self, page: Page, fps: int = 10):
        self.page = page
        self.interval = 1.0 / fps
        self.frames: list[tuple[Image.Image, float, tuple, list]] = []
        self.mouse: tuple[float, float] = (VIEWPORT["width"] / 2, VIEWPORT["height"] / 2)
        self.clicks: list[tuple[float, float, float]] = []
        self._task: asyncio.Task | None = None
        self._t0 = 0.0

    async def start(self) -> None:
        self.frames.clear()
        self.clicks.clear()
        self._t0 = time.perf_counter()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while True:
            t = time.perf_counter() - self._t0
            try:
                buf = await self.page.screenshot(type="jpeg", quality=80)
                img = Image.open(io.BytesIO(buf)).convert("RGB")
                self.frames.append((img, t, self.mouse, list(self.clicks)))
            except Exception as exc:  # pragma: no cover - defensive
                print(f"    [warn] frame failed: {exc}")
            await asyncio.sleep(self.interval)

    def note_click(self, x: float, y: float) -> None:
        self.clicks.append((x, y, time.perf_counter() - self._t0))


# ---------------------------------------------------------------------------
# Interaction helpers (drive UI + record cursor)
# ---------------------------------------------------------------------------

async def tap(page: Page, rec: Recorder | None, locator, timeout: float = 8000) -> None:
    box = await locator.bounding_box()
    if box:
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        if rec:
            await page.mouse.move(x, y, steps=6)
            rec.mouse = (x, y)
            rec.note_click(x, y)
    await locator.click(timeout=timeout)


async def move(page: Page, rec: Recorder | None, x: float, y: float, steps: int = 10) -> None:
    await page.mouse.move(x, y, steps=steps)
    if rec:
        rec.mouse = (x, y)


async def hover_center(page: Page, rec: Recorder | None, locator, dy: float = 0.0) -> None:
    box = await locator.bounding_box()
    if not box:
        return
    x = box["x"] + box["width"] * 0.55
    y = box["y"] + box["height"] * 0.5 + dy
    await move(page, rec, x, y)


async def scroll_by(page: Page, rec: Recorder | None, px: int, steps: int = 8) -> None:
    await move(page, rec, VIEWPORT["width"] / 2, VIEWPORT["height"] / 2)
    per = px / steps
    for _ in range(steps):
        await page.mouse.wheel(0, per)
        await page.wait_for_timeout(60)
    if rec:
        rec.mouse = (VIEWPORT["width"] / 2, VIEWPORT["height"] / 2)
    await page.wait_for_timeout(250)


async def scroll_to(page: Page, rec: Recorder | None, target: int, steps: int = 10) -> None:
    current = await page.evaluate("() => window.scrollY")
    delta = target - current
    if abs(delta) < 8:
        return
    await scroll_by(page, rec, delta, steps=steps)


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

async def new_page(
    context: BrowserContext, api: MockApi, qr_url: str, freeze_particles: bool
) -> Page:
    page = await context.new_page()
    await page.add_init_script(FAKE_CAMERA_JS.replace("__QR_URL__", json.dumps(qr_url)[1:-1]))
    if freeze_particles:
        await page.add_init_script(
            """
            (() => {
              const stop = () => document.querySelectorAll('animate').forEach(a => a.remove());
              const obs = () => {
                stop();
                new MutationObserver(stop).observe(document.documentElement, {childList: true, subtree: true});
              };
              if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', obs);
              else obs();
            })();
            """
        )
    await page.route("**/api/**", api.handle)
    page.on("popup", lambda p: asyncio.create_task(_safe_close(p)))
    return page


async def _safe_close(p: Page) -> None:
    try:
        await p.close()
    except Exception:
        pass


async def goto_home(page: Page) -> None:
    await page.goto(BASE_URL, wait_until="networkidle")
    await page.wait_for_timeout(900)


async def reach_scan(page: Page) -> None:
    await goto_home(page)
    await page.get_by_role("button", name=re.compile("Commencer")).first.click()
    await page.wait_for_selector("text=Scanner votre QR Code", timeout=10000)
    await page.wait_for_timeout(700)


async def present_qr(page: Page, wait_ms: int = 300) -> None:
    await page.evaluate("() => { window.__showQr = true; }")
    await page.wait_for_timeout(wait_ms)


async def reach_dashboard(page: Page) -> None:
    await reach_scan(page)
    await present_qr(page, wait_ms=250)
    await page.wait_for_selector(
        "nav[aria-label='Navigation principale']", timeout=20000
    )
    await page.wait_for_timeout(1200)


async def open_section(page: Page, rec: Recorder | None, label: str) -> None:
    btn = page.locator(
        f"nav[aria-label='Navigation principale'] button[aria-label='{label}']"
    )
    await tap(page, rec, btn)


async def go_back(page: Page, rec: Recorder | None) -> None:
    await tap(page, rec, page.get_by_label("Retour").first)
    await page.wait_for_selector(
        "nav[aria-label='Navigation principale']", timeout=10000
    )
    await page.wait_for_timeout(700)


async def open_dashboard_tab(page: Page, rec: Recorder | None, name: str) -> None:
    await tap(page, rec, page.get_by_role("tab", name=name))
    await page.wait_for_timeout(900)


# ---------------------------------------------------------------------------
# GIF scenarios
# ---------------------------------------------------------------------------

async def scenario_onboarding(page: Page, rec: Recorder) -> None:
    """1. Home: language switch (FR->AR->FR) -> Commencer -> QR scan -> detected."""
    await goto_home(page)
    await page.wait_for_timeout(2400)  # entrance animation + toast must finish pre-record
    await rec.start()
    await tap(page, rec, page.get_by_role("button", name=re.compile("العربية")).first)
    await page.wait_for_timeout(2200)  # admire the RTL layout
    await tap(page, rec, page.get_by_role("button", name=re.compile("Français")).first)
    await page.wait_for_timeout(1200)
    await tap(page, rec, page.get_by_role("button", name=re.compile("Commencer")).first)
    await page.wait_for_selector("text=Scanner votre QR Code", timeout=10000)
    await page.wait_for_timeout(2600)  # scan-line animation
    await present_qr(page, wait_ms=350)
    await page.wait_for_selector("text=QR Code Détecté", timeout=8000)
    await page.wait_for_timeout(1600)  # green overlay + "Traitement..." status


async def scenario_processing(page: Page, rec: Recorder) -> None:
    """2. AI processing: 5-step checklist ticking, then landing on the dashboard."""
    await reach_scan(page)
    await rec.start()
    await present_qr(page, wait_ms=200)
    await page.wait_for_selector("text=Analyse en cours", timeout=10000)
    await page.wait_for_selector(
        "nav[aria-label='Navigation principale']", timeout=20000
    )
    await page.wait_for_timeout(1800)


async def scenario_dashboard(page: Page, rec: Recorder) -> None:
    """3. Dashboard tour: patient card -> score ring -> categories -> charts tab."""
    await reach_dashboard(page)
    await rec.start()
    await page.wait_for_timeout(1200)  # score ring animates in

    await hover_center(page, rec, page.locator("text=Résumé IA").first)
    await page.wait_for_timeout(700)

    await scroll_by(page, rec, 420)  # score ring + dot matrix
    await page.wait_for_timeout(700)
    await scroll_by(page, rec, 520)  # tab bar + category cards
    await page.wait_for_timeout(800)
    await scroll_to(page, rec, 900, steps=8)  # back to the tab bar
    await page.wait_for_timeout(400)

    await open_dashboard_tab(page, rec, "Graphiques")
    await scroll_by(page, rec, 300)
    await page.wait_for_timeout(600)

    wrappers = page.locator(".recharts-wrapper")
    if await wrappers.count() >= 2:
        await hover_center(page, rec, wrappers.nth(1))
        await page.wait_for_timeout(900)
        box = await wrappers.nth(1).bounding_box()
        if box:
            await move(page, rec, box["x"] + box["width"] * 0.3, box["y"] + box["height"] * 0.5)
            await page.wait_for_timeout(800)
    if await wrappers.count() >= 3:
        await hover_center(page, rec, wrappers.nth(2), dy=20)
        await page.wait_for_timeout(800)

    await scroll_to(page, rec, 0, steps=8)
    await open_dashboard_tab(page, rec, "Vue d'ensemble")
    await page.wait_for_timeout(600)


async def scenario_insights(page: Page, rec: Recorder) -> None:
    """4. AI insights: filters -> scroll findings -> ask the AI -> answer."""
    await reach_dashboard(page)
    await rec.start()
    await open_section(page, rec, "Analyses IA")
    await page.wait_for_selector("text=Assistant IA", timeout=15000)
    await page.wait_for_timeout(1200)

    await tap(page, rec, page.get_by_role("button", name=re.compile(r"^Critique")).first)
    await page.wait_for_timeout(1100)
    await tap(page, rec, page.get_by_role("button", name=re.compile(r"^Tous")).first)
    await page.wait_for_timeout(900)

    await scroll_by(page, rec, 500)
    await page.wait_for_timeout(700)
    await scroll_by(page, rec, 520)
    await page.wait_for_timeout(800)

    ask = page.get_by_role("button", name=re.compile("Demander à l'IA")).first
    await tap(page, rec, ask)
    await scroll_to(page, rec, 0, steps=10)
    await page.wait_for_timeout(2400)  # answer streams into the assistant card

    await scroll_by(page, rec, 700, steps=10)
    await page.wait_for_timeout(800)


async def scenario_anomalies(page: Page, rec: Recorder) -> None:
    """5. Anomalies -> collapse/expand -> open a marker -> detail + AI reading."""
    await reach_dashboard(page)
    await rec.start()
    await open_section(page, rec, "Anomalies")
    await page.wait_for_selector("text=anomalie", timeout=10000)
    await page.wait_for_timeout(1100)

    crit = page.get_by_role("button", name=re.compile(r"^Critique")).first
    await tap(page, rec, crit)  # collapse
    await page.wait_for_timeout(800)
    await tap(page, rec, crit)  # re-expand
    await page.wait_for_timeout(900)

    await scroll_by(page, rec, 380)
    await page.wait_for_timeout(700)

    row = page.locator("main button", has_text="Gamma GT").first
    await tap(page, rec, row)
    await page.wait_for_selector("text=Détail des biomarqueurs", timeout=10000)
    await page.wait_for_timeout(1300)

    side = page.locator("main button", has_text="Gamma GT").first
    await tap(page, rec, side)
    await page.wait_for_timeout(1000)

    await scroll_by(page, rec, 420)  # gauge -> bar chart
    await page.wait_for_timeout(900)
    await scroll_by(page, rec, 420)  # -> interpretation IA
    await page.wait_for_timeout(1200)


async def scenario_history(page: Page, rec: Recorder) -> None:
    """6. History: score evolution chart -> delta -> scroll the timeline."""
    await reach_dashboard(page)
    await rec.start()
    await open_section(page, rec, "Historique")
    await page.wait_for_selector("text=Évolution du score", timeout=10000)
    await page.wait_for_timeout(1200)

    area = page.locator(".recharts-area-area").first
    if await area.count():
        await hover_center(page, rec, page.locator(".recharts-wrapper").first)
        await page.wait_for_timeout(1100)

    await scroll_by(page, rec, 460)
    await page.wait_for_timeout(900)
    await scroll_by(page, rec, 520)
    await page.wait_for_timeout(1000)


async def scenario_print(page: Page, rec: Recorder) -> None:
    """7. Print/PDF: paper preview -> print -> success toast -> PDF."""
    await reach_dashboard(page)
    await rec.start()
    await open_section(page, rec, "Imprimer")
    await page.wait_for_selector("text=Score Santé", timeout=10000)
    await page.wait_for_timeout(1200)

    await move(page, rec, VIEWPORT["width"] / 2, VIEWPORT["height"] / 2 - 40)
    await page.wait_for_timeout(600)

    await tap(page, rec, page.locator("main button", has_text="Imprimer").first)
    await page.wait_for_timeout(2200)  # spinner + success toast

    await tap(page, rec, page.locator("main button", has_text="PDF").first)
    await page.wait_for_timeout(2000)  # spinner + second toast


async def scenario_voice(page: Page, rec: Recorder) -> None:
    """8. Voice assistant: suggested question chip -> mic -> scripted listening -> Q&A."""
    await reach_dashboard(page)
    await rec.start()
    await open_section(page, rec, "Assistant Vocal")
    await page.wait_for_selector("text=Assistant Vocal PasteurAI", timeout=10000)
    await page.wait_for_timeout(1000)

    chip = page.get_by_role("button", name=re.compile("mon cholestérol", re.I)).first
    await chip.scroll_into_view_if_needed()
    await tap(page, rec, chip)
    await page.wait_for_timeout(2600)  # question card + AI answer

    await tap(page, rec, page.locator("main button").first)  # mic (fallback path)
    await page.wait_for_timeout(3600)  # listening animation + question card
    await page.wait_for_timeout(2200)  # AI answer card


SCENARIOS = [
    ("01-onboarding-scan", scenario_onboarding),
    ("02-ai-processing", scenario_processing),
    ("03-dashboard-tour", scenario_dashboard),
    ("04-ai-insights", scenario_insights),
    ("05-anomalies-explorer", scenario_anomalies),
    ("06-history-timeline", scenario_history),
    ("07-print-export", scenario_print),
    ("08-voice-assistant", scenario_voice),
]


# ---------------------------------------------------------------------------
# Screenshot pass
# ---------------------------------------------------------------------------

async def screenshot_pass(browser, api: MockApi, qr_url: str) -> None:
    context = await browser.new_context(
        viewport=VIEWPORT, device_scale_factor=2
    )
    page = await new_page(context, api, qr_url, freeze_particles=False)
    shots: list[str] = []

    async def shot(name: str, full_page: bool = False) -> None:
        await page.screenshot(path=str(SHOTS_DIR / f"{name}.png"), full_page=full_page)
        shots.append(name)
        print(f"  [OK] {name}.png{' (full page)' if full_page else ''}")

    # 1. Home (FR) — wait out the startup toast
    await goto_home(page)
    await page.wait_for_timeout(4200)
    await shot("01-home")

    # 2. Home (AR) — RTL flip
    await tap(page, None, page.get_by_role("button", name=re.compile("العربية")).first)
    await page.wait_for_timeout(1400)
    await shot("02-home-arabic")
    await tap(page, None, page.get_by_role("button", name=re.compile("Français")).first)
    await page.wait_for_timeout(900)

    # 3. Scan (searching)
    await page.get_by_role("button", name=re.compile("Commencer")).first.click()
    await page.wait_for_selector("text=Scanner votre QR Code", timeout=10000)
    await page.wait_for_timeout(1400)
    await shot("03-scan")

    # 4. Scan — QR detected overlay
    await present_qr(page, wait_ms=200)
    await page.wait_for_selector("text=QR Code Détecté", timeout=8000)
    await page.wait_for_timeout(400)
    await shot("04-scan-qr-detected")

    # 5. Processing — mid checklist
    await page.wait_for_selector("text=Analyse en cours", timeout=10000)
    await page.wait_for_timeout(900)
    await shot("05-processing")

    # 6. Dashboard
    await page.wait_for_selector(
        "nav[aria-label='Navigation principale']", timeout=20000
    )
    await page.wait_for_timeout(2200)
    await shot("06-dashboard")
    await shot("07-dashboard-full", full_page=True)

    # 8. Dashboard — Graphiques tab
    await page.get_by_role("tab", name="Graphiques").click()
    await page.wait_for_timeout(1600)
    await shot("08-dashboard-charts")
    await page.get_by_role("tab", name="Vue d'ensemble").click()
    await page.wait_for_timeout(800)

    # 9. Insights
    await open_section(page, None, "Analyses IA")
    await page.wait_for_selector("text=Assistant IA", timeout=15000)
    await page.wait_for_timeout(1600)
    await shot("09-insights")

    # 10. Insights — AI Q&A answer
    await page.get_by_role("button", name=re.compile("Demander à l'IA")).first.click()
    await page.evaluate("() => window.scrollTo(0, 0)")
    await page.wait_for_timeout(2500)
    await shot("10-insights-qa")
    await shot("11-insights-full", full_page=True)

    # 12. Anomalies
    await page.get_by_label("Retour").first.click()
    await page.wait_for_selector(
        "nav[aria-label='Navigation principale']", timeout=10000
    )
    await open_section(page, None, "Anomalies")
    await page.wait_for_selector("text=anomalie", timeout=10000)
    await page.wait_for_timeout(1400)
    await shot("12-anomalies")

    # 13. Biomarker detail (via Gamma GT row — bugfixed mapping)
    await page.locator("main button", has_text="Gamma GT").first.click()
    await page.wait_for_selector("text=Détail des biomarqueurs", timeout=10000)
    await page.wait_for_timeout(1400)
    await shot("13-biomarker-detail")

    # 14. History
    await page.get_by_label("Retour").first.click()
    await page.wait_for_selector(
        "nav[aria-label='Navigation principale']", timeout=10000
    )
    await open_section(page, None, "Historique")
    await page.wait_for_selector("text=Évolution du score", timeout=10000)
    await page.wait_for_timeout(1400)
    await shot("14-history")

    # 15. Print preview
    await page.get_by_label("Retour").first.click()
    await page.wait_for_selector(
        "nav[aria-label='Navigation principale']", timeout=10000
    )
    await open_section(page, None, "Imprimer")
    await page.wait_for_selector("text=Score Santé", timeout=10000)
    await page.wait_for_timeout(1200)
    await shot("15-print")

    # 16. Print — success toast
    await page.locator("main button", has_text="Imprimer").first.click()
    await page.wait_for_timeout(1600)
    await shot("16-print-toast")

    # 17. Voice — listening state
    await page.get_by_label("Retour").first.click()
    await page.wait_for_selector(
        "nav[aria-label='Navigation principale']", timeout=10000
    )
    await open_section(page, None, "Assistant Vocal")
    await page.wait_for_selector("text=Assistant Vocal PasteurAI", timeout=10000)
    await page.wait_for_timeout(900)
    await page.locator("main button").first.click()
    await page.wait_for_timeout(1000)
    await shot("17-voice")

    # 18. Voice — Q&A answer
    await page.wait_for_timeout(4200)
    await shot("18-voice-answer")

    await context.close()
    print(f"\n  {len(shots)} screenshots written to docs/screenshots/")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(args: argparse.Namespace) -> None:
    base_reports = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    report = next((r for r in base_reports if r.get("report_ref") == REF), base_reports[0])
    history = make_history(report)
    qr_url = qr_data_url(f"pasteur://report/r/{REF}")

    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    GIFS_DIR.mkdir(parents=True, exist_ok=True)

    selected = None
    if args.only:
        selected = {int(x) for x in args.only.split(",")}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )

        if not args.no_shots:
            print("Screenshot pass:")
            api = MockApi(report, history, {"process": 0.6, "ai": 0.9})
            await screenshot_pass(browser, api, qr_url)

        if not args.no_gifs:
            print("\nGIF scenarios:")
            for idx, (name, fn) in enumerate(SCENARIOS, start=1):
                if selected and idx not in selected:
                    continue
                print(f"  [{idx}/8] {name} ...", flush=True)
                api = MockApi(report, history, {"process": 1.4, "ai": 1.1})
                context = await browser.new_context(viewport=VIEWPORT)
                page = await new_page(context, api, qr_url, freeze_particles=True)
                rec = Recorder(page, fps=args.fps)
                try:
                    await fn(page, rec)
                finally:
                    await rec.stop()
                n_frames, size_kb = build_gif(
                    rec.frames, GIFS_DIR / f"{name}.gif"
                )
                print(f"         -> {name}.gif ({n_frames} frames, {size_kb} KB)")
                await context.close()

        await browser.close()

    print("\nDone — see docs/screenshots/ and docs/gifs/")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="comma-separated scenario numbers (1-8)")
    parser.add_argument("--no-gifs", action="store_true")
    parser.add_argument("--no-shots", action="store_true")
    parser.add_argument("--fps", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
