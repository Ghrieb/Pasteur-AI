import re
from pathlib import Path
from typing import Callable

import pandas as pd


# ── types ──────────────────────────────────────────────────

FilterFunc = Callable[[pd.DataFrame], pd.DataFrame]


class FilterStep:
    def __init__(self, name: str, apply: FilterFunc):
        self.name = name
        self.apply = apply


class FilterPipeline:
    """Chain of filter steps applied sequentially.

    Build:
        p = FilterPipeline()
        p.add("abnormal only", abnormal_only())
        p.add("section", by_section(["Hématologie"]))

    Run:
        result = p.run(df)
    """

    def __init__(self):
        self.steps: list[FilterStep] = []

    def add(self, name: str, func: FilterFunc) -> "FilterPipeline":
        self.steps.append(FilterStep(name, func))
        return self

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df
        for step in self.steps:
            result = step.apply(result)
            if len(result) == 0:
                break
        return result

    @property
    def description(self) -> str:
        return " \u2192 ".join(s.name for s in self.steps) if self.steps else "unfiltered"

    def empty(self) -> bool:
        return len(self.steps) == 0

    def suggest_filename(self) -> str:
        """Generate a descriptive filesystem-safe filename from the pipeline steps."""
        parts = []
        for s in self.steps:
            parts.append(_step_to_slug(s.name))
        slug = "_".join(parts) if parts else "all_data"
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug + ".csv"


def _step_to_slug(name: str) -> str:
    """Convert a step name like 'patient~KARIM BENALI' to 'karim_benali'."""
    # patient scope
    if name.startswith("patient~"):
        return name[len("patient~"):].strip().replace(" ", "_").lower()
    # report scope
    if name.startswith("report="):
        refs = name[len("report="):]
        return "ref_" + refs.replace("|", "_").replace("/", "_")
    # demande scope
    if name.startswith("demande="):
        ids = name[len("demande="):]
        return "dem_" + ids.replace("|", "_").replace("/", "_")
    # test name pattern
    if name.startswith("test=~/"):
        pat = name[len("test=~/"):-1] if name.endswith("/") else name[len("test=~/"):]
        return "test_" + re.sub(r'\W+', '_', pat).strip("_").lower()
    # section
    if name.startswith("section="):
        sections = name[len("section="):]
        return sections.split(",")[0].strip().lower().replace("é", "e").replace("è", "e")
    # sex
    if name.startswith("sex="):
        return name[len("sex="):].lower()
    # age
    if name.startswith("age="):
        return name.lower().replace("=", "_").replace("-", "_")
    # fallback: clean up
    return name.replace("-", "_").replace(" ", "_").lower()


# ── scope filter factories ─────────────────────────────────


def by_patient_name(pattern: str) -> FilterFunc:
    """Keep rows where patient_name contains *pattern* (case-insensitive)."""
    pat = pattern.strip().lower()

    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["patient_name"].str.lower().str.contains(pat, na=False)].copy()
    _filter.__name__ = f"patient~{pat}"
    return _filter


def by_report_refs(refs: list[str]) -> FilterFunc:
    """Keep rows whose report_ref is in *refs* (exact match)."""
    targets = [r.strip() for r in refs]

    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["report_ref"].isin(targets)].copy()
    _filter.__name__ = f"report={'|'.join(targets)}"
    return _filter


def by_demande_ids(ids: list[str]) -> FilterFunc:
    """Keep rows whose demande_id is in *ids* (exact match)."""
    targets = [i.strip() for i in ids]

    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["demande_id"].isin(targets)].copy()
    _filter.__name__ = f"demande={'|'.join(targets)}"
    return _filter


# ── row-level filter factories ─────────────────────────────


def abnormal_only() -> FilterFunc:
    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["abnormal"] == True].copy()
    _filter.__name__ = "abnormal-only"
    return _filter


def by_section(sections: list[str]) -> FilterFunc:
    targets = [s.strip().lower() for s in sections]

    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["section"].str.strip().str.lower().isin(targets)].copy()
    _filter.__name__ = f"section={','.join(sections)}"
    return _filter


