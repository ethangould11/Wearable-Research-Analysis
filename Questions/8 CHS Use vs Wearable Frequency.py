"""Q14 overall health score use by Q11 wearable-wearing frequency."""

from pathlib import Path
import os
import sys

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from Output.JournalTable import journal_table

df = pd.read_csv(Path(os.environ.get('WEARABLE_SURVEY_CSV', 'private/survey.csv')), skiprows=[1, 2], dtype=str)
df = df.loc[df['Status'].ne('Survey Preview') & df['Q8'].eq('Yes')].copy()

WEAR_FREQUENCY = [
    'All day, every day',
    'All day, not during sleep',
    'Most of the day',
    'Only during workouts',
    'Rarely',
    'Never',
]
CHS_USE = [
    'Yes, regularly',
    'Yes, sometimes',
    'Rarely',
    'Never',
    'My device does not provide these scores',
]

required = ['Status', 'Q8', 'Q11', 'Q14']
missing = [column for column in required if column not in df.columns]
if missing:
    raise KeyError(f'Missing survey columns: {missing}')

frequency = df['Q11'].astype('string').str.strip()
chs = df['Q14'].astype('string').str.strip()
for question, responses, valid in [('Q11', frequency, WEAR_FREQUENCY), ('Q14', chs, CHS_USE)]:
    unexpected = set(responses.dropna().unique()) - set(valid) - {''}
    if unexpected:
        raise ValueError(f'Unexpected {question} responses: {unexpected}')

complete = frequency.isin(WEAR_FREQUENCY) & chs.isin(CHS_USE)
observed_frequency = [option for option in WEAR_FREQUENCY
                      if int((complete & frequency.eq(option)).sum()) > 0]
denominators = {option: int((complete & frequency.eq(option)).sum())
                for option in observed_frequency}

rows = []
for chs_option in CHS_USE:
    row = {'Overall health score use': chs_option}
    for wear_option in observed_frequency:
        row[wear_option] = int((complete & chs.eq(chs_option) & frequency.eq(wear_option)).sum())
    rows.append(row)

excluded = len(df) - int(complete.sum())
zero_groups = [option for option in WEAR_FREQUENCY if option not in observed_frequency]
zero_note = (f'No complete Q11/Q14 responses were available for: {", ".join(zero_groups)}. '
             if zero_groups else '')

journal_table(
    data=pd.DataFrame(rows),
    title='Overall Health Score Use by Wearable-Wearing Frequency',
    percentage_denominators=denominators,
    total_counts_only=True,
    note=(
        f'Analysis includes {int(complete.sum())} current wearable users with both Q11 '
        f'and Q14 responses; {excluded} current users are excluded for missing responses. '
        'Cells are n (column %), using the number of respondents in each Q11 '
        'wearing-frequency group as the denominator. The Total column and bottom '
        'row show respondent counts. ' + zero_note
    ),
)
