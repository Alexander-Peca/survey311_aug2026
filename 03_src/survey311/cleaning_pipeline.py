"""
cleaning_pipeline.py

Stage-1 (structural) cleaning + inspection pipeline.

Scope (INTENTIONALLY LIMITED / GENERALIZABLE)
--------------------------------------------
This module automates only the parts of "setup & cleaning" that are truly dataset-agnostic:

1) Schema hygiene
   - Column-name normalization to snake_case
   - Column-name uniqueness checks
2) Structural inspection report (no domain assumptions)
   - Shape, columns, dtypes
   - Missingness summary
   - Duplicate-row summary
   - Numeric sanity (min/max, infinities)
   - Categorical sanity (nunique + top frequencies)
3) Optional *minimal-damage* row drops for tiny missingness in chosen columns
   - You must explicitly choose columns; nothing is auto-dropped silently.
4) Optional artifact saving
   - Save cleaned dataset to /processed
   - Save a JSON report for auditing

Non-goals (DELIBERATELY NOT AUTOMATED)
-------------------------------------
- Semantic equivalence checks (derived/redundant columns)
- Business rules / domain validity constraints
- Imputation strategies
- Feature engineering
- Modeling, train/test splitting, leakage prevention

Usage
-----
>>> import pandas as pd
>>> from cleaning_pipeline import run_stage1, Stage1Config
>>> df = pd.read_csv("...")
>>> cleaned_df, report = run_stage1(df, Stage1Config())

If you want artifact saving:
>>> from pathlib import Path
>>> from cleaning_pipeline import save_stage1_artifacts
>>> cleaned_path, report_path = save_stage1_artifacts(
...     cleaned_df, report, processed_dir=Path("01_data/processed"),
...     basename="titanic", stage_tag="stage1_structural"
... )
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import json
import logging
import re

import numpy as np
import pandas as pd


# -----------------------------
# Logging
# -----------------------------

LOGGER = logging.getLogger("cleaning_pipeline")
if not LOGGER.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("[%(levelname)s] %(message)s")
    _handler.setFormatter(_formatter)
    LOGGER.addHandler(_handler)
LOGGER.setLevel(logging.INFO)


# -----------------------------
# Configuration
# -----------------------------

@dataclass(frozen=True)
class Stage1Config:
    """
    Configuration for Stage-1 structural cleaning.

    Notes:
    - We do NOT auto-drop columns. That requires meaning.
    - We do NOT impute. That belongs to modeling.
    - You may optionally drop *rows* with missing values in specified columns
      if missingness is tiny and the column is essential for downstream work.
    """

    # report previews (kept small; report is JSON)
    preview_rows: int = 5

    # safe schema actions
    normalize_column_names: bool = True
    enforce_unique_column_names: bool = True

    # Optional row drops: only for explicitly named columns, and only if tiny-missing.
    drop_rows_missing_in: Optional[Sequence[str]] = None
    max_missing_row_drop_pct: float = 0.01  # 1% default

    # Optional duplicate summaries by candidate keys (identity checks)
    candidate_keys: Optional[Sequence[Sequence[str]]] = None

    # Report depth
    top_value_counts: int = 5  # top-k categories per categorical column


# -----------------------------
# Column name normalization
# -----------------------------

_COLUMN_NORMALIZE_RE_SPACES_HYPHENS = re.compile(r"[ \-]+")
_COLUMN_NORMALIZE_RE_INVALID = re.compile(r"[^a-z0-9_]", re.IGNORECASE)
_COLUMN_NORMALIZE_RE_MULTI_UNDERSCORE = re.compile(r"_+")


def normalize_column_name(name: Any) -> str:
    """
    Normalize a column name to snake_case.

    - Lowercase
    - Strip whitespace
    - Replace spaces/hyphens with underscores
    - Remove non-alphanumeric characters except underscore
    - Collapse multiple underscores
    - Strip leading/trailing underscores

    Designed to be idempotent (safe to run multiple times).
    """
    s = "" if name is None else str(name)
    s = s.strip().lower()
    s = _COLUMN_NORMALIZE_RE_SPACES_HYPHENS.sub("_", s)
    s = _COLUMN_NORMALIZE_RE_INVALID.sub("", s)
    s = _COLUMN_NORMALIZE_RE_MULTI_UNDERSCORE.sub("_", s)
    s = s.strip("_")
    return s


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a shallow copy with normalized column names."""
    out = df.copy(deep=False)
    out.columns = [normalize_column_name(column) for column in out.columns]
    return out


def ensure_unique_columns(columns: Sequence[str]) -> Tuple[List[str], Dict[str, List[int]]]:
    """
    Ensure unique column names by suffixing duplicates with _2, _3, ...

    Returns:
        new_columns: unique column names
        collisions: mapping base_name -> list of original positions that collided
    """
    seen: Dict[str, int] = {}
    new_cols: List[str] = []
    collisions: Dict[str, List[int]] = {}

    for idx, col in enumerate(columns):
        base = col if col else "unnamed"
        if base not in seen:
            seen[base] = 1
            new_cols.append(base)
        else:
            seen[base] += 1
            new_name = f"{base}_{seen[base]}"
            new_cols.append(new_name)
            collisions.setdefault(base, []).append(idx)

    return new_cols, collisions


