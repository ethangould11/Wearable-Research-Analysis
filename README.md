# Wearable Research Analysis

Python analysis and report-generation structure for a wearable-device survey.
This repository contains code and broad survey categories only. Research data,
results, charts, reports, participant records and input-file links are excluded.
The code describes the methods; it cannot reproduce the study results without
separately authorized private data.

## Questions

| Question | Comparison |
| --- | --- |
| 1 | Wearable device brand distribution |
| 2 | Wearable brands by self-rated athletic ability |
| 3 | Wearable brands by self-reported gender |
| 4 | Frequently used features by wearable brand |
| 5 | Attitude agreement by wearable brand |
| 6 | Feature usage and wearable attitudes |
| 7 | Composite health score use and wearable attitudes |
| 8 | Composite health score use and device-wearing frequency |

The existing Question 5 filename retains its `NU` marker. All eight question
scripts are included. Category definitions are survey options, not a claim
that any participant selected an option.

## Structure

- `Questions/`: the eight analysis entry points.
- `Analysis/review_q2_q4.py`: cleaning, recalculation and reconciliation for Questions 2–4.
- `Output/Journal*.py`: shared Word table and chart formatting helpers.
- `generate_reports.py`: runs the questions and verifies created or updated reports.
- `templates/`: starting point for an additional question.

## Methods

Questions 2–4 inspect export metadata, blank rows, duplicate records, eligibility,
missingness and invalid option values. Valid Other selections are retained.
Missing answers are not imputed. Checks reconcile counts with the input records
and verify that reading the source has not changed its bytes.

Questions 2–3 use stacked brand-selection counts. Athletic ability is ordered
Beginner, Recreational, Competent, Advanced, Elite. Question 4 includes a count
chart and a 100% stacked chart with brands on the horizontal axis and features
in the legend. The latter divides each feature count by the sum of feature
selections for that brand. It describes a share of feature selections.
Multiple brand and feature selections can overlap; device-specific feature
attribution is unavailable for respondents selecting several brands.

Questions 1 and 5–8 retain their existing processing. Questions 5 and 7 combine
somewhat agree and strongly agree for descriptive agreement tables. Their
denominators are people in the relevant group who answered the statement.
Question 6 uses Mann–Whitney comparisons; Question 7 uses Kruskal–Wallis tests;
the scripts apply Benjamini–Hochberg adjustment across attitude comparisons.
Question 8 uses within-frequency-group percentages. These are observational
survey comparisons and do not establish causation.

## Authorized local use

Install Python dependencies with `python3 -m pip install -r requirements.txt`.
Set `WEARABLE_SURVEY_CSV` to an authorized local Qualtrics export. The code
expects the survey column schema used in the scripts; no dataset or download
link is supplied. For example, after setting that environment variable:

```bash
python3 Analysis/review_q2_q4.py --data-only
python3 generate_reports.py
```

Generated `Data/` files and `Output/` artifacts are confidential local products.
Questions 2–4 update their current report; other questions create numbered
copies when needed. See [PRIVACY.md](PRIVACY.md) before adding any repository files.
