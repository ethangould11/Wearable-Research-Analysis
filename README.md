<div align="center">

# Wearable Research Analysis

**Understanding wearable use, feature preferences, and attitudes toward health technology**

Python analysis · Survey research · Reproducible methods · Privacy-conscious reporting

[Results overview](RESULTS.md) · [Research methods](docs/METHODS.md) · [Privacy](PRIVACY.md) · [Analysis code](Questions/)

</div>

## About the project

This project explores how people use wearable devices and how device choices,
self-rated athletic ability, feature use, and health-technology attitudes relate
within a survey sample. Eight analyses cover device adoption, frequently used
features, composite health scores, and attitudes toward wearable feedback.

The repository presents the analytical structure and a limited public results
overview. Detailed respondent data and subgroup reports remain private.

> **Start with the [results overview](RESULTS.md).** It presents broad observed
> findings, explains what they mean, and identifies which comparisons are kept
> private to protect small groups.

## Research questions

| | Focus | What the analysis examines |
| :---: | --- | --- |
| **Q1** | Device use | Distribution of wearable brands |
| **Q2** | Athletic ability | Ability composition within each wearable brand |
| **Q3** | Gender | Gender composition within each wearable brand |
| **Q4** | Feature use | Frequently used features within each wearable brand |
| **Q5** | Attitudes by brand | Agreement with wearable attitude statements |
| **Q6** | Features and attitudes | Attitude scores among feature users and nonusers |
| **Q7** | Composite health scores | Score use and agreement with wearable attitudes |
| **Q8** | Wearing frequency | Score use across device-wearing frequency groups |

## How to read the figures

Local Q2–Q4 percentage figures use a consistent layout: **wearable brands on
the horizontal axis, categories in the legend, and bars totaling 100%.**

| Figure | What 100% represents | What a segment represents |
| --- | --- | --- |
| Q2 | Usable athletic-ability respondents within a brand | Share in an ability category |
| Q3 | Usable gender respondents within a brand | Share in a gender category |
| Q4 | All counted feature selections within a brand | Share assigned to a feature |

Respondents could select several brands and features. A person can contribute
to several brand bars. Equal-height bars support composition comparisons;
they do not equalize sample sizes or remove sampling bias. Detailed figures
and their sample sizes are generated locally and excluded from GitHub.

## Project map

```text
Wearable-Research-Analysis/
├── README.md                   Project introduction
├── RESULTS.md                  Limited public findings
├── PRIVACY.md                  Publication boundaries
├── docs/METHODS.md             Definitions, denominators, limitations
├── Questions/                  All eight analysis entry points
├── Analysis/                   Cleaning, validation, pooled-summary methods
├── Output/Journal*.py          Shared chart and Word-table formatting
├── templates/                  Template for an additional question
├── generate_reports.py        Batch report generator
└── requirements.txt            Python dependencies
```

## Methods and reproducibility

Questions 2–4 use respondent-level cleaning, explicit missing-value checks,
duplicate checks, and independent count reconciliation. Valid Other responses
are retained. Missing answers are never imputed. Python produces editable
Word tables and matching chart images using shared formatting helpers.

Questions 5–8 include descriptive agreement tables and exploratory ordinal
comparisons. The [methods page](docs/METHODS.md) explains the question-specific
denominators, statistical procedures, and limits of interpretation.

### Run with authorized private data

```bash
python3 -m pip install -r requirements.txt
export WEARABLE_SURVEY_CSV="/path/to/authorized-local-survey.csv"
python3 Analysis/review_q2_q4.py --data-only
python3 generate_reports.py
```

The input must follow the survey schema defined in the scripts. No dataset or
download link is supplied. Generated data, reports, and figures remain local.
Q2–Q4 update their current reports; other questions retain numbered copies.

## Responsible interpretation

These are descriptive and exploratory survey analyses. Self-reported usage
does not measure clinical benefit, validate device accuracy, or establish
causation. Small brand groups make some local percentages unstable. Public
findings are pooled and coarsened; they are not population estimates.

**Privacy is part of the project structure.** The repository excludes source
records, identifiers, free text, detailed cross-tabulations, and report files.
See the [publication policy](PRIVACY.md) for the exact boundary.
