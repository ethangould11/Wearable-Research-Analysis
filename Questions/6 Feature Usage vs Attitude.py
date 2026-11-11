"""Q12 feature usage versus Q15 wearable attitudes."""

from pathlib import Path
import os
import sys

try:
    from scipy.stats import mannwhitneyu
    from statsmodels.stats.multitest import multipletests
except ModuleNotFoundError as exc:
    raise SystemExit(
        f"Missing dependency: {exc.name}. Install into this Python interpreter with:\n"
        f"  {sys.executable} -m pip install scipy statsmodels"
    ) from exc

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from Output.JournalTable import journal_table

CSV_PATH = Path(os.environ.get('WEARABLE_SURVEY_CSV', 'private/survey.csv'))

df = pd.read_csv(CSV_PATH, skiprows=[1, 2], dtype=str)

# Current wearable users only
df = df.loc[
    df["Status"].ne("Survey Preview")
    & df["Q8"].eq("Yes")
].copy()

FEATURES = {
    "Q12_1": "Step tracking",
    "Q12_2": "Heart monitoring",
    "Q12_3": "Sleep tracking",
    "Q12_4": "Workout tracking",
    "Q12_5": "Calorie tracking",
    "Q12_6": "Stress monitoring",
    "Q12_7": "Composite Health Score",
    "Q12_8": "Notifications",
    "Q12_9": "Mental health features",
    "Q12_10": "Other",
}

ATTITUDES = {
    "Q15_1": "Trust in accuracy",
    "Q15_2": "Meaningful feedback",
    "Q15_3": "Personalized insights",
    "Q15_4": "Improved health monitoring",
    "Q15_5": "Improved exercise performance",
    "Q15_6": "Better health decisions",
    "Q15_7": "Improved sleep habits",
    "Q15_8": "Pressure to meet metrics",
}

LIKERT = {
    "Strongly disagree": 1,
    "Somewhat disagree": 2,
    "Neither agree nor disagree": 3,
    "Somewhat agree": 4,
    "Strongly agree": 5,
}

required = ["Status", "Q8", *FEATURES, *ATTITUDES]
missing = [col for col in required if col not in df.columns]

if missing:
    raise KeyError(f"Missing survey columns: {missing}")

def selected(series):
    """Identify selected Qualtrics multi-response options."""
    return series.astype("string").str.strip().fillna("").ne("")

# Convert attitudes to numeric Likert scores.
for col in ATTITUDES:
    responses = df[col].astype("string").str.strip()
    unexpected = set(responses.dropna().unique()) - set(LIKERT) - {""}

    if unexpected:
        raise ValueError(f"Unexpected values in {col}: {unexpected}")

    df[col + "_numeric"] = responses.map(LIKERT).astype(float)

# ------------------------------------------------------------
# TABLE 1: DESCRIPTIVE MEANS AMONG FEATURE USERS
# ------------------------------------------------------------

descriptive_rows = []

for feature_col, feature_name in FEATURES.items():
    mask = selected(df[feature_col])

    row = {
        "Feature": feature_name,
        "n": int(mask.sum()),
    }

    for attitude_col, attitude_name in ATTITUDES.items():
        values = df.loc[mask, attitude_col + "_numeric"].dropna()

        row[attitude_name] = (
            round(values.mean(), 2)
            if len(values) else np.nan
        )

    descriptive_rows.append(row)

descriptive = pd.DataFrame(descriptive_rows)

descriptive_report = journal_table(
    data=descriptive,
    title="Wearable Feature Usage and Attitudes Toward Wearable Technology",
    decimals=2,
    percentage_denominators=len(df),
    note=(
        "Values represent mean Likert scores among respondents selecting "
        "each feature (1 = strongly disagree; 5 = strongly agree). "
        "Feature n includes all respondents selecting that feature; "
        f"feature percentages use all {len(df)} current wearable users as the denominator; "
        "individual attitude means exclude missing responses. "
        "Respondents could select multiple features."
    ),
)

# ------------------------------------------------------------
# TABLE 2: FEATURE USERS VERSUS NONUSERS
# ------------------------------------------------------------

comparison_rows = []

for feature_col, feature_name in FEATURES.items():
    feature_mask = selected(df[feature_col])

    for attitude_col, attitude_name in ATTITUDES.items():
        scores = df[attitude_col + "_numeric"]

        users = scores[feature_mask].dropna()
        nonusers = scores[~feature_mask].dropna()

        if len(users) < 2 or len(nonusers) < 2:
            continue

        result = mannwhitneyu(
            users,
            nonusers,
            alternative="two-sided",
            method="asymptotic",
        )

        # Rank-biserial correlation, oriented so positive values
        # indicate higher scores among feature users.
        effect = (
            2 * result.statistic / (len(users) * len(nonusers))
            - 1
        )

        comparison_rows.append({
            "Feature": feature_name,
            "Attitude": attitude_name,
            "Users n": len(users),
            "Nonusers n": len(nonusers),
            "Users mean": round(users.mean(), 2),
            "Nonusers mean": round(nonusers.mean(), 2),
            "Mean difference": round(
                users.mean() - nonusers.mean(), 2
            ),
            "Rank-biserial r": round(effect, 3),
            "p": result.pvalue,
        })

comparisons = pd.DataFrame(comparison_rows)

if not comparisons.empty:
    # Control false discovery rate across all performed tests.
    comparisons["Adjusted p"] = multipletests(
        comparisons["p"],
        method="fdr_bh",
    )[1]

    comparisons["p"] = comparisons["p"].round(4)
    comparisons["Adjusted p"] = comparisons["Adjusted p"].round(4)

    comparisons = comparisons.sort_values(
        "Adjusted p"
    ).reset_index(drop=True)

    # Q12 features as rows and Q15 attitudes as columns.
    # Each cell reports the rank-biserial effect and FDR-adjusted p-value.
    matrix = comparisons.copy()
    matrix["Result"] = matrix.apply(
        lambda row: f"{row['Rank-biserial r']:+.3f} (p={row['Adjusted p']:.3f})",
        axis=1,
    )
    matrix = matrix.pivot(index="Feature", columns="Attitude", values="Result")
    matrix = matrix.reindex(index=list(FEATURES.values()), columns=list(ATTITUDES.values()))
    matrix = matrix.reset_index()

    journal_table(
        data=matrix,
        title="Associations Between Wearable Feature Usage and Attitudes",
        decimals=3,
        word_document=descriptive_report.attrs["word_output_path"],
        note=(
            "Rows represent Q12 features and columns represent Q15 attitudes. "
            "Each cell reports rank-biserial r (Benjamini–Hochberg FDR-adjusted p-value) "
            "from a two-sided Mann–Whitney U comparison of feature users and nonusers. "
            "Positive r indicates higher attitude scores among feature users. "
            "Analyses are exploratory."
        ),
    )

print("\nAnalysis complete.")
print(f"Current wearable users: {len(df)}")
print(f"Comparisons performed: {len(comparisons)}")

if not comparisons.empty:
    print(
        "Associations with adjusted p < .05:",
        int((comparisons["Adjusted p"] < 0.05).sum())
    )
