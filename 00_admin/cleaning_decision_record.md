# Survey311_aug2026 — Data Cleaning Decision Log

**Purpose:** Document inspection-based decisions *before* applying transformations, so the cleaned dataset is reproducible and defensible.

- **Dataset:**  NYC 311 Resolution Satisfaction Survey / https://data.cityofnewyork.us/City-Government/311-Resolution-Satisfaction-Survey/5ijn-vbdv / NYC Open Data
- **Owner:** Alexander Perez
- **Date started:** <2026-08-18>
- **Last updated:** <YYYY-MM-DD>
- **Scope:** Setup & Cleaning (Stage 0–1)
- **Definition of Done (DoD):**
  - Consistent names (snake_case)
  - Types confirmed (safe coercions only)
  - Obvious invalids handled (with rationale)
  - Missingness summarized + policy per column
  - Duplicates assessed (row + candidate keys)
  - Staged artifact saved under `/processed`
  - This decision log updated and shipped

---

## 0. Project Structure & Reproducibility
- **Project root strategy:** (e.g., `Path.cwd().parent`)
- **Folders ensured:** `/01_data/raw`, `/01_data/processed`, `/02_notebooks`, etc.
- **Artifact naming convention:** `YYYY-MM-DD_stageN_keyword.ext`
- **Environment notes:** (optional: python version, env.yml/requirements.txt)

---

## 1. Observation Summary (Baseline Facts)
### 1.1 Dataset Snapshot
- **Rows x Cols:** 549,244 rows × 11 columns
- **Column list:** 
'Unique Key',
 'Agency Acronym',
 'Agency Name',
 'Complaint Type',
 'Descriptor',
 'Borough',
 'Resolution Description',
 'Survey Year',
 'Survey Month',
 'Satisfaction Response',
 'Dissatisfaction Reason'

- **Dtypes summary:** Year and month can be merged and dtype changed to to_date
- **Head/tail anomalies:** None 

### 1.2 Missingness Overview

	                      missing_count	missing_rate
Dissatisfaction Reason	209521	0.381472
Descriptor	            18291	  0.033302
Borough	                9357	  0.017036
Resolution Description	2006	  0.003652
Agency Name	            101	    0.000184

All could be dropped saved Descriptor and Dissatisfaction reason (here ~ % 3-4 )

### 1.3 Duplicates & Candidate Keys

Fully duplicated rows: 0

### 1.4 Unique value counts

Unique value counts: 

Unique Key                549244
Descriptor                   819
Resolution Description       744
Complaint Type               226
Agency Name                   21
Agency Acronym                19
Survey Month                  12
Dissatisfaction Reason         9
Borough                        6
Survey Year                    5
Satisfaction Response          5


---

## 2. Column Inventory (Roles)
- **Target(s):** <...>
- **Identifiers:** <...>
- **Categoricals:** <...>
- **Numerics:** <...>
- **Booleans:** <...>
- **High-missing columns:** <...>

---

# 3. Cleaning Decisions

## 3.1 Global Cleaning Decisions

### <Decision title>
- **Columns:** <...>
- **Inspection:** <what was checked>
- **Decision:** <what was decided>
- **Rationale:** <why>
- **Action:** <what was applied>

---

## 3.2 Variable-Level Decisions

### <column_name>
- **Inspection:** <checks performed>
- **Findings:** <what was observed>
- **Decision:** <keep / transform / drop / defer>
- **Rationale:** <why>
- **Action:** <what was applied>
- **Deferred:** <optional>

---

## 3.3 Cross-Variable Decisions

### <relationship or issue>
- **Columns involved:** <...>
- **Inspection:** <...>
- **Findings:** <...>
- **Decision:** <...>
- **Rationale:** <...>
- **Action:** <...>

---

# 4. Cleaned Dataset Artifacts

- <artifact>
- <artifact>

# 5. Deferred Items

- <item>