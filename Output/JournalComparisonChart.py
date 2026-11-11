"""Validated within-brand composition figures for Questions 2–4."""
from pathlib import Path
import os
import json
import os
import tempfile
import textwrap

cache_dir = Path(tempfile.gettempdir()) / 'wearable-research-matplotlib'
cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(cache_dir))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
from docx import Document
from docx.shared import Inches, Pt


def journal_comparison_chart(result, title, note, word_document, q4_orientation='brand',
                             q4_percent=False):
    """Build stacks from cleaned counts and verify their denominators and heights."""
    number = result['question']
    counts = result['counts']
    percent = number in (2, 3) or q4_percent
    if number in (2, 3):
        counts = counts.T
    if number == 4 and q4_orientation == 'feature':
        counts = counts.T
    raw_counts = counts.copy()
    if percent:
        denominators = counts.sum(axis=0)
        if (denominators <= 0).any():
            raise ValueError('Cannot calculate a composition for a brand with no usable answers.')
        counts = counts.div(denominators, axis=1).mul(100)
        np.testing.assert_allclose(counts.sum(axis=0).to_numpy(), np.full(len(denominators), 100.0))
    categories = list(counts.columns)
    series = list(counts.index)
    samples = result['denominators']
    assert np.all(counts.to_numpy() >= 0)
    if not percent:
        assert np.all(counts.to_numpy() == counts.to_numpy().astype(int))
    fig, ax = plt.subplots(figsize=(14, 8))
    labels = []
    for group in categories:
        if number == 4 and q4_orientation == 'feature':
            sample_size = len(result['rows'])
        elif number == 4:
            sample_size = int(samples[group])
        else:
            sample_size = int(raw_counts[group].sum())
        wrap = 18 if number == 4 and q4_orientation == 'feature' else (20 if number == 4 else (24 if number == 3 else 14))
        if percent:
            sample_size = int(raw_counts[group].sum())
            sample_label = f'(n={sample_size})'
        else:
            sample_label = f'(n={sample_size})'
        labels.append(f'{textwrap.fill(str(group), wrap)}\n{sample_label}')
    positions = np.arange(len(categories))
    bottoms = np.zeros(len(categories))
    palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
               '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    for index, label in enumerate(series):
        values = counts.loc[label].to_numpy(dtype=float if percent else int)
        bars = ax.bar(positions, values, bottom=bottoms, width=0.68,
                      color=palette[index], edgecolor='white', linewidth=0.4, label=label)
        np.testing.assert_allclose([bar.get_height() for bar in bars], values)
        np.testing.assert_allclose([bar.get_y() for bar in bars], bottoms)
        bottoms += values
    if percent:
        np.testing.assert_allclose(bottoms, np.full(len(categories), 100.0))
    else:
        np.testing.assert_allclose(bottoms, counts.sum(axis=0))
    for x, total in enumerate(bottoms):
        total_label = '100%' if percent else str(int(total))
        ax.annotate(total_label, (x, total), xytext=(0, 4),
                    textcoords='offset points', ha='center', fontsize=9)
    ax.set_xticks(positions, labels)
    ax.set_ylim(0, 105 if percent else max(1, float(bottoms.max()) * 1.12))
    if percent:
        ax.set_yticks(range(0, 101, 20), [f'{v}%' for v in range(0, 101, 20)])
    else:
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylabel('Share of brand feature selections (%)' if number == 4 and q4_percent else
                  ('Brand selections by feature (count)' if q4_orientation == 'feature' else 'Feature selections by brand (count)')
                  if number == 4 else 'Respondents within wearable brand (%)')
    ax.set_xlabel(('Frequently used feature' if q4_orientation == 'feature' else 'Wearable brand') if number == 4 else
                  'Wearable brand')
    ax.set_axisbelow(True)
    ax.grid(axis='y', alpha=0.18)
    ax.spines[['top', 'right']].set_visible(False)
    if number == 4:
        ax.legend(title='Wearable brand' if q4_orientation == 'feature' else 'Frequently used feature',
                  bbox_to_anchor=(1.01, 1), loc='upper left', frameon=False, fontsize=8)
    else:
        ax.legend(title='Self-rated athletic ability' if number == 2 else 'Self-reported gender',
                  bbox_to_anchor=(1.01, 1), loc='upper left', frameon=False, fontsize=9)
    ax.set_title(title, loc='left', fontsize=13, fontweight='bold', pad=16)
    chart_note = ('n = respondents with usable paired answers. Multiple selections were allowed. '
                  'Numbers above bars are selection totals, not unique respondents.')
    if number == 4 and q4_percent:
        chart_note = ('Each bar is 100% of that brand’s counted feature selections. Segments show each feature’s share '
                      'of that brand’s feature selections; n is the denominator in feature selections, not respondents. '
                      'Features and brands could be selected multiple times across respondents; features cannot be '
                      'attributed to a single device for multi-brand users.')
    elif number == 4:
        chart_note += ' Features cannot be attributed to a particular device for multi-brand users.'
    else:
        chart_note = ('Each bar is 100% of respondents selecting that brand who provided a usable '
                      + ('athletic-ability' if number == 2 else 'gender')
                      + ' answer; n is that brand’s respondent denominator. Categories within a brand '
                      'are mutually exclusive. Multiple brands could be selected, so the same respondent '
                      'may appear in several bars. Small brand groups require caution; percentages do not remove sampling bias.')
    fig.text(0.08, 0.02, textwrap.fill(chart_note, 135), fontsize=9, va='bottom')
    if number == 4 and q4_orientation == 'feature':
        plt.setp(ax.get_xticklabels(), rotation=42, ha='right')
    fig.subplots_adjust(left=0.09, right=0.78, top=0.90, bottom=0.26)
    suffix = (('_Brand_Feature_Share' if q4_percent else f'_by_{q4_orientation}') if number == 4 else '_Brand_Composition')
    stem = (f'Q{number}_Brand_Composition_100pct' if number in (2, 3) else
            f'Q{number}_Feature_Share_Stacked{suffix}' if q4_percent else f'Q{number}_Counts_Stacked{suffix}')
    paths = [Path(__file__).parent / f'{stem}.{extension}'
             for extension in ('png', 'pdf')]
    for path in paths:
        fig.savefig(path, dpi=300, facecolor='white', bbox_inches='tight')
    assert [tick.get_text() for tick in ax.get_xticklabels()] == labels
    plt.close(fig)
    manifest = {'question': number, 'orientation': q4_orientation if number == 4 else 'brand',
                'type': ('100% stacked feature-selection shares' if number == 4 else '100% stacked respondent composition') if percent else 'vertical stacked counts',
                'categories': categories, 'series': series,
                'percentage_denominator_unit': ('feature selections' if number == 4 else 'respondents') if percent else None,
                'percentage_denominators': {str(group): int(raw_counts[group].sum()) for group in categories} if percent else None,
                'group_sample_sizes': {str(group): int(raw_counts[group].sum()) for group in categories} if number in (2, 3) else
                                      {str(group): int(samples[group]) for group in categories} if q4_orientation == 'brand'
                                      else ({str(group): len(result['rows']) for group in categories}
                                            if number == 4 else {k: int(v) for k, v in samples.items()}),
                'rendered_counts_and_stack_totals_verified': True, 'axis_labels_verified': True}
    manifest_path = Path(__file__).parents[1] / 'Data' / 'derived' / f'q{number}_chart_validation{suffix}.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')

    document = Document(word_document)
    document.add_page_break()
    caption = document.add_paragraph(style='Caption')
    caption.paragraph_format.keep_with_next = True
    view = (' (within-brand respondent composition)' if number in (2, 3) else
            ' (share of brand feature selections)' if number == 4 and q4_percent else
            (f' by {q4_orientation}' if number == 4 else ''))
    caption.add_run(f'Figure {number}{view}. {title}')
    section = document.sections[0]
    available_width = (section.page_width - section.left_margin - section.right_margin) / Inches(1)
    document.add_picture(str(paths[0]), width=Inches(min(available_width, 9.0)))
    paragraph = document.add_paragraph(f'Note. {chart_note}')
    for run in paragraph.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(9)
    document.save(word_document)
    print('Chart and table saved:', word_document)
    return paths
