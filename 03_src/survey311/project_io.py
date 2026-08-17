from __future__ import annotations
"""Input/output helpers for project data and exported tables."""

"""
Project I/O utilities.

Purpose
-------
Provide standardized read/write helpers for project datasets and
outputs while keeping notebooks free from hard-coded paths.

Design principles
-----------------
- Prefer relative project paths.
- Prefer Parquet for processed analytical data.
- Use CSV/Excel mainly for interoperability and reporting.
- Return output paths instead of printing them.
"""

# =============================================================================
# Notes
# =============================================================================
#
# Preferred workflow
# ------------------
# Raw data:
#     read_csv_from_raw()
#     read_excel_from_raw()
#     read_parquet_from_raw()
#
# Processed analytical data:
#     write_parquet_to_processed()
#     read_parquet_from_processed()
#
# Client / human-readable exports:
#     write_csv_to_processed()
#     write_excel_to_processed()
#
#
# Parquet
# --------
# Parquet preserves pandas data types (e.g. datetime, nullable integers,
# categoricals) much better than CSV or Excel and should be the preferred
# format for intermediate analytical datasets.
#
# Requires:
#     pyarrow
#
# Install if needed:
#     conda install pyarrow
# or
#     pip install pyarrow
#
# =============================================================================



from pathlib import Path
from typing import Any

import pandas as pd

from .paths import PROC_DIR, RAW_DIR, TABLES_DIR


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _resolve_path(directory: Path, filename: str | Path) -> Path:
    """
    Build a path inside a project directory.

    Absolute paths are rejected so that project I/O remains contained
    within the expected folder structure.
    """
    filename = Path(filename)

    if filename.is_absolute():
        raise ValueError(
            "filename must be relative to the project directory, "
            f"not an absolute path: {filename}"
        )

    return directory / filename


def _prepare_output_path(
    directory: Path,
    filename: str | Path,
) -> Path:
    """Build an output path and create its parent folders if needed."""
    output_path = _resolve_path(directory, filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


# ---------------------------------------------------------------------
# Read RAW
# ---------------------------------------------------------------------

def read_csv_from_raw(
    filename: str | Path,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a CSV file from ``01_data/raw``."""
    path = _resolve_path(RAW_DIR, filename)
    return pd.read_csv(path, **kwargs)


def read_excel_from_raw(
    filename: str | Path,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read an Excel file from ``01_data/raw``."""
    path = _resolve_path(RAW_DIR, filename)
    return pd.read_excel(path, **kwargs)


def read_parquet_from_raw(
    filename: str | Path,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a Parquet file from ``01_data/raw``."""
    path = _resolve_path(RAW_DIR, filename)
    return pd.read_parquet(path, **kwargs)


# ---------------------------------------------------------------------
# Read PROCESSED
# ---------------------------------------------------------------------

def read_csv_from_processed(
    filename: str | Path,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a CSV file from ``01_data/processed``."""
    path = _resolve_path(PROC_DIR, filename)
    return pd.read_csv(path, **kwargs)


def read_excel_from_processed(
    filename: str | Path,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read an Excel file from ``01_data/processed``."""
    path = _resolve_path(PROC_DIR, filename)
    return pd.read_excel(path, **kwargs)


def read_parquet_from_processed(
    filename: str | Path,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a Parquet file from ``01_data/processed``."""
    path = _resolve_path(PROC_DIR, filename)
    return pd.read_parquet(path, **kwargs)


# ---------------------------------------------------------------------
# Write PROCESSED
# ---------------------------------------------------------------------

def write_csv_to_processed(
    df: pd.DataFrame,
    filename: str | Path,
    index: bool = False,
    **kwargs: Any,
) -> Path:
    """
    Write a DataFrame as CSV to ``01_data/processed``.

    CSV is suitable for interoperability, but it does not preserve all
    pandas data types.
    """
    output_path = _prepare_output_path(PROC_DIR, filename)
    df.to_csv(output_path, index=index, **kwargs)
    return output_path


def write_excel_to_processed(
    df: pd.DataFrame,
    filename: str | Path,
    index: bool = False,
    **kwargs: Any,
) -> Path:
    """
    Write a DataFrame as Excel to ``01_data/processed``.

    Excel is useful for human review and client-facing exchange.
    """
    output_path = _prepare_output_path(PROC_DIR, filename)
    df.to_excel(output_path, index=index, **kwargs)
    return output_path


def write_parquet_to_processed(
    df: pd.DataFrame,
    filename: str | Path,
    index: bool = False,
    **kwargs: Any,
) -> Path:
    """
    Write a DataFrame as Parquet to ``01_data/processed``.

    Parquet is preferred for processed analytical data because it
    preserves data types more reliably than CSV or Excel.
    """
    output_path = _prepare_output_path(PROC_DIR, filename)
    df.to_parquet(output_path, index=index, **kwargs)
    return output_path


# ---------------------------------------------------------------------
# Write OUTPUT TABLES
# ---------------------------------------------------------------------

def write_table(
    df: pd.DataFrame,
    filename: str | Path,
    index: bool = False,
    **kwargs: Any,
) -> Path:
    """
    Save a final table to ``05_outputs/tables``.

    The output format is inferred from the filename extension.
    Supported formats are CSV, Excel, and Parquet.
    """
    output_path = _prepare_output_path(TABLES_DIR, filename)
    suffix = output_path.suffix.lower()

    if suffix == ".csv":
        df.to_csv(output_path, index=index, **kwargs)
    elif suffix in {".xlsx", ".xls"}:
        df.to_excel(output_path, index=index, **kwargs)
    elif suffix in {".parquet", ".pq"}:
        df.to_parquet(output_path, index=index, **kwargs)
    else:
        raise ValueError(
            "Unsupported table format. Use .csv, .xlsx, .xls, "
            f".parquet, or .pq. Received: {suffix or '<no suffix>'}"
        )

    return output_path




