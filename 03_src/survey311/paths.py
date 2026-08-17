# --- paths.py ---
from pathlib import Path

def _find_project_root(markers=(".git", "pyproject.toml", "environment.yml")) -> Path:
    """
    Walk upward from the current working directory until a known project marker is found.
    Works reliably when run from within subfolders (e.g., 02_notebooks/).

    Returns:
        Path object pointing to the detected project root.
    """
    p = Path.cwd().resolve()
    for _ in range(5):  # limit upward search depth to avoid infinite loops
        if any((p / m).exists() for m in markers):
            return p
        if p == p.parent:
            break
        p = p.parent

    # Fallback: if no marker found (e.g. running inside /02_notebooks)
    # assume project root is one level above this notebook folder
    return Path.cwd().resolve().parents[0]

# --- Anchors ---
PROJECT_ROOT = _find_project_root()

DATA_DIR    = PROJECT_ROOT / "01_data"
RAW_DIR     = DATA_DIR / "raw"
PROC_DIR    = DATA_DIR / "processed"
EXT_DIR     = DATA_DIR / "external"
INT_DIR     = DATA_DIR / "interim"

OUTPUTS_DIR = PROJECT_ROOT / "05_outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"

REPORTS_DIR = PROJECT_ROOT / "06_reports"

# Ensure key dirs exist (no error if they already exist)
for d in (RAW_DIR, PROC_DIR, EXT_DIR, INT_DIR, FIGURES_DIR, TABLES_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)
# --- END paths.py ---

