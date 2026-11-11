# Multiple device selections are allowed, so brand percentages may sum to more than 100%.

from pathlib import Path
import os
import sys
import pandas as pd

# Resolve paths relative to this script, regardless of the working directory.
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from Output.JournalTable import journal_table
from Output.JournalHChart import journal_h_chart

# Load original survey data without modifying the source file.
CSV_PATH = Path(os.environ.get('WEARABLE_SURVEY_CSV', 'private/survey.csv'))
df = pd.read_csv(CSV_PATH, skiprows=[1, 2], dtype=str)

# Remove survey preview responses
df = df[df["Status"] != "Survey Preview"].copy()

# Keep participants who currently use a wearable
df = df[df["Q8"] == "Yes"].copy()

# Wearable device columns
devices = {
    "Q9_1": "Apple Watch",
    "Q9_2": "Fitbit/Google",
    "Q9_3": "Garmin",
    "Q9_4": "Samsung Galaxy Watch",
    "Q9_5": "Oura Ring",
    "Q9_6": "WHOOP",
    "Q9_7": "Other"
}

# Validate the expected survey columns before calculating counts.
required_columns = ["Status", "Q8", *devices]
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise KeyError(f"Missing expected survey columns: {missing_columns}")

# Qualtrics multi-select exports typically store a selected response as a
# nonblank cell. Treat missing values and whitespace-only cells as unselected.
def is_selected(series):
    return series.astype("string").str.strip().fillna("").ne("")

# Count users of each brand
results = []

for column, brand in devices.items():
    count = int(is_selected(df[column]).sum())

    results.append({
        "Brand": brand,
        "Users": count,
        "Percentage": round(count / len(df) * 100, 2)
    })

# Create results dataframe
popularity = pd.DataFrame(results)

# Sort from most popular to least popular
popularity = popularity.sort_values(
    by="Users",
    ascending=False
).reset_index(drop=True)

# Add ranking
popularity.insert(0, "Rank", popularity.index + 1)

# Send the complete Q1 result to the reusable journal-table formatter.
# Q1 performs the analysis; JournalTable handles all presentation.
report_table = journal_table(
    data=popularity.drop(columns=["Percentage"]),
    title="Table 1. Wearable Device Brand Distribution",
    columns={
        "Rank": "Rank",
        "Brand": "Wearable device",
        "Users": "n (%)",
    },
    decimals=1,
    percentage_denominators=len(df),
    note=(
        f"Percentages are based on {len(df)} current wearable users (Q8 = Yes). "
        f"{int(pd.concat([is_selected(df[col]) for col in devices], axis=1).any(axis=1).sum())} provided at least one "
        f"brand response; {int(popularity['Users'].sum())} brand selections were recorded. "
        "Multiple selections were permitted, so percentages may exceed 100% when summed."
    )
)

# Use the exact document created by the shared table writer. A rerun gets a
# numbered document, so recalculating its filename would target the wrong one.
word_output = report_table.attrs["word_output_path"]

# Create a horizontal chart from the same device counts and percentages.
# Append it to the Word document produced by JournalTable.
journal_h_chart(
    data=popularity,
    category="Brand",
    value="Percentage",
    counts="Users",
    title="Wearable Device Use Among College Students",
    xlabel="Percentage of current wearable users (%)",
    note=(
        f"Percentages are based on {len(df)} current wearable users (Q8 = Yes). "
        "Respondents could select multiple devices; percentages may sum to more than 100%."
    ),
    filename="Wearable_Device_Popularity",
    word_document=word_output,
)
