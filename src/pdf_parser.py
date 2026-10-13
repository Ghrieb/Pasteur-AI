import logging
import re
from pathlib import Path
from pypdf import PdfReader

logger = logging.getLogger(__name__)


_PATIENT_RE = re.compile(
    r"Patient\s*:\s*(.+?)\s+(\d+)\s*ans\s*[-:]\s*([MF])"
)
_DEMANDE_RE = re.compile(r"Demande\s*N[°o]\s*:\s*(.+)")
_DATE_DEMANDE_RE = re.compile(r"Date de demande\s*:\s*(.+)")
_DATE_EDITION_RE = re.compile(r"Date d'[eé]dition\s*:\s*(.+)")
_DATE_CTX_RE = re.compile(r"^\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}$")
_QR_REF_RE = re.compile(r"^\d{4,6}$")
_METHODOLOGY_RE = re.compile(r"^\((.+)\)\s*$")
_ANTERIORITY_RE = re.compile(r"^\d+\.?\d*$")
_RANGE_ONLY_RE = re.compile(r"^\d+\.?\d*\s*-\s*\d+\.?\d*$")
_PAGE_HEADER_RE = re.compile(
    r"^(?:D\.\s*N|Patient\s*:|Date de demande|Date d'[eé]dition)"
)
_FOOTER_RE = re.compile(r"(?:Rue Omar|pasteur\.dz)")
_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
_SKIP_LINES = {
    "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE",
    "Laboratoire de Biologie Médicale",
    "Compte Rendu d'Analyse",
    "Unit\u00e9s Normes Ant\u00e9riorit\u00e9s",
}
_MAIN_SECTIONS = {
    "H\u00e9matologie", "Hormonologie", "Marqueurs tumoraux",
    "Biochimie", "Bact\u00e9riologie", "S\u00e9rologie",
    "Immunologie", "Parasitologie", "Virologie",
}
_INTERP_MARKERS = {"Normale", "Carence", "Diab\u00e8te", "Potentiel",
                   "Pr\u00e9-diab\u00e8te", "Augmentation", "Diminution"}


def _is_section_header(ls: str) -> bool:
    if len(ls) < 3:
        return False
    if ls[0].islower() or ls[0].isdigit():
        return False
    if any(c.isdigit() for c in ls):
        return False
    words = ls.split()
    if len(words) > 4:
        return False
    if _METHODOLOGY_RE.match(ls):
        return False
    if ls in _SKIP_LINES:
        return False
    return True


def _is_number(token: str) -> bool:
    try:
        float(token.replace(",", "."))
        return True
    except (ValueError, TypeError):
        return False


def _strip_bom(s: str) -> str:
    return s.lstrip("\ufeff")