def by_test_name(pattern: str) -> FilterFunc:
    compiled = re.compile(pattern, re.IGNORECASE)

    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["test_name"].str.contains(compiled, na=False)].copy()
    _filter.__name__ = f"test=~/{pattern}/"
    return _filter


def by_sex(sex: str) -> FilterFunc:
    target = sex.strip().lower()

    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["sex"].str.strip().str.lower() == target].copy()
    _filter.__name__ = f"sex={sex}"
    return _filter


def by_age_range(min_age: int | None, max_age: int | None) -> FilterFunc:
    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        ages = pd.to_numeric(df["age"], errors="coerce")
        mask = pd.Series(True, index=df.index)
        if min_age is not None:
            mask &= ages >= min_age
        if max_age is not None:
            mask &= ages <= max_age
        return df[mask].copy()
    lo = min_age or ""
    hi = max_age or ""
    _filter.__name__ = f"age={lo}-{hi}"
    return _filter


def anteriority_only() -> FilterFunc:
    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["anteriority"].notna() & (df["anteriority"] != "")].copy()
    _filter.__name__ = "anteriority-only"
    return _filter


# ── I/O helpers ────────────────────────────────────────────


def read_combined_csv(csv_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    df["abnormal"] = df["abnormal"].map({"True": True, "False": False})
    return df


def write_filtered_csv(df: pd.DataFrame, output_path: str | Path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


# ── interactive prompts ────────────────────────────────────


def _describe_df(df: pd.DataFrame) -> str:
    n_patients = df["patient_name"].nunique()
    n_rows = len(df)
    return f"{n_rows} rows from {n_patients} patient(s)"


def _prompt_scope(df: pd.DataFrame) -> FilterFunc | None:
    """Ask user what data to scope and return a scope FilterFunc (or None = all)."""
    print()
    print(f"Which data to filter?  ({_describe_df(df)})")
    print("  1) All patients")
    print("  2) A specific patient")
    print("  3) By report reference(s)")
    print("  4) By demande ID(s)")
    while True:
        choice = input("Enter choice (1-4) [1]: ").strip()
        if not choice or choice == "1":
            return None
        if choice == "2":
            name = input("Enter patient name (partial match): ").strip()
            if name:
                f = by_patient_name(name)
                return f
            print("Name cannot be empty.")
        elif choice == "3":
            refs_input = input("Enter report reference(s) (comma-separated): ").strip()
            if refs_input:
                refs = [r.strip() for r in refs_input.split(",") if r.strip()]
                if refs:
                    return by_report_refs(refs)
            print("At least one reference required.")
        elif choice == "4":
            ids_input = input("Enter demande ID(s) (comma-separated): ").strip()
            if ids_input:
                ids = [i.strip() for i in ids_input.split(",") if i.strip()]
                if ids:
                    return by_demande_ids(ids)
            print("At least one ID required.")
        else:
            print("Please enter 1, 2, 3, or 4.")


def _prompt_sections(df: pd.DataFrame) -> list[str] | None:
    available = sorted(df["section"].dropna().unique())
    if not available:
        return None
    print("Available sections:")
    for s in available:
        print(f"  - {s}")
    answer = input("Enter sections (comma-separated) or leave empty to skip: ").strip()
    if not answer:
        return None
    return [s.strip() for s in answer.split(",")]


def _prompt_yes_no(prompt: str, default: bool = False) -> bool:
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


def _prompt_str(prompt: str) -> str | None:
    answer = input(f"{prompt}: ").strip()
    return answer if answer else None


def _prompt_int(prompt: str) -> int | None:
    while True:
        answer = input(f"{prompt}: ").strip()
        if not answer:
            return None
        try:
            return int(answer)
        except ValueError:
            print("Please enter a valid integer.")


def _prompt_choice(prompt: str, options: list[str]) -> str | None:
    if not _prompt_yes_no(prompt):
        return None
    print("Options: " + ", ".join(options))
    while True:
        answer = input("Enter choice: ").strip().lower()
        for opt in options:
            if answer == opt.lower():
                return opt
        print(f"Please enter one of: {', '.join(options)}")


def _prompt_output_path(default_name: str, output_dir: str | Path = "output") -> Path:
    """Ask user to confirm or customize the output filename."""
    output_dir = Path(output_dir)
    filtered_dir = output_dir / "filtered"
    default_path = filtered_dir / default_name

    print()
    print(f"Output path: {default_path}")
    answer = input("Press Enter to accept or type a different path: ").strip()
    if not answer:
        filtered_dir.mkdir(parents=True, exist_ok=True)
        return default_path

    custom = Path(answer)
    if not custom.is_absolute():
        custom = filtered_dir / custom
    custom.parent.mkdir(parents=True, exist_ok=True)
    return custom


# ── pipeline builders ──────────────────────────────────────


def build_pipeline_from_interactive(df: pd.DataFrame) -> FilterPipeline:
    p = FilterPipeline()

    # ── Step 1: SCOPE ──────────────────────────────────────
    scope_filter = _prompt_scope(df)
    if scope_filter:
        p.add(scope_filter.__name__, scope_filter)
        scoped = scope_filter(df)
        print(f"  -> scoped to {_describe_df(scoped)}")
        if len(scoped) == 0:
            print("  -> no data matches this scope. Stopping.")
            return p
    else:
        scoped = df

    # ── Step 2: ROW-LEVEL FILTERS ──────────────────────────
    print()
    if _prompt_yes_no("Filter abnormal values only?"):
        p.add("abnormal-only", abnormal_only())

    sections = _prompt_sections(scoped)
    if sections:
        p.add(f"section={','.join(sections)}", by_section(sections))

    pattern = _prompt_str("Filter by test name pattern (regex)? Leave empty to skip")
    if pattern:
        p.add(f"test=~/{pattern}/", by_test_name(pattern))

    sex = _prompt_choice("Filter by sex?", ["Male", "Female"])
    if sex:
        p.add(f"sex={sex}", by_sex(sex))

    min_age = _prompt_int("Minimum age? Leave empty for no limit")
    max_age = _prompt_int("Maximum age? Leave empty for no limit")
    if min_age is not None or max_age is not None:
        p.add(f"age={min_age or ''}-{max_age or ''}", by_age_range(min_age, max_age))

    if _prompt_yes_no("Only rows with anteriority?"):
        p.add("anteriority-only", anteriority_only())

    return p


def build_pipeline_from_args(args) -> FilterPipeline:
    p = FilterPipeline()

    # ── scope (from CLI flags) ──────────────────────────────
    patient = getattr(args, "patient", None)
    if patient:
        p.add(f"patient~{patient}", by_patient_name(patient))
    report_refs = getattr(args, "report_ref", None)
    if report_refs:
        p.add(f"report={'|'.join(report_refs)}", by_report_refs(report_refs))
    demande_ids = getattr(args, "demande_id", None)
    if demande_ids:
        p.add(f"demande={'|'.join(demande_ids)}", by_demande_ids(demande_ids))

    # ── row-level filters ──────────────────────────────────
    if getattr(args, "abnormal_only", False):
        p.add("abnormal-only", abnormal_only())
    sections = getattr(args, "section", None)
    if sections:
        sections = [s.strip() for s in sections]
        p.add(f"section={','.join(sections)}", by_section(sections))
    pattern = getattr(args, "test_name", None)
    if pattern:
        p.add(f"test=~/{pattern}/", by_test_name(pattern))
    sex = getattr(args, "sex", None)
    if sex:
        p.add(f"sex={sex}", by_sex(sex))
    min_age = getattr(args, "min_age", None)
    max_age = getattr(args, "max_age", None)
    if min_age is not None or max_age is not None:
        p.add(f"age={min_age or ''}-{max_age or ''}", by_age_range(min_age, max_age))
    anteriors = getattr(args, "anteriority_only", False)
    if anteriors:
        p.add("anteriority-only", anteriority_only())

    return p
