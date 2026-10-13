import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd


def _make_patient_folder_name(parsed: dict) -> str:
    meta = parsed.get("metadata", {})
    name = meta.get("patient_name", "Inconnu").strip()
    parts = name.split()
    if len(parts) >= 2:
        folder_name = f"{parts[0].upper()}_{'_'.join(p.upper() for p in parts[1:])}"
    else:
        folder_name = name.upper().replace(" ", "_")

    date = meta.get("date_demande", "") or meta.get("date_edition", "")
    if date:
        date_str = str(date).strip()
        m = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", date_str)
        if m:
            date_norm = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        else:
            m = re.search(r"(\d{2})[-/](\d{2})[-/](\d{4})", date_str)
            if m:
                date_norm = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            else:
                date_norm = date_str.replace("/", "-").replace(" ", "_")
        folder_name += f"_{date_norm}"

    return folder_name


def export_markdown(parsed: dict) -> str:
    meta = parsed.get("metadata", {})
    tests = parsed.get("tests", [])
    interpretations = parsed.get("interpretations", [])

    lines = []
    name = meta.get("patient_name", "Inconnu")
    lines.append(f"# Rapport IPA — {name}")
    lines.append("")

    info_table = [
        ("Réf. Rapport", meta.get("report_ref", "")),
        ("Demande N°", meta.get("demande_id", "")),
        ("Patient", name),
        ("Âge", str(meta.get("age", ""))),
        ("Sexe", meta.get("sex", "")),
        ("Date de demande", meta.get("date_demande", "")),
        ("Date d'édition", meta.get("date_edition", "")),
        ("Source PDF", parsed.get("pdf_path", "")),
    ]
    for label, val in info_table:
        lines.append(f"| **{label}** | {val} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not tests:
        lines.append("*Aucun résultat trouvé.*")
        lines.append("")
        return "\n".join(lines)

    current_section = ""
    current_sub = ""
    # group tests by section -> sub_section
    sections: dict[str, dict[str, list[dict]]] = {}
    for t in tests:
        sec = t.get("section", "") or "(sans section)"
        sub = t.get("sub_section", "") or ""
        sections.setdefault(sec, {}).setdefault(sub, []).append(t)

    for sec_name, subs in sections.items():
        lines.append(f"## {sec_name}")
        lines.append("")

        for sub_name, group in subs.items():
            if sub_name:
                lines.append(f"### {sub_name}")
                lines.append("")

            # Check if all tests in group share the same methodology (sub-section level)
            method_set = {t.get("methodology", "") for t in group if t.get("methodology")}
            shared_meth = method_set.pop() if len(method_set) == 1 else None
            if shared_meth:
                lines.append(f"*Méthode : {shared_meth}*")
                lines.append("")

            # Table header
            lines.append("| Test | Valeur | Unité | Normes | Antériorités |")
            lines.append("|------|--------|-------|--------|-------------|")

            for t in group:
                tname = t.get("test_name", "")
                val_display = t.get("value_display") or t.get("value") or ""
                unit = t.get("unit", "")
                normes = _format_range_display(t)
                ant = t.get("anteriority") or ""

                # Escape pipe chars in test names
                tname_esc = tname.replace("|", "\\|")
                lines.append(f"| {tname_esc} | {val_display} | {unit} | {normes} | {ant} |")

                # Per-test methodology row (only if different from shared sub-section level)
                meth = t.get("methodology", "")
                if meth and meth != shared_meth:
                    lines.append(f"| *↳ Méthode : {meth}* | | | | |")

            lines.append("")

        # Interpretation blocks after each section
        if interpretations:
            # Only show interpretations relevant to this section
            sec_interpretations = _filter_interpretations(interpretations, sec_name)
            if sec_interpretations:
                lines.append("**Interprétations :**")
                lines.append("")
                for interp in sec_interpretations:
                    lines.append(f"- {interp}")
                lines.append("")

    result = "\n".join(lines)
    return result


def _format_range_display(test: dict) -> str:
    cmp = test.get("range_comparator", "")
    rmin = test.get("range_min")
    rmax = test.get("range_max")
    sec = test.get("secondary_range", "")

    parts = []
    if cmp == "<":
        parts.append(f"<{rmax}")
    elif cmp == ">":
        parts.append(f">{rmin}")
    elif rmin is not None and rmax is not None:
        parts.append(f"{rmin} - {rmax}")
    else:
        parts.append("")

    if sec:
        parts.append(f"[{sec}]")

    return " ".join(parts).strip() or ""


def _filter_interpretations(interpretations: list[str], section: str) -> list[str]:
    section_keywords = {
        "Hématologie": [],
        "Hormonologie": ["Vitamine D", "TSH", "FT4", "Vitamine B12"],
        "Biochimie": ["HbA1c", "Glycémie", "Cholestérol"],
    }
    keywords = section_keywords.get(section, [])
    if not keywords:
        return []
    return [i for i in interpretations if any(k.lower() in i.lower() for k in keywords)]


def build_dataframe(
    parsed_list: list[dict],
    include_normes: bool = True,
    include_anteriors: bool = False,
) -> pd.DataFrame:
    rows = []
    for parsed in parsed_list:
        meta = parsed.get("metadata", {})
        base = {
            "report_ref": meta.get("report_ref", ""),
            "demande_id": meta.get("demande_id", ""),
            "patient_name": meta.get("patient_name", ""),
            "age": meta.get("age", ""),
            "sex": meta.get("sex", ""),
            "date_demande": meta.get("date_demande", ""),
            "date_edition": meta.get("date_edition", ""),
        }

        for t in parsed.get("tests", []):
            row = dict(base)
            row["pdf_source"] = str(parsed.get("pdf_path", ""))
            row["section"] = t.get("section", "")
            row["sub_section"] = t.get("sub_section", "")
            row["test_date"] = t.get("test_date", "")
            row["test_name"] = t.get("test_name", "")

            val_display = t.get("value_display") or t.get("value") or ""
            row["value"] = val_display
            row["abnormal"] = t.get("abnormal", False)
            row["unit"] = t.get("unit", "")

            if include_normes:
                row["range_comparator"] = t.get("range_comparator", "")
                row["range_min"] = t.get("range_min", "")
                row["range_max"] = t.get("range_max", "")

                sec_min = sec_max = ""
                sec_raw = t.get("secondary_range", "")
                if sec_raw:
                    parts = sec_raw.replace(" ", "").split("-", 1)
                    if len(parts) == 2:
                        sec_min, sec_max = parts[0], parts[1]
                row["secondary_range_min"] = sec_min
                row["secondary_range_max"] = sec_max

            if include_anteriors:
                row["anteriority"] = t.get("anteriority", "")
                row["anteriority_date"] = t.get("anteriority_date", "")

            rows.append(row)

    return pd.DataFrame(rows)


def write_patient_output(
    parsed: dict,
    output_dir: str | Path,
    include_normes: bool = True,
    include_anteriors: bool = False,
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    folder_name = _make_patient_folder_name(parsed)
    patient_dir = output_dir / folder_name
    patient_dir.mkdir(parents=True, exist_ok=True)

    md_path = patient_dir / "report.md"
    md = export_markdown(parsed)
    md_path.write_text(md, encoding="utf-8")

    csv_path = patient_dir / "report.csv"
    df = build_dataframe([parsed], include_normes=include_normes, include_anteriors=include_anteriors)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    return md_path, csv_path


def write_combined_csv(
    parsed_list: list[dict],
    output_path: str | Path,
    include_normes: bool = True,
    include_anteriors: bool = False,
):
    df = build_dataframe(parsed_list, include_normes, include_anteriors)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df


def write_combined_markdown(parsed_list: list[dict], output_path: str | Path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# IPA Reports \u2014 Complete Overview", ""]

    for i, parsed in enumerate(parsed_list, 1):
        meta = parsed.get("metadata", {})
        name = meta.get("patient_name", "Inconnu")
        lines.append(f"## Patient {i}: {name}")
        lines.append("")

        report_md = export_markdown(parsed)
        report_lines = report_md.split("\n")
        body = "\n".join(report_lines[1:]) if report_lines else ""
        lines.append(body.strip())

        if i < len(parsed_list):
            lines.append("")
            lines.append("---")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown(parsed: dict, output_path: str | Path):
    md = export_markdown(parsed)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")


# ── JSON export (AI‑ready) ───────────────────────────────

def _to_float_or_none(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except (ValueError, TypeError):
        return None


_INTERP_RE = re.compile(
    r"^([<>]\s*)?(\d+\.?\d*)\s*(?:-\s*(\d+\.?\d*))?\s*([a-zA-Z/\[\]\*3-9]+)\s*:\s*(.+)$"
)


def _parse_interpretation(raw: str) -> dict:
    """Parse '20 - 30 ng/mL : Carence modérée' into structured object."""
    m = _INTERP_RE.match(raw.strip())
    if not m:
        return {"raw": raw}
    comparator = m.group(1).strip() if m.group(1) else ""
    lo = m.group(2)
    hi = m.group(3)
    unit = m.group(4).strip()
    severity = m.group(5).strip()
    result = {"severity": severity, "unit": unit}
    if comparator:
        result["comparator"] = comparator
        result["value"] = _to_float_or_none(lo)
    elif hi:
        result["min"] = _to_float_or_none(lo)
        result["max"] = _to_float_or_none(hi)
    else:
        result["value"] = _to_float_or_none(lo)
    return result


def _parse_secondary_range(raw: str) -> dict:
    if not raw or raw == "":
        return {"min": None, "max": None}
    parts = raw.replace(" ", "").split("-", 1)
    if len(parts) == 2:
        return {
            "min": _to_float_or_none(parts[0]),
            "max": _to_float_or_none(parts[1]),
        }
    return {"min": None, "max": None}


def export_json(parsed: dict) -> dict:
    """Transform a parsed report into a clean AI‑friendly JSON structure."""
    meta = parsed.get("metadata", {})
    tests_raw = parsed.get("tests", [])
    interpretations_raw = parsed.get("interpretations", [])

    return {
        "report_ref": meta.get("report_ref", ""),
        "demande_id": meta.get("demande_id", ""),
        "patient": {
            "name": meta.get("patient_name", ""),
            "age": _to_float_or_none(meta.get("age")),
            "sex": meta.get("sex", ""),
        },
        "dates": {
            "demande": meta.get("date_demande", ""),
            "edition": meta.get("date_edition", ""),
        },
        "tests": [_test_to_json(t, meta) for t in tests_raw],
        "interpretations": [_parse_interpretation(i) for i in interpretations_raw],
        "meta": {
            "pdf_source": str(parsed.get("pdf_path", "")),
            "parsed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def _test_to_json(t: dict, meta: dict) -> dict:
    v_str = t.get("value")
    ant_str = t.get("anteriority")

    obj = {
        "test_name": t.get("test_name", ""),
        "value": _to_float_or_none(v_str),
        "value_display": t.get("value_display") or v_str or "",
        "unit": t.get("unit", ""),
        "abnormal": bool(t.get("abnormal", False)),
        "section": t.get("section", ""),
        "sub_section": t.get("sub_section", ""),
        "methodology": t.get("methodology", ""),
        "range": {
            "comparator": t.get("range_comparator", ""),
            "min": _to_float_or_none(t.get("range_min")),
            "max": _to_float_or_none(t.get("range_max")),
        },
        "secondary_range": _parse_secondary_range(t.get("secondary_range", "")),
        "anteriority": {
            "value": _to_float_or_none(ant_str),
            "date": t.get("anteriority_date") or "",
        } if ant_str else None,
        "test_date": meta.get("date_edition", ""),
    }
    return obj


def write_combined_json(
    parsed_list: list[dict],
    output_path: str | Path,
) -> list[dict]:
    """Write all parsed reports as a single JSON array (one object per report)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = [export_json(p) for p in parsed_list]
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def write_patient_json(
    parsed: dict,
    output_path: str | Path,
) -> Path:
    """Write a single patient report as JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = export_json(parsed)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
