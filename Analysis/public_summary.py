"""Limited pooled feature summaries; not a general anonymization tool."""

FEATURES_FOR_OVERVIEW = {
    'Q12_1': 'Step tracking', 'Q12_2': 'Heart monitoring',
    'Q12_4': 'Workout/fitness tracking', 'Q12_3': 'Sleep tracking',
}


def feature_bands(bundle):
    """Return only broad bands among current users with usable Q12 answers."""
    columns = [key for key in bundle['expected'] if key.startswith('Q12_')]
    rows = bundle['current']
    valid = rows[columns].apply(
        lambda column: column.eq('') | column.eq(bundle['expected'][column.name])
    ).all(axis=1)
    rows = rows.loc[valid & rows[columns].ne('').any(axis=1)]
    if len(rows) < 50:
        raise ValueError('Insufficient pooled responses for the public overview.')
    output = []
    for column, label in FEATURES_FOR_OVERVIEW.items():
        count = int(rows[column].eq(bundle['expected'][column]).sum())
        if count < 20 or len(rows) - count < 10:
            raise ValueError('Public feature overview requires disclosure review.')
        lower = (100 * count // len(rows) // 10) * 10
        output.append({'feature': label, 'percentage_band': f'{lower}% to <{lower + 10}%'})
    return output
