# Survey311 Aug 2026 Data Cleaning Decision Record

**Purpose:** Document inspection-based decisions before applying transformations so that the cleaned dataset is reproducible, auditable, and defensible.

- **Dataset:** [NYC 311 Resolution Satisfaction Survey](https://data.cityofnewyork.us/City-Government/311-Resolution-Satisfaction-Survey/5ijn-vbdv), NYC Open Data
- **Owner:** Alexander Perez
- **Date started:** 2026-08-18
- **Last updated:** 2026-10-27
- **Scope:** Setup and Cleaning, Stage 0-1
- **Raw input:** `311_Resolution_Satisfaction_Survey_20260814.csv`
- **Final processed artifact:** `311_Resolution_Satisfaction_Clean3_20261027.csv`

## Definition of Done

The cleaning stage is complete when:

- column names are consistently formatted in `snake_case`;
- data types are inspected and only safe transformations are applied;
- missingness is summarized and a policy exists for every affected column;
- obvious invalid values are investigated and handled with a documented rationale;
- fully duplicated rows and candidate keys are assessed;
- the final processed artifact is saved with a versioned name;
- the saved artifact is reloaded and checked; and
- this decision record is aligned with the final cleaning notebook.

## 0. Project Structure and Reproducibility

- **Path strategy:** Project paths are resolved through `survey311.paths`. Data loading and saving are handled through `survey311.project_io` rather than notebook-specific absolute paths.
- **Relevant folders:** `/01_data/raw`, `/01_data/processed`, `/02_notebooks`, `/03_src`, and `/06_reports`.
- **Project package:** `survey311`, installed in editable mode.
- **Environment:** Conda environment `cleaning_phase1`, Python 3.11.
- **Artifact naming convention:** `311_Resolution_Satisfaction_CleanN_YYYYMMDD.csv`, where `N` identifies the cleaning checkpoint.
- **Primary notebook:** `01_data_ingestion_cleaning.ipynb`.
- **Reproducibility check:** The final notebook was executed from a restarted kernel and completed from top to bottom without errors.

## 1. Baseline Observation Summary

### 1.1 Dataset Snapshot

- **Rows:** 549,244
- **Columns:** 11
- **Observation unit:** One survey response associated with a NYC 311 service request.

| Original column | Initial dtype | Role |
|---|---:|---|
| Unique Key | string | Candidate row identifier |
| Agency Acronym | string | Agency identifier |
| Agency Name | string | Human-readable agency label |
| Complaint Type | string | Categorical service-request classification |
| Descriptor | string | Additional complaint detail |
| Borough | string | Reported-problem location |
| Resolution Description | string | Semi-structured resolution text |
| Survey Year | integer | Temporal component |
| Survey Month | integer | Temporal component |
| Satisfaction Response | string | Main analytical outcome |
| Dissatisfaction Reason | string | Conditional survey response |

No obvious anomalies were identified from the initial head and tail inspection.

### 1.2 Baseline Missingness

| Column | Missing rows | Missing rate |
|---|---:|---:|
| Dissatisfaction Reason | 209,521 | 38.147% |
| Descriptor | 18,291 | 3.330% |
| Borough | 9,357 | 1.704% |
| Resolution Description | 2,006 | 0.365% |
| Agency Name | 101 | 0.018% |

Missingness alone was not treated as evidence that rows or columns should be removed. Each affected variable was evaluated according to survey logic, domain meaning, and planned analytical use.

### 1.3 Duplicates and Candidate Key

- Fully duplicated rows: **0**.
- `Unique Key` contained 549,244 nonmissing distinct values across 549,244 rows.
- `Unique Key` was therefore accepted as the candidate row identifier for this dataset version.

### 1.4 Distinct-Value Convention

The initial `data_overview()` output counted missing values as an additional level for categorical summaries. By contrast, pandas `.nunique()` excludes missing values by default. This explains apparent one-level differences in fields such as `Agency Name`, `Descriptor`, and `Borough`.

Before repair, `Agency Name` contained 20 distinct nonmissing values, plus missing values. After cleaning, the dataset contains 19 agency acronyms and 19 corresponding agency names.

## 2. Column Inventory

- **Formal modelling target:** None defined during Stage 1.
- **Primary analytical outcome:** `satisfaction_response`.
- **Identifier:** `unique_key`.
- **Categorical variables:** `agency_acronym`, `agency_name`, `complaint_type`, `descriptor`, `borough`, `satisfaction_response`, and `dissatisfaction_reason`.
- **Semi-structured text:** `resolution_description`.
- **Temporal variables:** `survey_year`, `survey_month`, and the derived `survey_period`.
- **Persistent Boolean variables:** None. Temporary Boolean masks were used for validation.
- **Highest-missing variable:** `dissatisfaction_reason`, with 38.147% missingness.

## 3. Cleaning Decisions

### 3.1 Global Decisions

- Column names were normalized to `snake_case`.
- `survey_year` and `survey_month` were retained as integer columns.
- A monthly `survey_period` variable with dtype `Period[M]` was added for later aggregation and time-based analysis.
- Missingness was evaluated separately for every affected variable.
- No rows were removed solely because of missing values.
- Structurally meaningful missingness was retained.
- Only missing or invalid `agency_name` values that could be recovered deterministically were repaired.
- Heavy imputation, feature engineering, encoding, and scaling were deferred beyond Stage 1.

### 3.2 Column Name Normalization

- **Columns:** All columns.
- **Inspection:** Original column names contained spaces and title-style capitalization.
- **Decision:** Convert all column names to `snake_case`.
- **Rationale:** Consistent programmatic names reduce quoting and formatting errors and are convenient for Python-based analysis.
- **Action:** Applied `normalize_columns(df)` from `survey311.cleaning_pipeline`.
- **Validation:** The normalized names were inspected and confirmed to be unique.

### 3.3 Survey Period

- **Columns:** `survey_year`, `survey_month`.
- **Inspection:** Both columns were nonmissing integers. Months were within 1-12, and years ranged from 2022 to 2026.
- **Decision:** Retain the original columns and create `survey_period` as a monthly period.
- **Rationale:** A monthly period supports grouping and time-based EDA without discarding the original components.
- **Action:** Created `survey_period` with `pd.PeriodIndex(..., freq="M")`.
- **Validation:** The derived year and month matched the original columns for every row. The resulting range was 2022-09 through 2026-08, with no missing periods.

## 4. Variable-Level Missingness Decisions

### 4.1 Dissatisfaction Reason

- **Inspection:** Examined missingness, distinct response values, and the relationship between `satisfaction_response` and the presence of a dissatisfaction reason.
- **Findings:** The field is governed primarily by survey skip logic. A reason was provided for 339,723 of the 340,316 dissatisfied responses. The remaining 593 dissatisfied responses without a reason represent 0.174% of dissatisfied respondents and 0.108% of the complete dataset. All 208,928 non-dissatisfied responses correctly lacked a dissatisfaction reason.
- **Decision:** Retain the missing values.
- **Rationale:** Most missingness means that the question was not applicable or not presented, rather than that data were accidentally lost. The 593 exceptions are too few to justify deleting otherwise usable survey records.
- **Action:** No transformation and no row deletion.
- **Deferred:** Any task-specific encoding of structural missingness will be decided during EDA or modelling.

### 4.2 Descriptor

- **Inspection:** Examined missingness, distinct counts, reproducible row samples, semantic pairings with `complaint_type`, and missingness rates by complaint type.
- **Findings:** `descriptor` had 18,291 missing values, or 3.330%. Descriptors provide additional detail associated with complaint types but are not required for every request. Missingness was strongly concentrated in particular complaint types: all 8,901 agency-specific Literature Request records lacked a descriptor, followed by 6,647 missing descriptors for Encampment.
- **Decision:** Retain the missing values.
- **Rationale:** The systematic concentration by complaint type supports structural rather than random missingness. The remaining fields in these rows retain analytical value.
- **Action:** No transformation and no row deletion.
- **Deferred:** Filtering, explicit missing-category encoding, or other treatment will depend on the later analytical question.

### 4.3 Borough

- **Inspection:** Examined missingness, distinct nonmissing borough values, the data-dictionary definition, and missingness rates by complaint type.
- **Findings:** `borough` had 9,357 missing values, or 1.704%. The five expected boroughs were present among nonmissing records. The data dictionary states that requests not requiring a customer-provided location are recorded as `N/A`; standard CSV parsing interprets this value as missing. Missingness was concentrated in several complaint types, including administrative DOF Parking requests and some highway, bridge, and transport-related requests.
- **Decision:** Retain the missing values.
- **Rationale:** A missing borough can be meaningful because not every service request requires a location. Imputing a borough would invent geographic information.
- **Action:** No transformation and no row deletion.
- **Deferred:** Any task-specific missing-category treatment will be decided during EDA or modelling.

### 4.4 Resolution Description

- **Inspection:** Examined missingness, the most frequent descriptions, a reproducible random sample of less frequent distinct descriptions, and the documented meaning of `See notes.`.
- **Findings:** `resolution_description` had 2,006 missing values, or 0.365%. The field contains predominantly standardized or semi-standardized agency responses. `See notes.` occurred in 5,624 records, or approximately 1.02%, and is a legitimate value indicating that additional details were communicated privately. It is not missing data.
- **Decision:** Retain missing values and preserve the recorded text unchanged.
- **Rationale:** The missingness rate is low, the remaining variables in affected rows are useful, and text imputation would not be defensible.
- **Action:** No transformation, text imputation, or row deletion.
- **Deferred:** Text-specific analysis or feature engineering will be considered only if required by a later analytical task.

### 4.5 Agency Name and Agency Acronym

- **Inspection:** Compared missingness, counted distinct values, and tested the functional dependency `agency_acronym -> agency_name`.
- **Findings:** `agency_acronym` had no missing values. `agency_name` had 101 missing values. Four acronyms appeared to map to two names because the invalid system-like value `nyc311-prd` occurred in 452 rows: DSNY 432, NYPD 17, DPR 2, and OTI 1.
- **Validation:** After excluding missing names and `nyc311-prd`, every one of the 19 agency acronyms mapped to exactly one valid full name. The correct names of the four affected agencies were also checked against official NYC sources.
- **Decision:** Build a complete 19-agency acronym-to-name reference mapping from validated dataset records. Use it only to repair rows where `agency_name` is missing or equals `nyc311-prd`.
- **Rationale:** The complete acronym provides a deterministic and evidence-based way to recover the corresponding full name. No agency name was inferred from an uncertain or ambiguous source.
- **Action:** Repaired 553 rows: 101 missing names and 452 invalid values.
- **Post-repair validation:**
  - missing `agency_name` values: 0;
  - occurrences of `nyc311-prd`: 0;
  - agency acronyms: 19;
  - agency names: 19;
  - each acronym maps to exactly one name;
  - row count and index remained unchanged; and
  - valid names outside the repair population and all unrelated columns remained unchanged.

Official reference pages used for the anomalous agencies:

- [Department of Sanitation](https://www.nyc.gov/site/dsny/index.page)
- [Department of Parks and Recreation](https://www.nycgovparks.org/)
- [New York City Police Department](https://www.nyc.gov/site/nypd/index.page)
- [Office of Technology and Innovation](https://www.nyc.gov/content/oti/pages/)

## 5. Final Validation Summary

| Check | Result |
|---|---:|
| Final rows | 549,244 |
| Final columns | 12 |
| Fully duplicated rows | 0 |
| Missing `unique_key` values | 0 |
| Distinct `unique_key` values | 549,244 |
| Missing `agency_name` values | 0 |
| Remaining `nyc311-prd` values | 0 |
| Agency acronyms | 19 |
| Agency names | 19 |
| One name per acronym | Confirmed |

The final dataset deliberately retains documented structural missingness in `dissatisfaction_reason`, `descriptor`, `borough`, and `resolution_description`.

## 6. Cleaned Dataset Artifacts

| Artifact | Date | Status and purpose |
|---|---|---|
| `311_Resolution_Satisfaction_Clean1_20260825.csv` | 2026-08-25 | Intermediate checkpoint after column normalization and creation of `survey_period` |
| `311_Resolution_Satisfaction_Clean2_20261020.csv` | 2026-10-20 | Intermediate checkpoint after the agency-name repair |
| `311_Resolution_Satisfaction_Clean3_20261027.csv` | 2026-10-27 | Final Stage 1 cleaned artifact produced by the reorganized reproducible notebook |

### CSV Type Note

CSV does not preserve pandas extension dtypes such as `Period[M]`. When Clean3 is reloaded, `survey_period` should be reconstructed explicitly with `pd.PeriodIndex(..., freq="M")`, or the project may later add a Parquet artifact if native dtype preservation becomes important.

## 7. Deferred Items

No required Stage 1 cleaning actions remain. The following task-specific decisions are intentionally deferred:

- analytical treatment of structural missingness in `dissatisfaction_reason`;
- possible missing-category encoding for `descriptor` or `borough`;
- text analysis or feature engineering for `resolution_description`;
- categorical encoding, scaling, and modelling transformations; and
- selection of one agency representation for modelling to avoid using the semantically redundant acronym and full-name fields simultaneously.

## 8. Stage Completion Decision

The Stage 0-1 cleaning process is complete. The dataset is suitable for exploratory data analysis, subject to the documented interpretation of structural missingness and the explicit reconstruction of `survey_period` after CSV reload.
