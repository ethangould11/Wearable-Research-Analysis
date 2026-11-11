"""Reproducible respondent-level cleaning, analysis and reporting for Q2–Q4.

Run from any directory: python3 Analysis/review_q2_q4.py
The raw CSV is read only. Audit and derived data are written under Data/.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import os
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE = Path(os.environ.get('WEARABLE_SURVEY_CSV', 'private/survey.csv'))
DATA = ROOT / 'Data'
BRANDS = dict(zip([f'Q9_{i}' for i in range(1, 8)],
                 ['Apple Watch', 'Fitbit/Google', 'Garmin', 'Samsung Galaxy Watch',
                  'Oura Ring', 'WHOOP', 'Other']))
FEATURES = dict(zip([f'Q12_{i}' for i in range(1, 11)],
                   ['Step tracking', 'Heart monitoring', 'Sleep tracking',
                    'Workout/fitness tracking', 'Calorie tracking', 'Stress monitoring',
                    'Composite Health Score', 'Notifications', 'Mental health features', 'Other feature']))
ABILITIES = {
    'Beginner/not very athletic': 'Beginner',
    'Recreational/somewhat athletic': 'Recreational',
    'Competent/moderately athletic': 'Competent',
    'Advanced/Very athletic': 'Advanced',
    'Elite/Highly trained/competitive athlete': 'Elite',
}
GENDERS = ['Woman', 'Man', 'Non-binary', 'Another identity (please specify)', 'Prefer not to say']
STEMS = {2: '2 Wearable Device vs. Athletic', 3: '3 Wearable Device vs. Gender',
         4: '4 Wearable Device vs Feature Usage'}
TITLES = {2: 'Wearable Device Brands by Self-Rated Athletic Ability',
          3: 'Wearable Device Brands by Self-Reported Gender',
          4: 'Frequently Used Wearable Features by Wearable Brand'}


def clean_source(source=SOURCE):
    """Content-based artifact detection; question nonresponse is not imputed."""
    source = Path(source)
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    # Do not let pandas turn literal strings such as NA into missing responses.
    raw = pd.read_csv(source, dtype=str, keep_default_na=False, skip_blank_lines=False)
    required = ['ResponseId', 'Status', 'Finished', 'Q3', 'Q4', 'Q8', *BRANDS, *FEATURES]
    if set(required) - set(raw):
        raise ValueError(f'Missing source columns: {set(required) - set(raw)}')
    frame = raw.map(lambda value: str(value).strip())
    frame.insert(0, 'source_record', np.arange(1, len(frame) + 1))
    descriptions = frame.loc[frame.ResponseId.eq('Response ID') & frame.Status.eq('Response Type')]
    if len(descriptions) != 1:
        raise ValueError('Expected one Qualtrics descriptive header; source schema needs review.')
    codebook = descriptions.iloc[0]
    expected = {column: codebook[column].rsplit(' - ', 1)[-1] for column in [*BRANDS, *FEATURES]}
    audit, removed = [], []

    def drop(reason, mask, kind='cleaning'):
        nonlocal frame
        selected = frame.loc[mask]
        audit.append({'stage': kind, 'reason': reason, 'records_removed': len(selected)})
        removed.extend({'source_record': int(row.source_record), 'ResponseId': row.ResponseId,
                        'stage': kind, 'reason': reason} for row in selected.itertuples())
        frame = frame.loc[~mask].copy()

    drop('Blank rows', frame.drop(columns='source_record').eq('').all(axis=1))
    drop('Qualtrics descriptive metadata', frame.ResponseId.eq('Response ID') & frame.Status.eq('Response Type'))
    drop('Qualtrics import metadata', frame.ResponseId.str.contains('"ImportId"', regex=False)
         & frame.Status.str.contains('"ImportId"', regex=False))
    drop('Repeated CSV column headers', frame.ResponseId.eq('ResponseId') & frame.Status.eq('Status'))
    survey_columns = [c for c in raw if c.startswith('Q')]
    drop('Nonresponse formatting or footnote rows', frame.ResponseId.eq('')
         & frame[survey_columns].eq('').all(axis=1) & frame.Status.eq(''))
    drop('Exact duplicate rows (keep first)', frame.duplicated(subset=list(raw.columns)))
    duplicate_ids = frame.ResponseId.ne('') & frame.ResponseId.duplicated(keep=False)
    if duplicate_ids.any():
        raise ValueError('Conflicting repeated ResponseIds require review; existing reports were not replaced.')
    if (~frame.ResponseId.str.fullmatch(r'R_[A-Za-z0-9]+')).any():
        raise ValueError('Missing or malformed response IDs require review; no identities were inferred.')
    drop('Survey Preview (test records)', frame.Status.eq('Survey Preview'), 'scope')
    clean = frame.copy()
    drop('Q8 No (not a current wearable user)', frame.Q8.eq('No'), 'scope')
    drop('Q8 missing (eligibility unknown)', frame.Q8.eq(''), 'scope')
    drop('Q8 invalid (eligibility unknown)', ~frame.Q8.eq('Yes'), 'scope')
    current = frame.copy()

    # All checked cells must match the option label in this export's metadata.
    valid_brand = current[list(BRANDS)].apply(lambda col: col.eq('') | col.eq(expected[col.name])).all(axis=1)
    valid_feature = current[list(FEATURES)].apply(lambda col: col.eq('') | col.eq(expected[col.name])).all(axis=1)
    brand_answered = current[list(BRANDS)].ne('').any(axis=1)
    feature_answered = current[list(FEATURES)].ne('').any(axis=1)
    usable_brand = valid_brand & brand_answered
    usable_feature = valid_feature & feature_answered
    usable = {2: usable_brand & current.Q4.isin(ABILITIES),
              3: usable_brand & current.Q3.isin(GENDERS),
              4: usable_brand & usable_feature}
    quality = []
    for column, values in [('Q3', GENDERS), ('Q4', list(ABILITIES)), ('Q8', ['Yes', 'No'])]:
        for scope, rows in [('cleaned respondents', clean), ('current wearable users', current)]:
            quality.append({'scope': scope, 'variable': column, 'missing': int(rows[column].eq('').sum()),
                            'invalid': int((rows[column].ne('') & ~rows[column].isin(values)).sum())})
    for columns, name in [(BRANDS, 'Q9'), (FEATURES, 'Q12')]:
        for scope, rows in [('cleaned respondents', clean), ('current wearable users', current)]:
            invalid = rows[list(columns)].apply(lambda col: col.ne('') & col.ne(expected[col.name])).any(axis=1)
            quality.append({'scope': scope, 'variable': name, 'missing': int(rows[list(columns)].eq('').all(axis=1).sum()),
                            'invalid': int(invalid.sum())})
    exclusions = []
    for number in (2, 3, 4):
        for idx, row in current.loc[~usable[number]].iterrows():
            reasons = []
            if not valid_brand.loc[idx]: reasons.append('invalid Q9 option value')
            if not brand_answered.loc[idx]: reasons.append('Q9 unanswered')
            if number in (2, 3):
                column, allowed = ('Q4', ABILITIES) if number == 2 else ('Q3', GENDERS)
                if row[column] == '': reasons.append(f'{column} missing')
                elif row[column] not in allowed: reasons.append(f'{column} invalid')
            if number == 4:
                if not valid_feature.loc[idx]: reasons.append('invalid Q12 option value')
                if not feature_answered.loc[idx]: reasons.append('Q12 unanswered')
            exclusions.append({'question': number, 'ResponseId': row.ResponseId,
                               'source_record': int(row.source_record), 'reasons': '; '.join(reasons)})
    profiles = {
        'raw_data_records_including_metadata': len(raw), 'cleaned_respondents': len(clean),
        'current_wearable_users': len(current), 'duplicate_response_ids_after_exact_dedup': 0,
        'repeated_nonblank_IP_rows': int(clean.loc[clean.IPAddress.ne(''), 'IPAddress'].duplicated(keep=False).sum()),
        'unfinished_current_users_retained': int(current.Finished.eq('False').sum()),
        'valid_other_brand_responses_retained': int(current.Q9_7.eq(expected['Q9_7']).sum()),
        'valid_other_feature_responses_retained': int(current.Q12_10.eq(expected['Q12_10']).sum()),
        'other_brand_text_without_selection': int((current.Q9_7.eq('') & current.Q9_7_TEXT.ne('')).sum()),
        'other_feature_text_without_selection': int((current.Q12_10.eq('') & current.Q12_10_TEXT.ne('')).sum()),
    }
    return dict(source=str(source), sha256=fingerprint, expected=expected, clean=clean,
                current=current, usable=usable, audit=audit, removed=removed,
                quality=quality, exclusions=exclusions, profile=profiles)


def calculate(bundle, number):
    rows = bundle['current'].loc[bundle['usable'][number]].copy()
    if rows.empty:
        raise ValueError(f'Q{number}: no usable paired answers; existing output left unchanged.')
    if number in (2, 3):
        variable = 'Q4' if number == 2 else 'Q3'
        groups = list(ABILITIES) if number == 2 else [g for g in GENDERS if rows.Q3.eq(g).any()]
        labels = [ABILITIES[g] for g in groups] if number == 2 else groups
        denominators = pd.Series({label: int(rows[variable].eq(group).sum()) for group, label in zip(groups, labels)})
        counts = pd.DataFrame({label: [int((rows[variable].eq(group) & rows[col].eq(bundle['expected'][col])).sum())
                                     for col in BRANDS] for group, label in zip(groups, labels)}, index=list(BRANDS.values()))
    else:
        denominators = pd.Series({brand: int(rows[col].eq(bundle['expected'][col]).sum()) for col, brand in BRANDS.items()})
        counts = pd.DataFrame({brand: [int((rows[bcol].eq(bundle['expected'][bcol]) & rows[fcol].eq(bundle['expected'][fcol])).sum())
                                     for fcol in FEATURES] for bcol, brand in BRANDS.items()}, index=list(FEATURES.values()))
    summary = pd.DataFrame([{'category': group, 'series': series, 'count': int(counts.loc[series, group]),
                             'group_respondents': int(denominators[group])}
                            for group in counts for series in counts.index])
    return dict(question=number, rows=rows, counts=counts, denominators=denominators,
                summary=summary)


def verify_from_raw(bundle, result):
    """Independent record-loop reconciliation against raw CSV (not formatted tables)."""
    with open(bundle['source'], newline='', encoding='utf-8-sig') as handle:
        original = list(csv.DictReader(handle))
    lookup = {row['ResponseId'].strip(): {k: (v or '').strip() for k, v in row.items()} for row in original}
    members = set(result['rows'].ResponseId)
    assert len(members) == len(result['rows'])
    assert members <= set(lookup)
    for value in result['summary'].itertuples():
        numerator = denominator = 0
        for identifier in members:
            record = lookup[identifier]
            if result['question'] == 2:
                group = ABILITIES[record['Q4']] == value.category
                column = next(k for k, v in BRANDS.items() if v == value.series)
            elif result['question'] == 3:
                group = record['Q3'] == value.category
                column = next(k for k, v in BRANDS.items() if v == value.series)
            else:
                brand_column = next(k for k, v in BRANDS.items() if v == value.category)
                group = record[brand_column] == bundle['expected'][brand_column]
                column = next(k for k, v in FEATURES.items() if v == value.series)
            denominator += int(group)
            numerator += int(group and record[column] == bundle['expected'][column])
        assert (numerator, denominator) == (value.count, value.group_respondents)
        assert 0 <= numerator <= denominator
    if result['question'] == 2:
        assert list(result['counts']) == list(ABILITIES.values())
    assert hashlib.sha256(Path(bundle['source']).read_bytes()).hexdigest() == bundle['sha256']
    return {'question': result['question'], 'cells_reconciled_to_raw': len(result['summary']),
            'unique_usable_respondents': len(members), 'raw_hash_unchanged': True,
            'counts_valid': True}


def save_data(bundle, results):
    (DATA / 'derived').mkdir(parents=True, exist_ok=True)
    # Save analysis fields and lineage, without copying IP addresses or contact fields.
    columns = ['source_record', 'ResponseId', 'Status', 'Finished', 'Q3', 'Q4', 'Q8', *BRANDS, *FEATURES,
               'Q3_4_TEXT', 'Q9_7_TEXT', 'Q12_10_TEXT']
    bundle['clean'][columns].to_csv(DATA / 'cleaned_respondents.csv', index=False)
    bundle['current'][columns].to_csv(DATA / 'current_wearable_users.csv', index=False)
    pd.DataFrame(bundle['audit']).to_csv(DATA / 'cleaning_counts.csv', index=False)
    pd.DataFrame(bundle['removed'], columns=['source_record', 'ResponseId', 'stage', 'reason']).to_csv(DATA / 'excluded_records.csv', index=False)
    pd.DataFrame(bundle['quality']).to_csv(DATA / 'missing_invalid_values.csv', index=False)
    pd.DataFrame(bundle['exclusions'], columns=['question', 'ResponseId', 'source_record', 'reasons']).to_csv(DATA / 'question_exclusions.csv', index=False)
    for result in results:
        prefix = DATA / 'derived' / f"q{result['question']}"
        result['rows'][columns].to_csv(f'{prefix}_respondents.csv', index=False)
        result['summary'].to_csv(f'{prefix}_summary.csv', index=False)
        result['counts'].to_csv(f'{prefix}_counts.csv', index_label='series')
        if result['question'] == 4:
            brand_totals = result['counts'].sum(axis=0)
            shares = result['counts'].div(brand_totals.replace(0, np.nan), axis=1) * 100
            brand_mix = pd.DataFrame([
                {'wearable_brand': brand, 'feature': feature,
                 'feature_selection_count': int(result['counts'].loc[feature, brand]),
                 'total_brand_feature_selections': int(brand_totals[brand]),
                 'share_of_brand_feature_selections_pct': shares.loc[feature, brand]}
                for brand in result['counts'].columns for feature in result['counts'].index
            ])
            brand_mix.to_csv(DATA / 'derived' / 'q4_brand_feature_shares.csv', index=False)
    codebook = {column: {'export_value': bundle['expected'][column], 'display_label': label}
                for column, label in {**BRANDS, **FEATURES}.items()}
    (DATA / 'codebook.json').write_text(json.dumps({'options': codebook, 'ability_labels': ABILITIES}, indent=2) + '\n')
    checks = [verify_from_raw(bundle, result) for result in results]
    (DATA / 'validation.json').write_text(json.dumps({'raw_sha256': bundle['sha256'], 'profile': bundle['profile'],
                                                    'checks': checks}, indent=2) + '\n')
    lines = ['# Questions 2–4 cleaning and validation', '',
             'Source: `private survey CSV` (unchanged). Unit: one Qualtrics ResponseId.',
             'Input integrity is checked locally.', '',
             '## Rules and removed records', '',
             'Whitespace is trimmed; empty cells remain empty. Removal counts are sequential and mutually exclusive.',
             'Scope exclusions are not invalid respondents. All retained real respondents remain in cleaned_respondents.csv.', '']
    lines += [f"- {r['stage']}: {r['reason']}: **{r['records_removed']}**." for r in bundle['audit']]
    lines += ['', 'Unfinished surveys are retained when the relevant paired answers are usable. Valid Other options and free text are retained.',
              'Checkbox values must exactly match the option labels in the source metadata. Blank options mean unchecked only when the question has at least one valid selection.',
              'An entirely blank multi-select question is missing, not a response of none. No missing value is imputed.',
              'Invalid answers exclude only the affected question; they remain in the cleaned file and quality audit.',
              'Exact duplicate rows keep the first occurrence. Conflicting duplicate IDs or malformed IDs stop regeneration for review.',
              'ResponseId uniqueness cannot prove person-level uniqueness. Repeated nonblank IP addresses are flagged, never automatically deduplicated.', '',
              '## Question-specific usable sample sizes', '']
    for result in results:
        n = result['question']
        definition = ('Respondents with a valid group answer and usable Q9 brand selections in that group.' if n in (2, 3)
                      else 'Respondents selecting the brand who also provided usable Q12 feature selections.')
        lines += [f"- Q{n}: {len(result['rows'])} usable respondents; {len(bundle['current']) - len(result['rows'])} excluded from this question. {definition}",
                  '  Group sample sizes: ' + '; '.join(f'{k} n={v}' for k, v in result['denominators'].items()) + '.']
    lines += ['', 'Question exclusion reasons in question_exclusions.csv may overlap within a respondent. Use unique records for exclusion totals.',
              'Counts are recalculated from respondent rows. Every summary cell is independently reconciled to the original CSV using a record loop.',
              'Tables show integer counts. Q2–Q3 charts show counts; Q4 also has a 100% stacked chart. Its denominator is the sum of counted feature selections for that wearable brand, so each brand bar sums to 100%. These are shares of selections, not respondents.',
              'Group sample sizes are shown under the bars and in the corresponding table headers.', '',
              '## Findings and limitations', '']
    lines += [f'- {k.replace("_", " ")}: {v}.' for k, v in bundle['profile'].items()]
    lines += ['',
              'Q4 features are respondent-level selections and cannot be attributed to a specific device for people selecting multiple brands.',
              'Full survey choice definitions for unobserved gender values are not supplied; unfamiliar future labels are flagged for review, not recoded.',
              'These are descriptive counts. Group-size differences affect bar heights; counts do not correct for sampling bias.', '',
              'Reproduce: `python3 Analysis/review_q2_q4.py`. Validate/recalculate data only: `python3 Analysis/review_q2_q4.py --data-only`.', '']
    (DATA / 'CLEANING_SUMMARY.md').write_text('\n'.join(lines))


def create_report(bundle, result):
    from Output.JournalTable import journal_table
    from Output.JournalComparisonChart import journal_comparison_chart
    number = result['question']
    header_map = {group: f'{group}\n(n={denominator})' for group, denominator in result['denominators'].items()}
    counts = result['counts'].rename(columns=header_map)
    counts.index.name = 'Wearable device' if number in (2, 3) else 'Frequently used feature'
    if number in (2, 3):
        note = ('Cells show respondent counts with usable group and brand answers. '
                'Multiple wearable brands could be selected. Stack heights and totals count brand selections, '
                'not unique respondents. ')
    else:
        note = ('Cells show counts of respondents selecting both the brand and feature, among those with usable paired answers. '
                'Multiple brands and features could be selected. Stack heights and totals count selections, '
                'not unique respondents. Features reported by multi-brand users cannot be attributed to a specific device. ')
    note += (f"Of {len(bundle['current'])} current wearable users, {len(result['rows'])} provided usable paired answers. "
             'Group sample sizes are shown in the headers. Valid Other responses are retained.')
    table = journal_table(data=counts.reset_index(), title=TITLES[number],
                          decimals=0, total_counts_only=True, note=note,
                          source_file=ROOT / 'Questions' / f'{STEMS[number]}.py', overwrite=True)
    document_path = table.attrs['word_output_path']
    if number == 4:
        journal_comparison_chart(result, title=TITLES[number], note=note, word_document=document_path,
                                 q4_orientation='brand')
        journal_comparison_chart(result, title=TITLES[number], note=note, word_document=document_path,
                                 q4_orientation='brand', q4_percent=True)
    else:
        journal_comparison_chart(result, title=TITLES[number], note=note, word_document=document_path)
    from docx import Document
    document = Document(document_path)
    assert len(document.tables) == 1 and len(document.inline_shapes) == (2 if number == 4 else 1)
    for row_number, series in enumerate(counts.index, 1):
        for column_number, group in enumerate(result['counts'].columns, 1):
            count = result['counts'].loc[series, group]
            expected = f'{count:,}'
            assert document.tables[0].cell(row_number, column_number).text == expected
    return str(document_path)


def run(questions=(2, 3, 4), data_only=False):
    bundle = clean_source()
    results = [calculate(bundle, number) for number in (2, 3, 4)]
    save_data(bundle, results)
    reports = [] if data_only else [create_report(bundle, result) for result in results if result['question'] in questions]
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == bundle['sha256']
    print('Data and validation saved:', DATA)
    return reports


if __name__ == '__main__':
    run(data_only='--data-only' in sys.argv)
