# NYC 311 Resolution Satisfaction Survey

## Project Overview

This project explores customer satisfaction with the handling and resolution of NYC 311 service requests. It uses survey data published by NYC Open Data to examine overall satisfaction and identify meaningful patterns across available service, agency, geographic, and temporal dimensions.

The project is currently in development. Findings and recommendations will be added after data validation, cleaning, and exploratory analysis.

## Business Objective

Analyze NYC 311 resolution satisfaction survey responses to:

* Describe the overall distribution of customer satisfaction.
* Identify meaningful differences across available service and geographic segments.
* Detect areas that may warrant further operational investigation.
* Communicate findings without treating descriptive associations as causal evidence.

The primary outcome is the survey response to the statement:

> “Overall, I am satisfied with the way my Service Request was handled.”

The final analytical questions and success metrics will be refined after the initial data inspection.

## Personal Learning Objective

Execute and ship a polished, reproducible exploratory data analysis project with greater independence, strengthening:

* Python and pandas fluency
* Descriptive-statistical reasoning
* Visualization selection and design
* Evidence-based interpretation
* Analytical and business communication
* Reproducible project workflow

## Data Source

The project uses the **NYC 311 Resolution Satisfaction Survey**, provided through NYC Open Data.

* Dataset: [311 Resolution Satisfaction Survey](https://data.cityofnewyork.us/City-Government/311-Resolution-Satisfaction-Survey/5ijn-vbdv)
* Provider: NYC Office of Technology and Innovation / NYC Open Data
* Unit of observation: One survey response
* Data access details: See [`DATA.md`](DATA.md)

Raw data is not stored in this repository.

## Project Structure

```text
00_admin/       Project administration and decision records
01_data/        Raw, interim, and processed data
02_notebooks/   Data inspection, cleaning, and EDA notebooks
03_src/         Reusable Python source code
04_models/       Validation and utility tests
05_outputs/     Tables, figures, and analytical outputs
06_reports/     Project report and supporting materials
```

## Planned Workflow

1. Project setup
2. Data loading and inspection
3. Cleaning and standardization
4. Cleaning Decision Record
5. Exploratory data analysis
6. Narrative report
7. README completion
8. GitHub publication
9. Retrospective
10. Python drills and final quiz

## Environment Setup

The project uses a Conda environment documented in `environment.yml`.

Create the environment:

```bash
conda env create -f environment.yml
```

Activate it:

```bash
conda activate cleaning_phase1
```

Install the local project package in editable mode:

```bash
pip install -e .
```

## Project Status

**Current phase:** Project setup

The README will be updated with analytical methods, visualizations, findings, limitations, and conclusions as the project progresses.
