"""Q15 attitude agreement (rows) by Q9 device brand (columns)."""

from pathlib import Path
import os
import sys

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from Output.JournalTable import journal_table

df = pd.read_csv(Path(os.environ.get('WEARABLE_SURVEY_CSV', 'private/survey.csv')), skiprows=[1, 2], dtype=str)
df = df.loc[df['Status'].ne('Survey Preview') & df['Q8'].eq('Yes')].copy()

DEVICE_COLUMNS = {
    'Q9_1': 'Apple Watch',
    'Q9_2': 'Fitbit/Google',
    'Q9_3': 'Garmin',
    'Q9_4': 'Samsung Galaxy Watch',
    'Q9_5': 'Oura Ring',
    'Q9_6': 'WHOOP',
    'Q9_7': 'Other',
}
ATTITUDES = {
    'Q15_1': 'Trust in accuracy',
    'Q15_2': 'Meaningful feedback',
    'Q15_3': 'Personalized insights',
    'Q15_4': 'Improved health monitoring',
    'Q15_5': 'Improved exercise performance',
    'Q15_6': 'Better health decisions',
    'Q15_7': 'Improved sleep habits',
    'Q15_8': 'Pressure to meet metrics',
}

required = ['Status', 'Q8', *DEVICE_COLUMNS, *ATTITUDES]
missing = [column for column in required if column not in df.columns]
if missing:
    raise KeyError(f'Missing survey columns: {missing}')

def selected(column):
    return df[column].astype('string').str.strip().fillna('').ne('')

device_masks = {brand: selected(column) for column, brand in DEVICE_COLUMNS.items()}
brands = sorted(device_masks, key=lambda brand: int(device_masks[brand].sum()), reverse=True)
valid_responses = {
    'Strongly disagree', 'Somewhat disagree', 'Neither agree nor disagree',
    'Somewhat agree', 'Strongly agree',
}
agree_responses = {'Somewhat agree', 'Strongly agree'}

rows = []
denominators = {}
for attitude_column, attitude in ATTITUDES.items():
    responses = df[attitude_column].astype('string').str.strip()
    unexpected = set(responses.dropna().unique()) - valid_responses - {''}
    if unexpected:
        raise ValueError(f'Unexpected responses in {attitude_column}: {unexpected}')
    answered = responses.isin(valid_responses)
    agreed = responses.isin(agree_responses)
    row = {'Attitude (agreement)': attitude}
    for brand in brands:
        row[brand] = int((agreed & device_masks[brand]).sum())
        denominators[(attitude, brand)] = int((answered & device_masks[brand]).sum())
    rows.append(row)

# Denominators vary by both statement and brand because Q15 can be unanswered.
# Format n (%) before passing the table to the shared Word formatter.
result = pd.DataFrame(rows, columns=['Attitude (agreement)', *brands])
result[brands] = result[brands].astype(object)
for index, attitude in enumerate(ATTITUDES.values()):
    for brand in brands:
        n = result.at[index, brand]
        denominator = denominators[(attitude, brand)]
        result.at[index, brand] = f'{n} ({n / denominator * 100:.1f}%)' if denominator else f'{n} (—)'

journal_table(
    data=result,
    title='Agreement With Wearable Attitudes by Device Brand',
    note=(
        f'Analysis includes {len(df)} current wearable users. Agreement combines '
        '“somewhat agree” and “strongly agree” for each Q15 statement. '
        'Cells are n (% of respondents selecting that brand who answered the statement). '
        'Device brand (Q9) allows multiple selections, so respondents may appear in '
        'multiple brand columns. Totals are counts of agreement selections, not '
        'unique respondents; percentages are omitted from totals.'
    ),
)