class PdfParser:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        self.raw_lines: list[str] = []
        self.metadata: dict = {}
        self.tests: list[dict] = []
        self.interpretations: list[str] = []

    # ── public API ──────────────────────────────────────────────

    def parse(self) -> dict:
        self._extract_text()
        self._classify_and_build()
        self._mark_abnormal()
        return self._build_result()

    # ── text extraction ─────────────────────────────────────────

    def _extract_text(self):
        reader = PdfReader(self.pdf_path)
        raw = ""
        for page in reader.pages:
            raw += page.extract_text() + "\n"
        lines = [_strip_bom(l).strip() for l in raw.split("\n")]
        self.raw_lines = [l for l in lines if l]

    # ── classification & build ──────────────────────────────────

    def _classify_and_build(self):
        current_section = ""
        current_sub = ""
        current_methodology = ""
        meta_extracted = False
        qr_ref_extracted = False

        for line in self.raw_lines:
            ls = line

            # ── metadata (page 1 only) ──────────────────────
            if not meta_extracted:
                m = _DEMANDE_RE.search(ls)
                if m and "demande_id" not in self.metadata:
                    self.metadata["demande_id"] = m.group(1).strip()
                    continue
                m = _PATIENT_RE.search(ls)
                if m and "patient_name" not in self.metadata:
                    raw_name = m.group(1).strip()
                    self.metadata["patient_name"] = re.sub(r"\s+", " ", raw_name)
                    self.metadata["age"] = int(m.group(2))
                    self.metadata["sex"] = "Male" if m.group(3) == "M" else "Female"
                    continue
                m = _DATE_DEMANDE_RE.search(ls)
                if m and "date_demande" not in self.metadata:
                    self.metadata["date_demande"] = m.group(1).strip()
                    continue
                m = _DATE_EDITION_RE.search(ls)
                if m and "date_edition" not in self.metadata:
                    self.metadata["date_edition"] = m.group(1).strip()
                    continue
                if _QR_REF_RE.match(ls) and not qr_ref_extracted:
                    self.metadata["report_ref"] = ls
                    qr_ref_extracted = True
                    continue
                if len(self.metadata) >= 6:
                    meta_extracted = True

            # ── skip lines ──────────────────────────────────
            if _ARABIC_RE.search(ls):
                continue
            if _PAGE_HEADER_RE.match(ls):
                continue
            if ls in _SKIP_LINES:
                continue
            if _FOOTER_RE.search(ls):
                continue
            if _QR_REF_RE.match(ls):
                continue

            # ── date (anteriority date) ─────────────────────
            if _DATE_CTX_RE.match(ls):
                if (self.tests
                        and self.tests[-1].get("anteriority")
                        and not self.tests[-1].get("anteriority_date")):
                    self.tests[-1]["anteriority_date"] = ls
                continue

            # ── section header ──────────────────────────────
            if ls in _MAIN_SECTIONS or _is_section_header(ls):
                if ls not in _MAIN_SECTIONS:
                    logger.info("Auto-detected new section: %s", ls)
                current_section = ls
                current_sub = ""
                current_methodology = ""
                continue

            # ── interpretation line ─────────────────────────
            if self._is_interpretation(ls):
                self.interpretations.append(ls)
                continue

            # ── methodology (parenthetical) ─────────────────
            m = _METHODOLOGY_RE.match(ls)
            if m:
                meth = m.group(1).strip()
                current_methodology = meth
                if (self.tests
                        and self.tests[-1].get("section") == current_section
                        and self.tests[-1].get("sub_section") == current_sub):
                    self.tests[-1]["methodology"] = meth
                continue

            # ── standalone anteriority ──────────────────────
            if _ANTERIORITY_RE.match(ls) and len(ls.split()) == 1:
                if self.tests:
                    self.tests[-1]["anteriority"] = ls
                continue

            # ── standalone range ────────────────────────────
            if _RANGE_ONLY_RE.match(ls):
                if self.tests:
                    self.tests[-1]["secondary_range"] = ls
                continue

            # ── sub-section ─────────────────────────────────
            if self._is_sub_section(ls):
                current_sub = ls
                current_methodology = ""
                continue

            # ── test line ───────────────────────────────────
            parsed = self._parse_test_line(ls)
            if parsed:
                parsed["section"] = current_section
                parsed["sub_section"] = current_sub
                if not parsed.get("methodology"):
                    parsed["methodology"] = current_methodology
                if not parsed.get("anteriority"):
                    parsed["anteriority"] = None
                if not parsed.get("anteriority_date"):
                    parsed["anteriority_date"] = None
                if not parsed.get("secondary_range"):
                    parsed["secondary_range"] = ""
                self.tests.append(parsed)

    # ── helpers ────────────────────────────────────────────────

    def _is_interpretation(self, ls: str) -> bool:
        if " : " not in ls:
            return False
        # Must contain at least one digit on the left side of ":"
        left = ls.split(" : ", 1)[0]
        if not any(c.isdigit() for c in left):
            return False
        # Must look like a clinical note
        right = ls.split(" : ", 1)[1].strip()
        if not right:
            return False
        if any(right.startswith(m) for m in _INTERP_MARKERS):
            return True
        if right[0].isupper() and len(right) > 3:
            return True
        return False

    def _is_sub_section(self, ls: str) -> bool:
        if not ls or ls[0].islower() or ls.startswith("("):
            return False
        if any(c.isdigit() for c in ls):
            return False
        words = ls.split()
        if len(words) < 2 or len(words) > 8:
            return False
        return True

    # ── right-to-left test line parser ─────────────────────────

    def _parse_test_line(self, line: str) -> dict | None:
        tokens = line.split()
        if len(tokens) < 4:
            return None

        result = {
            "test_name": "",
            "value": None,
            "unit": "",
            "range_comparator": "",
            "range_min": None,
            "range_max": None,
            "anteriority": None,
            "secondary_range": "",
            "methodology": "",
            "abnormal": False,
            "value_display": None,
        }

        idx = len(tokens) - 1

        # ── Phase 1: anteriority ────────────────────────────
        if _is_number(tokens[idx]):
            # Check if this number is part of a range: X - Y
            if (idx >= 2 and tokens[idx - 1] == "-"
                    and _is_number(tokens[idx - 2])):
                pass  # it's range_max, handle below
            else:
                result["anteriority"] = tokens[idx]
                idx -= 1

        # ── Phase 2: range ──────────────────────────────────
        if idx >= 0:
            t = tokens[idx]

            # pattern: <55 or >30 (single token)
            if len(t) > 1 and t[0] in "<>" and _is_number(t[1:]):
                result["range_comparator"] = t[0]
                if t[0] == "<":
                    result["range_max"] = t[1:]
                else:
                    result["range_min"] = t[1:]
                idx -= 1

            # pattern: < X or > X (separate tokens)
            elif t in ("<", ">") and idx >= 1 and _is_number(tokens[idx - 1]):
                result["range_comparator"] = t
                if t == "<":
                    result["range_max"] = tokens[idx - 1]
                else:
                    result["range_min"] = tokens[idx - 1]
                idx -= 2

            # pattern: X - Y (three tokens)
            elif (idx >= 2 and _is_number(tokens[idx - 2])
                  and tokens[idx - 1] == "-"
                  and _is_number(tokens[idx])):
                result["range_min"] = tokens[idx - 2]
                result["range_max"] = tokens[idx]
                idx -= 3

            # pattern: X-Y (single token with hyphen)
            elif "-" in t:
                parts = t.split("-", 1)
                if _is_number(parts[0]) and _is_number(parts[1]):
                    result["range_min"] = parts[0]
                    result["range_max"] = parts[1]
                    idx -= 1

        # ── Phase 3: unit (optional) ────────────────────────
        if idx >= 0:
            t = tokens[idx]
            # If it's a pure number, there's no unit → proceed to value
            if not _is_number(t):
                result["unit"] = t
                idx -= 1
        elif idx < 0:
            return None

        # ── Phase 4: value ──────────────────────────────────
        if idx >= 0 and _is_number(tokens[idx]):
            result["value"] = tokens[idx]
            idx -= 1
        else:
            return None

        # ── Phase 5: test name (everything left) ────────────
        if idx >= 0:
            raw_name = " ".join(tokens[: idx + 1])
            result["test_name"] = raw_name.rstrip(":").strip()
        else:
            return None

        return result

    # ── abnormal value detection ───────────────────────────────

    def _mark_abnormal(self):
        for t in self.tests:
            v_str = t.get("value")
            if v_str is None:
                continue
            try:
                v = float(v_str.replace(",", "."))
            except (ValueError, TypeError):
                t["value_display"] = v_str
                continue

            abnormal = False

            if t.get("range_min") is not None and t.get("range_max") is not None:
                try:
                    lo = float(str(t["range_min"]).replace(",", "."))
                    hi = float(str(t["range_max"]).replace(",", "."))
                    if v < lo or v > hi:
                        abnormal = True
                except (ValueError, TypeError):
                    pass
            elif t.get("range_comparator") == "<" and t.get("range_max") is not None:
                try:
                    hi = float(str(t["range_max"]).replace(",", "."))
                    if v >= hi:
                        abnormal = True
                except (ValueError, TypeError):
                    pass
            elif t.get("range_comparator") == ">" and t.get("range_min") is not None:
                try:
                    lo = float(str(t["range_min"]).replace(",", "."))
                    if v <= lo:
                        abnormal = True
                except (ValueError, TypeError):
                    pass

            t["abnormal"] = abnormal
            t["value_display"] = f"{v_str}*" if abnormal else v_str

    # ── result construction ────────────────────────────────────

    def _build_result(self) -> dict:
        edition_date = self.metadata.get("date_edition", "")
        for t in self.tests:
            t["test_date"] = edition_date
        return {
            "metadata": self.metadata,
            "tests": self.tests,
            "interpretations": self.interpretations,
            "pdf_path": str(self.pdf_path.resolve()),
        }
