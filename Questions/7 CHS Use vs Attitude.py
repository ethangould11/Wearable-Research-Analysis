"""Q14 overall health score use versus Q15 attitude agreement."""

from pathlib import Path
import os
import sys

import pandas as pd
from scipy.stats import kruskal
from statsmodels.stats.multitest import multipletests

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from Output.JournalTable import journal_table

df = pd.read_csv(Path(os.environ.get('WEARABLE_SURVEY_CSV', 'private/survey.csv')), skiprows=[1, 2], dtype=str)
df = df.loc[df['Status'].ne('Survey Preview') & df['Q8'].eq('Yes')].copy()

CHS_OPTIONS = [
    'Yes, regularly',
    'Yes, sometimes',
    'Rarely',
    'Never',
    'My device does not provide these scores',
]
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
VALID_ATTITUDES = {
    'Strongly disagree', 'Somewhat disagree', 'Neither agree nor disagree',
    'Somewhat agree', 'Strongly agree',
}
AGREEMENT = {'Somewhat agree', 'Strongly agree'}

required = ['Status', 'Q8', 'Q14', *ATTITUDES]
missing = [column for column in required if column not in df.columns]
if missing:
    raise KeyError(f'Missing survey columns: {missing}')

chs = df['Q14'].astype('string').str.strip()
unexpected = set(chs.dropna().unique()) - set(CHS_OPTIONS) - {''}
if unexpected:
    raise ValueError(f'Unexpected Q14 responses: {unexpected}')

rows = []
for attitude_column, attitude in ATTITUDES.items():
    responses = df[attitude_column].astype('string').str.strip()
    unexpected = set(responses.dropna().unique()) - VALID_ATTITUDES - {''}
    if unexpected:
        raise ValueError(f'Unexpected responses in {attitude_column}: {unexpected}')
    answered = responses.isin(VALID_ATTITUDES)
    agreed = responses.isin(AGREEMENT)
    row = {'Attitude (agreement)': attitude}
    for option in CHS_OPTIONS:
        group = chs.eq(option).fillna(False)
        n = int((group & agreed).sum())
        denominator = int((group & answered).sum())
        row[option] = f'{n} ({100 * n / denominator:.1f}%)' if denominator else f'{n} (—)'
    rows.append(row)

report = journal_table(
    data=pd.DataFrame(rows),
    title='Agreement With Wearable Attitudes by Overall Health Score Use',
    total_counts_only=True,
    note=(
        f'Analysis includes {len(df)} current wearable users. Q14 asks whether '
        'respondents use overall health scores from their device. Agreement combines '
        '“somewhat agree” and “strongly agree” for each Q15 statement. Cells are '
        'n (% of respondents in the Q14 category who answered that statement); '
        'missing Q14 or Q15 responses are excluded from the relevant cell. '
        'The right Total counts agreeing respondents per statement. The bottom '
        'Total counts agreements across statements, not unique respondents.'
    ),
)

# Q15 is ordinal. Compare the full five-point response across the five
# mutually exclusive Q14 groups, once per attitude statement.
likert = {
    'Strongly disagree': 1,
    'Somewhat disagree': 2,
    'Neither agree nor disagree': 3,
    'Somewhat agree': 4,
    'Strongly agree': 5,
}
tests = []
for attitude_column, attitude in ATTITUDES.items():
    scores = df[attitude_column].astype('string').str.strip().map(likert)
    groups = [scores[chs.eq(option).fillna(False)].dropna().to_numpy(dtype=float)
              for option in CHS_OPTIONS]
    if any(len(group) < 5 for group in groups):
        raise ValueError(f'Too few Q15 responses for a Q14 group in {attitude_column}')
    result = kruskal(*groups)
    tests.append({'Attitude': attitude, 'H': result.statistic, 'p': result.pvalue})

adjusted = multipletests([row['p'] for row in tests], method='fdr_bh')[1]

def format_p(value):
    return '<0.0001' if value < 0.0001 else f'{value:.4f}'

for row, adjusted_p in zip(tests, adjusted):
    row['H'] = f"{row['H']:.2f}"
    row['p'] = format_p(row['p'])
    row['Adjusted p'] = format_p(adjusted_p)

journal_table(
    data=pd.DataFrame(tests),
    title='Q14 Health Score Use and Q15 Attitudes: Group Comparisons',
    word_document=report.attrs['word_output_path'],
    note=(
        'Each row is a separate Kruskal–Wallis test of the full five-point Q15 '
        'response across the five mutually exclusive Q14 categories. H is the '
        'test statistic; adjusted p uses Benjamini–Hochberg false discovery rate '
        'correction across eight tests. These are exploratory overall tests; '
        'a significant result does not identify which groups differ.'
    ),
)