# -----------------------------
# Inspection utilities
# -----------------------------

def _safe_preview_records(df: pd.DataFrame, n: int) -> List[Dict[str, Any]]:
    """
    Return up to n rows as list-of-dicts, safe for JSON serialization.
    Avoid dumping huge previews into reports.
    """
    if n <= 0 or df.empty:
        return []
    preview = df.head(n).copy()
    return json.loads(preview.to_json(orient="records"))


def missingness_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return missingness summary table with counts and percentages."""
    total = len(df)
    miss = df.isna().sum()
    pct = (miss / total * 100.0) if total else miss * 0.0
    out = pd.DataFrame({"missing_count": miss, "missing_pct": pct})
    return out.sort_values(["missing_count", "missing_pct"], ascending=False)


def duplicate_summary(df: pd.DataFrame, subset: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """
    Summarize duplicates for the chosen subset definition.

    duplicated_rows_beyond_first:
        counts rows flagged True by duplicated() (default keep='first')
    rows_in_duplicate_groups:
        counts all rows involved in duplicates (keep=False)
    """
    if df.empty:
        return {
            "duplicated_rows_beyond_first": 0,
            "rows_in_duplicate_groups": 0,
            "subset": list(subset) if subset else None,
        }

    dup_beyond_first = int(df.duplicated(subset=subset).sum())
    rows_in_groups = int(df.duplicated(subset=subset, keep=False).sum())
    return {
        "duplicated_rows_beyond_first": dup_beyond_first,
        "rows_in_duplicate_groups": rows_in_groups,
        "subset": list(subset) if subset else None,
    }


def numeric_sanity(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Basic numeric sanity checks: min, max, inf count, missing count."""
    out: Dict[str, Dict[str, Any]] = {}
    num_cols = df.select_dtypes(include=[np.number]).columns

    for c in num_cols:
        s = df[c]
        if len(s):
            arr = s.to_numpy(dtype="float64", copy=False)
            inf_count = int(np.isinf(arr).sum())
        else:
            inf_count = 0

        out[c] = {
            "min": None if s.dropna().empty else float(s.min()),
            "max": None if s.dropna().empty else float(s.max()),
            "inf_count": inf_count,
            "missing_count": int(s.isna().sum()),
        }
    return out


def categorical_sanity(df: pd.DataFrame, top_k: int = 5) -> Dict[str, Dict[str, Any]]:
    """Basic categorical sanity checks: nunique + top value counts (including NA)."""
    out: Dict[str, Dict[str, Any]] = {}
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns

    for c in cat_cols:
        vc = df[c].value_counts(dropna=False).head(top_k)
        top = [{"value": ("<NA>" if pd.isna(k) else str(k)), "count": int(v)} for k, v in vc.items()]
        out[c] = {
            "nunique_including_na": int(df[c].nunique(dropna=False)),
            "top_values": top,
            "missing_count": int(df[c].isna().sum()),
        }
    return out


# -----------------------------
# Stage-1 runner
# -----------------------------

