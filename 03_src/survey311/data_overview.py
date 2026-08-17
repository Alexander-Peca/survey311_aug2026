"""Interactive DataFrame overview for early notebook exploration.

This utility is intended for inspection and diagnostics rather than
formal reporting.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

try:
    from IPython.display import display
except ImportError:  # pragma: no cover
    def display(obj: object) -> None:
        """Fallback display outside an IPython environment."""
        print(obj)


def data_overview(
    df: pd.DataFrame,
    top: int | None = 15,
    show_numeric_summary: bool = True,
    show_missingness: bool = True,
    show_unique_counts: bool = True,
    show_duplicates: bool = True,
    show_categoricals_preview: bool = True,
    max_cats: int = 8,
    head_rows: int = 3,
    tail_rows: int = 3,
) -> dict[str, Any]:
    """
    Display early diagnostics for a pandas DataFrame.

    Parameters
    ----------
    df:
        DataFrame to inspect.
    top:
        Number of rows to show in ranked summary tables.
        Use ``None`` to display all columns.
    show_numeric_summary:
        Whether to display descriptive statistics for numeric columns.
    show_missingness:
        Whether to display missing-value counts and rates.
    show_unique_counts:
        Whether to display unique-value counts.
    show_duplicates:
        Whether to report the number of fully duplicated rows.
    show_categoricals_preview:
        Whether to preview the most frequent levels in categorical columns.
    max_cats:
        Maximum number of categorical columns to preview.
    head_rows:
        Number of rows to display from the beginning of the DataFrame.
    tail_rows:
        Number of rows to display from the end of the DataFrame.

    Returns
    -------
    dict[str, Any]
        Dictionary containing the generated diagnostic objects.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    if top is not None and top <= 0:
        raise ValueError("top must be a positive integer or None.")

    if head_rows < 0 or tail_rows < 0:
        raise ValueError("head_rows and tail_rows must be non-negative.")

    if max_cats < 0:
        raise ValueError("max_cats must be non-negative.")

    out: dict[str, Any] = {}

    # 1) Basic structure
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]:,} columns")

    columns = df.columns.tolist()
    out["columns"] = columns

    print("\nColumns in dataset order:")
    display(columns)

    # 2) Row previews
    if head_rows:
        print(f"\nFirst {head_rows} rows:")
        display(df.head(head_rows))

    if tail_rows:
        print(f"\nLast {tail_rows} rows:")
        display(df.tail(tail_rows))

    # 3) Data types
    dtypes = df.dtypes.rename("dtype")
    out["dtypes"] = dtypes

    print("\nData types:")
    display(dtypes)

    # 4) Numeric summary
    if show_numeric_summary:
        numeric_df = df.select_dtypes(include="number")

        if numeric_df.empty:
            numeric_summary = pd.DataFrame()
            print("\nNumeric summary: no numeric columns found.")
        else:
            numeric_summary = numeric_df.describe().T
            print("\nNumeric summary:")
            display(numeric_summary)

        out["numeric_summary"] = numeric_summary

    # 5) Missingness
    if show_missingness:
        missingness = pd.DataFrame(
            {
                "missing_count": df.isna().sum(),
                "missing_rate": df.isna().mean(),
            }
        ).sort_values(
            by=["missing_count", "missing_rate"],
            ascending=False,
        )

        out["missingness"] = missingness
        out["missing_count"] = missingness["missing_count"]
        out["missing_rate"] = missingness["missing_rate"]

        if top is None:
            print("\nMissingness — all columns:")
            display(missingness)
        else:
            print(f"\nMissingness — top {top} columns by missing count:")
            display(missingness.head(top))

    # 6) Unique-value counts
    if show_unique_counts:
        unique_counts = (
            df.nunique(dropna=False)
            .sort_values(ascending=False)
            .rename("n_unique")
        )

        out["n_unique"] = unique_counts

        if top is None:
            print("\nUnique-value counts — all columns:")
            display(unique_counts)
        else:
            print(f"\nUnique-value counts — top {top} columns:")
            display(unique_counts.head(top))

    # 7) Fully duplicated rows
    if show_duplicates:
        duplicate_rows = int(df.duplicated().sum())
        out["duplicate_rows"] = duplicate_rows

        print(f"\nFully duplicated rows: {duplicate_rows:,}")

    # 8) Categorical preview
    if show_categoricals_preview:
        categorical_columns = df.select_dtypes(
            include=["object", "category", "string"]
        ).columns.tolist()

        out["categorical_columns"] = categorical_columns

        if not categorical_columns:
            print("\nCategorical preview: no categorical columns found.")
        elif max_cats == 0:
            print("\nCategorical preview disabled because max_cats=0.")
        else:
            preview_columns = categorical_columns[:max_cats]

            print(
                "\nCategorical preview "
                f"(top 10 levels for up to {max_cats} columns):"
            )

            for column in preview_columns:
                value_counts = (
                    df[column]
                    .value_counts(dropna=False)
                    .head(10)
                )

                print(f"\n• {column}")
                display(value_counts)

    return out