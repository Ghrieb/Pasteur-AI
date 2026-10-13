"""AI Interpreter — Medical report explanation via Groq LLM.

Combines patient info, current report (JSON + text summary),
historical reports (from DB), and Medical Knowledge into a
single prompt for the LLM to answer patient questions.
"""

import copy
import json
import logging
import os
from typing import Any

from groq import Groq

from src.biomarker_registry import CODE_TO_ENTRY


class AIInterpreter:
    """Uses Groq LLM to explain lab reports with full patient history context."""

    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def __init__(self, api_key: str | None = None, db: Any = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.db = db

    def interpret(
        self,
        report_json: dict,
        query: str = "",
        language: str = "fr",
    ) -> str:
        """Build context, assemble prompt, call LLM, return answer."""
        context = self._build_context(report_json)
        prompt = self._build_prompt(context, query, language)

        if not self.client:
            return f"[DRY RUN — set GROQ_API_KEY env var]\n\n=== PROMPT ===\n\n{prompt}"

        response = self.client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    def analyze(self, report_json: dict, language: str = "fr") -> dict:
        """Get structured analysis — returns dict with summary, findings, recommendations, confidence."""
        safe_json = self._strip_pii(report_json)
        safe_json = self._strip_non_text(safe_json)
        context = self._build_context(safe_json)
        prompt = self._build_analysis_prompt(context, language)

        if not self.client:
            return self._build_fallback_analysis(report_json, language)

        try:
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
        except Exception as e:
            logger = logging.getLogger("pasteur-ai")
            logger.error("Groq analyze call failed: %s", e)
            return self._build_fallback_analysis(report_json, language)

        try:
            result = json.loads(content)
            findings = result.get("findings", [])
            if not findings and self._has_abnormal_tests(report_json):
                logger.info("AI returned empty findings but abnormal tests exist — using fallback")
                return self._build_fallback_analysis(report_json, language, ai_summary=result.get("summary", ""))
            # Normalize severity strings from AI
            for f in findings:
                f["severity"] = self._normalize_severity(f.get("severity", "normal"))
            result["findings"] = findings
            return result
        except json.JSONDecodeError:
            return self._build_fallback_analysis(report_json, language, ai_summary=content)

    @staticmethod
    def _is_test_abnormal(t: dict) -> bool:
        val = t.get("value")
        if val is None:
            return False
        try:
            val = float(val)
        except (ValueError, TypeError):
            val_n = t.get("value_display", "")
            try:
                val = float(val_n.replace(",", "."))
            except (ValueError, TypeError):
                return False

        r = t.get("range", {})
        comparator = r.get("comparator")

        if comparator == "<":
            max_v = r.get("max")
            if max_v is not None and val >= float(max_v):
                return True
        elif comparator == ">":
            min_v = r.get("min")
            if min_v is not None and val <= float(min_v):
                return True
        else:
            lo = r.get("min")
            hi = r.get("max")
            if lo is not None and hi is not None:
                try:
                    if val < float(lo) or val > float(hi):
                        return True
                except (ValueError, TypeError):
                    pass

        return False

    def _has_abnormal_tests(self, report_json: dict) -> bool:
        """Check if report has any tests marked abnormal (by value/range comparison)."""
        for t in report_json.get("tests", []):
            if self._is_test_abnormal(t):
                return True
        return False

    _SEVERITY_MAP = {
        "high": "critical", "severe": "critical", "critical": "critical",
        "elevated": "elevated", "warning": "elevated",
        "low": "low",
        "normal": "normal",
        "abnormal": "elevated",
    }

    @staticmethod
    def _normalize_severity(s: str) -> str:
        return AIInterpreter._SEVERITY_MAP.get(s.lower(), "elevated")

    def _build_fallback_analysis(self, report_json: dict, language: str, ai_summary: str = "") -> dict:
        """Generate basic analysis from report data when AI is unavailable or returns empty findings."""
        tests = report_json.get("tests", [])
        abnormal_tests = [t for t in tests if self._is_test_abnormal(t)]

        findings = []
        for t in abnormal_tests:
            val = t.get("value_display") or str(t.get("value", ""))
            unit = t.get("unit", "")
            name = t.get("test_name", "")
            r = t.get("range", {})
            range_str = ""
            if r.get("comparator"):
                if r["comparator"] == "<":
                    range_str = f"<{r.get('max', '')}"
                elif r["comparator"] == ">":
                    range_str = f">{r.get('min', '')}"
            elif r.get("min") is not None and r.get("max") is not None:
                range_str = f"{r['min']} - {r['max']}"

            # Determine severity based on how far out of range
            severity = "elevated"
            t_val = t.get("value")
            if t_val is not None:
                try:
                    t_val = float(t_val)
                    if r.get("max") is not None and t_val > float(r["max"]) * 1.5:
                        severity = "critical"
                    elif r.get("min") is not None and t_val < float(r["min"]):
                        severity = "low"
                    elif r.get("max") is not None and t_val > float(r["max"]):
                        severity = "elevated"
                except (ValueError, TypeError):
                    pass

            findings.append({
                "title": name,
                "test": name,
                "value": f"{val} {unit}" if val and unit else val or "",
                "range": f"{range_str} {unit}" if range_str and unit else range_str or "",
                "severity": severity,
                "explanation": f"{name} à {val} {unit} (réf: {range_str} {unit}). Valeur anormale détectée.",
                "recommendation": f"Consultez votre médecin pour un suivi de {name.lower()}.",
                "confidence": 92,
            })

        if not findings:
            return {
                "summary": ai_summary or "Aucune anomalie détectée dans les résultats.",
                "findings": [],
                "recommendations": ["Maintenez vos habitudes actuelles."],
                "confidence": "high",
            }

        return {
            "summary": ai_summary or f"{len(findings)} anomalie(s) détectée(s) dans le bilan.",
            "findings": findings,
            "recommendations": [f["recommendation"] for f in findings[:3]],
            "confidence": "medium",
        }

    def summarizeDashboard(self, report_json: dict, language: str = "fr") -> str:
        """Get concise dashboard summary string."""
        safe_json = self._strip_pii(report_json)
        safe_json = self._strip_non_text(safe_json)
        context = self._build_context(safe_json)
        prompt = self._build_summary_prompt(context, language)

        if not self.client:
            return f"[DRY RUN] Analysis based on {len(report_json.get('tests', []))} biomarkers."

        try:
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
        except Exception as e:
            logger = logging.getLogger("pasteur-ai")
            logger.error("Groq summarizeDashboard call failed: %s", e)
            return ""

        try:
            data = json.loads(content)
            return data.get("summary", content)
        except json.JSONDecodeError:
            return content

    def _strip_pii(self, report_json: dict) -> dict:
        """Remove patient name from the report JSON before sending to AI."""
        safe = copy.deepcopy(report_json)
        patient = safe.get("patient", {})
        if isinstance(patient, dict):
            allowed = {"age", "sex"}
            safe["patient"] = {k: v for k, v in patient.items() if k in allowed}
        return safe

    def _strip_non_text(self, report_json: dict) -> dict:
        """Remove non-text fields that could confuse the LLM (images, binaries, etc)."""
        safe = copy.deepcopy(report_json)
        for key in ("meta", "interpretations"):
            safe.pop(key, None)
        tests = safe.get("tests", [])
        if isinstance(tests, list):
            for t in tests:
                if isinstance(t, dict):
                    t.pop("methodology", None)
                    t.pop("normalization_confidence", None)
        return safe

    # ── context assembly ─────────────────────────────────

    def _build_context(self, report_json: dict) -> dict:
        patient = report_json.get("patient", {})
        patient_name = patient.get("name", "")

        # Previous reports from DB
        history = []
        if self.db and patient_name:
            try:
                all_reports = self.db.get_patient_reports(patient_name)
                current_ref = report_json.get("report_ref", "")
                history = [r for r in all_reports if r["report_ref"] != current_ref]
            except Exception:
                history = []

        # Medical knowledge for tests in this report
        codes_in_report = set()
        for t in report_json.get("tests", []):
            code = t.get("code", "")
            if code and code != "UNKNOWN":
                codes_in_report.add(code)

        knowledge = []
        for code in sorted(codes_in_report):
            entry = CODE_TO_ENTRY.get(code)
            if entry:
                knowledge.append({
                    "code": code,
                    "name": entry.get("canonical_name", ""),
                    "category": entry.get("category", ""),
                    "dashboard_group": entry.get("dashboard_group", ""),
                    "description": entry.get("description", ""),
                    "unit": entry.get("unit", ""),
                })

        return {
            "patient": patient,
            "current_report": report_json,
            "history": history,
            "medical_knowledge": knowledge,
        }

    # ── text summary ─────────────────────────────────────

    def _build_text_summary(self, report_json: dict) -> str:
        lines = []
        patient = report_json.get("patient", {})
        dates = report_json.get("dates", {})
        meta = report_json.get("meta", {})
        tests = report_json.get("tests", [])

        ref = report_json.get("report_ref", "")
        demande = report_json.get("demande_id", "")
        lines.append(f"Report #{ref}")
        if demande:
            lines.append(f"Demande: {demande}")
        lines.append(f"Date: {dates.get('edition') or dates.get('demande', '')}")
        lines.append(f"Patient: {patient.get('name', '')} | {patient.get('age', '')} years | {patient.get('sex', '')}")
        lines.append(f"Source: {meta.get('pdf_source', '')}")
        lines.append("")

        groups: dict[str, list[dict]] = {}
        for t in tests:
            g = t.get("dashboard_group") or t.get("category") or "Other"
            groups.setdefault(g, []).append(t)

        abnormal_count = 0
        for group_name in sorted(groups.keys()):
            group_tests = groups[group_name]
            lines.append(f"--- {group_name} ---")
            for t in group_tests:
                name = t.get("test_name", "")
                code = t.get("code", "")
                val = t.get("value_display") or str(t.get("value", ""))
                unit = t.get("unit", "")
                abnormal = t.get("abnormal", False)
                flag = " *ABNORMAL*" if abnormal else ""
                if abnormal:
                    abnormal_count += 1

                r = t.get("range", {})
                range_str = ""
                if r.get("comparator"):
                    if r["comparator"] == "<":
                        range_str = f" <{r.get('max', '')}"
                    elif r["comparator"] == ">":
                        range_str = f" >{r.get('min', '')}"
                elif r.get("min") is not None and r.get("max") is not None:
                    range_str = f" [{r['min']} - {r['max']}]"

                sec = t.get("secondary_range", {})
                sec_str = ""
                if sec.get("min") is not None and sec.get("max") is not None:
                    sec_str = f" ({sec['min']} - {sec['max']})"

                lines.append(f"  {name} ({code}): {val} {unit}{range_str}{sec_str}{flag}")
            lines.append("")

        interps = report_json.get("interpretations", [])
        if interps:
            lines.append("--- Interpretations ---")
            for i in interps:
                if isinstance(i, dict):
                    parts = []
                    if i.get("severity"):
                        parts.append(i["severity"])
                    if i.get("min") is not None and i.get("max") is not None:
                        parts.append(f"{i['min']}-{i['max']}")
                    if i.get("comparator") and i.get("value"):
                        parts.append(f"{i['comparator']}{i['value']}")
                    if i.get("unit"):
                        parts.append(i["unit"])
                    lines.append("  " + " ".join(parts))
                else:
                    lines.append(f"  {i}")
            lines.append("")

        lines.append(f"Total tests: {len(tests)}, Abnormal: {abnormal_count}")
        return "\n".join(lines)

    # ── prompt assembly ──────────────────────────────────

    _LANG_NAMES = {"ar": "Arabic", "fr": "French", "en": "English"}

    def _build_prompt(self, context: dict, query: str, language: str) -> str:
        lang_name = self._LANG_NAMES.get(language, "French")
        parts = []

        parts.append(f"""You are a medical report assistant for Institut Pasteur lab results.
Answer in {lang_name}. Be concise, accurate, and empathetic.

Use the provided data to answer the patient's question. If the question references trends or history, compare current values with previous reports. If you don't have enough data to answer, say so.

Do NOT invent lab values. Only use the data provided below.""")
        parts.append("")

        # Patient
        p = context["patient"]
        parts.append("=== PATIENT ===")
        parts.append(f"Name: {p.get('name', '')}")
        parts.append(f"Age: {p.get('age', '')} years")
        parts.append(f"Sex: {p.get('sex', '')}")
        parts.append("")

        # Current report (text summary)
        parts.append("=== CURRENT REPORT ===")
        parts.append(self._build_text_summary(context["current_report"]))
        parts.append("")

        # History
        if context["history"]:
            parts.append(f"=== PREVIOUS REPORTS ({len(context['history'])}) ===")
            for i, r in enumerate(context["history"], 1):
                raw = r.get("raw_json")
                if raw:
                    parts.append(f"--- Previous Report #{i} (ref: {r.get('report_ref', '')}) ---")
                    parts.append(json.dumps(raw, ensure_ascii=False, indent=2))
                    parts.append("")
        else:
            parts.append("=== PREVIOUS REPORTS ===\nNone available.\n")

        # Medical knowledge
        if context["medical_knowledge"]:
            parts.append(f"=== MEDICAL KNOWLEDGE ({len(context['medical_knowledge'])} biomarkers) ===")
            for entry in context["medical_knowledge"]:
                parts.append(f"- {entry['code']}: {entry['name']}")
                parts.append(f"  Category: {entry['category']} | Group: {entry['dashboard_group']}")
                parts.append(f"  Description: {entry['description']}")
                parts.append(f"  Unit: {entry['unit']}")
                parts.append("")

        # User question
        parts.append("=== PATIENT'S QUESTION ===")
        parts.append(query if query else "Explain this lab report in simple terms. What are the key results I should know about?")

        return "\n".join(parts)

    def _build_analysis_prompt(self, context: dict, language: str) -> str:
        lang_name = self._LANG_NAMES.get(language, "French")
        parts = []

        parts.append(f"""You are a medical laboratory analyst for Institut Pasteur d'Algérie.
Analyze these lab results and return ONLY valid JSON.
Answer in {lang_name}. Be concise and clinically accurate.

CRITICAL: The report marks abnormal values with *ABNORMAL*. You MUST include a finding for EVERY test marked *ABNORMAL*. Do NOT leave the findings array empty if any *ABNORMAL* tests exist.

Severity rules:
- Values ABOVE the reference range → severity "elevated"
- Values BELOW the reference range → severity "low"
- Values far outside range (>1.5x max or <0.5x min) → severity "critical"
- Normal values → severity "normal" (only include if clinically relevant)

Return ONLY a JSON object with this exact structure (no markdown, no code fences):
{{
  "summary": "3-4 concise sentences: direct observations of abnormal results and quick recommended actions. Do NOT mention age, gender, or use framing like 'the patient presents with'. Start directly with findings.",
  "findings": [
    {{
      "title": "Clinical impression (e.g., Cytolyse hépatique modérée, Hypothyroïdie infraclinique, Anémie ferriprive légère)",
      "test": "Test name (e.g., ALT (SGPT))",
      "value": "value with unit",
      "range": "reference range",
      "severity": "elevated|low|critical|normal",
      "explanation": "clinical meaning",
      "recommendation": "what to do",
      "confidence": 94
    }}
  ],
  "recommendations": ["recommendation 1", "recommendation 2"],
  "confidence": "high|medium|low"
}}""")
        parts.append("")

        p = context["patient"]
        parts.append("=== PATIENT ===")
        parts.append(f"Age: {p.get('age', '')} years | Sex: {p.get('sex', '')}")
        parts.append("")

        parts.append("=== REPORT ===")
        parts.append(self._build_text_summary(context["current_report"]))
        parts.append("")

        if context["medical_knowledge"]:
            parts.append(f"=== MEDICAL KNOWLEDGE ({len(context['medical_knowledge'])} biomarkers) ===")
            for entry in context["medical_knowledge"]:
                parts.append(f"- {entry['code']}: {entry['name']}")
                parts.append(f"  Category: {entry['category']} | Group: {entry['dashboard_group']}")
                parts.append(f"  Description: {entry['description']}")
                parts.append("")

        parts.append(f"REMINDER: Include EVERY test marked *ABNORMAL* as a finding. Return ONLY valid JSON matching the structure above.")
        return "\n".join(parts)

    def _build_summary_prompt(self, context: dict, language: str) -> str:
        lang_name = self._LANG_NAMES.get(language, "French")
        parts = []

        parts.append(f"""You are a medical dashboard assistant for Institut Pasteur d'Algérie.
Summarize this lab report in 3-4 concise sentences. Focus on direct observations of abnormal results and recommended actions. Do NOT mention age, gender, or use framing like 'the patient presents with'. State findings directly.
Answer in {lang_name}.

Return ONLY a JSON object with this exact structure:
{{
  "summary": "Your summary here"
}}""")
        parts.append("")

        p = context["patient"]
        parts.append("=== PATIENT ===")
        parts.append(f"Age: {p.get('age', '')} years | Sex: {p.get('sex', '')}")
        parts.append("")

        parts.append("=== REPORT ===")
        parts.append(self._build_text_summary(context["current_report"]))
        parts.append("")

        parts.append("Return ONLY valid JSON matching the structure above.")
        return "\n".join(parts)