def run_stage1(df: pd.DataFrame, config: Stage1Config = Stage1Config()) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run Stage-1 structural cleaning + produce an audit report.

    Returns:
        cleaned_df: DataFrame (copy) after safe structural operations
        report: JSON-serializable dict with summaries and actions taken
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("run_stage1 expects a pandas DataFrame")

    actions: List[str] = []
    warnings: List[str] = []
    working = df.copy()

    # 1) Normalize column names
    if config.normalize_column_names:
        old_cols = list(working.columns)
        working = normalize_columns(working)
        new_cols = list(working.columns)
        actions.append("normalized_column_names" if old_cols != new_cols else "normalized_column_names (no_change)")

    # 2) Ensure unique column names
    collisions: Dict[str, List[int]] = {}
    if config.enforce_unique_column_names:
        cols = list(map(str, working.columns))
        unique_cols, collisions = ensure_unique_columns(cols)
        if unique_cols != cols:
            working.columns = unique_cols
            actions.append("enforced_unique_column_names")
        else:
            actions.append("enforced_unique_column_names (no_change)")

    # 3) Optional minimal-damage row drops (explicit columns only)
    dropped_rows = 0
    dropped_details: List[Dict[str, Any]] = []
    if config.drop_rows_missing_in:
        cols = [normalize_column_name(c) for c in config.drop_rows_missing_in]
        missing_tbl = missingness_table(working)
        total_rows = len(working)

        for c in cols:
            if c not in working.columns:
                warnings.append(f"drop_rows_missing_in: column '{c}' not found; skipping")
                continue

            miss_count = int(missing_tbl.loc[c, "missing_count"])
            miss_pct = float(missing_tbl.loc[c, "missing_pct"]) / 100.0 if total_rows else 0.0

            if miss_count > 0 and miss_pct <= config.max_missing_row_drop_pct:
                before = len(working)
                working = working.dropna(subset=[c])
                removed = before - len(working)
                dropped_rows += removed
                dropped_details.append({"column": c, "removed_rows": removed, "missing_pct_before": miss_pct})
            elif miss_count > 0:
                warnings.append(
                    f"drop_rows_missing_in: '{c}' missing={miss_count} ({miss_pct:.2%}) exceeds max_missing_row_drop_pct; deferred"
                )

        actions.append(f"dropped_rows_for_missingness: {dropped_rows}")

    # 4) Build report
    miss_tbl = missingness_table(working)
    report: Dict[str, Any] = {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "module": "cleaning_pipeline.py",
            "stage": "stage1_structural",
            "config": asdict(config),
        },
        "summary": {
            "rows": int(working.shape[0]),
            "cols": int(working.shape[1]),
            "missing_total_cells": int(working.isna().sum().sum()),
            "duplicate_rows_fullrow": duplicate_summary(working, subset=None),
        },
        "schema": {
            "columns": list(map(str, working.columns)),
            "dtypes": {str(k): str(v) for k, v in working.dtypes.items()},
            "column_name_collisions": collisions,
        },
        "previews": {
            "head": _safe_preview_records(working, config.preview_rows),
            "tail": _safe_preview_records(working.tail(config.preview_rows), config.preview_rows) if config.preview_rows > 0 else [],
        },
        "missingness": {
            "table": miss_tbl.reset_index().rename(columns={"index": "column"}).to_dict(orient="records"),
        },
        "sanity": {
            "numeric": numeric_sanity(working),
            "categorical": categorical_sanity(working, top_k=config.top_value_counts),
        },
        "duplicates": {
            "candidate_keys": [],
        },
        "actions": actions,
        "row_drop_details": dropped_details,
        "warnings": warnings,
    }

    # Candidate key duplicate summaries
    if config.candidate_keys:
        key_summaries = []
        for key_cols in config.candidate_keys:
            cols = [normalize_column_name(c) for c in key_cols]
            missing = [c for c in cols if c not in working.columns]
            if missing:
                warnings.append(f"candidate_keys: columns not found {missing}; skipping key {cols}")
                continue
            key_summaries.append(duplicate_summary(working, subset=cols))
        report["duplicates"]["candidate_keys"] = key_summaries

    return working, report


# -----------------------------
# Artifact saving
# -----------------------------

def save_stage1_artifacts(
    cleaned_df: pd.DataFrame,
    report: Dict[str, Any],
    processed_dir: Path,
    basename: str,
    stage_tag: str = "stage1_structural",
    date_prefix: Optional[str] = None,
    file_ext: str = "csv",
) -> Tuple[Path, Path]:
    """
    Save the cleaned dataset + JSON report into processed_dir.

    Naming:
        <date>_<basename>_<stage_tag>.<ext>
        <date>_<basename>_<stage_tag>_report.json
    """
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    date_str = date_prefix or datetime.now().strftime("%Y-%m-%d")
    base = normalize_column_name(basename) or "dataset"

    data_path = processed_dir / f"{date_str}_{base}_{stage_tag}.{file_ext}"
    report_path = processed_dir / f"{date_str}_{base}_{stage_tag}_report.json"

    ext = file_ext.lower()
    if ext == "csv":
        cleaned_df.to_csv(data_path, index=False)
    elif ext in {"parquet", "pq"}:
        cleaned_df.to_parquet(data_path, index=False)
    else:
        raise ValueError("file_ext must be 'csv' or 'parquet'/'pq'")

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    LOGGER.info(f"Saved cleaned data: {data_path}")
    LOGGER.info(f"Saved report:       {report_path}")
    return data_path, report_path


# -----------------------------
# CLI (optional convenience)
# -----------------------------

def _cli() -> int:
    """
    Minimal command line interface.

    Example:
      python cleaning_pipeline.py --input 01_data/raw/titanic.csv --processed 01_data/processed --name titanic
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run Stage-1 structural cleaning + generate a JSON audit report.")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--processed", required=True, help="Processed directory to save outputs")
    parser.add_argument("--name", required=True, help="Dataset basename used in output filenames")
    parser.add_argument("--drop-missing-in", nargs="*", default=None, help="Columns to drop rows for (tiny-missing only)")
    parser.add_argument("--max-missing-pct", type=float, default=1.0, help="Max missing percentage for row-dropping per column (default 1.0)")
    parser.add_argument("--preview-rows", type=int, default=5, help="Number of preview rows stored in report")
    parser.add_argument("--ext", default="csv", choices=["csv", "parquet", "pq"], help="Output file extension")
    args = parser.parse_args()

    input_path = Path(args.input)
    processed_dir = Path(args.processed)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    cfg = Stage1Config(
        preview_rows=args.preview_rows,
        drop_rows_missing_in=args.drop_missing_in,
        max_missing_row_drop_pct=args.max_missing_pct / 100.0,
    )

    cleaned, report = run_stage1(df, cfg)
    save_stage1_artifacts(
        cleaned, report,
        processed_dir=processed_dir,
        basename=args.name,
        stage_tag="stage1_structural",
        file_ext=args.ext,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
