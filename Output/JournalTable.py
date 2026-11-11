"""Reusable journal-style tables with Word export for pandas analysis results."""

import re
from numbers import Integral
from collections.abc import Mapping, Sequence

import pandas as pd
from pathlib import Path
import os
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


def word_output_path_for_script(source_file, overwrite=False):
    """Return the next unused Word-report path for a question script."""
    output_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)
    name = Path(source_file).stem
    candidate = output_dir / f"{name}.docx"
    if overwrite or not candidate.exists():
        return candidate
    number = 2
    while candidate.exists():
        candidate = output_dir / f"{name} ({number}).docx"
        number += 1
    return candidate


def journal_table(
    data,
    title,
    columns=None,
    decimals=2,
    note=None,
    show_index=False,
    total_label="Total",
    word_document=None,
    percentage_denominators=None,
    total_counts_only=False,
    source_file=None,
    overwrite=False,
):
    """Render a journal-style table in the terminal and save a clean Word document.

    Every table receives a rightmost Total column and a bottom Total row.
    Pass a denominator, a mapping by column, or a list by row to display
    count values as n (%). Set ``total_counts_only`` when the totals are
    selections that should not be presented as participant percentages.
    """
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)

    table = data.copy()
    if columns:
        table = table.rename(columns=columns)

    if show_index:
        table = table.reset_index()

    if percentage_denominators is not None and "n" in table.columns:
        table = table.rename(columns={"n": "n (%)"})

    # Calculate totals before display formatting. A cell such as "6 (12.5%)"
    # contributes six selections, but percentages and statistical results do
    # not contribute to a total.
    count_cell = re.compile(r"^\s*(\d[\d,]*)\s*\([^)]*\)\s*$")
    non_additive_names = {"rank", "id", "year", "age", "percentage", "%", "p", "p-value"}

    def count_value(column, value):
        if str(column).strip().casefold() in non_additive_names:
            return None
        if isinstance(value, Integral) and not isinstance(value, bool):
            return int(value)
        if pd.isna(value):
            return None
        if column == "Total" and re.fullmatch(r"\d[\d,]*", str(value)):
            return int(str(value).replace(",", ""))
        match = count_cell.fullmatch(str(value))
        return int(match.group(1).replace(",", "")) if match else None

    # Some analyses already supply a participant-level Total selections column.
    # Move it to the right and use the shared heading instead of adding a
    # duplicate. Otherwise calculate each row's total from count cells.
    existing_total = next((name for name in ("Total", "Total selections")
                           if name in table.columns), None)
    if existing_total is not None:
        right_total = table.pop(existing_total)
        table["Total"] = right_total
    else:
        count_columns = list(table.columns[1:])
        row_totals = []
        for _, row in table.iterrows():
            counts = [count_value(column, row[column]) for column in count_columns]
            counts = [count for count in counts if count is not None]
            row_totals.append(sum(counts) if counts else pd.NA)
        table["Total"] = row_totals

    totals = {}
    for column in table.columns:
        counts = [count_value(column, value) for value in table[column]]
        counts = [count for count in counts if count is not None]
        totals[column] = sum(counts) if counts else "—"
    totals[table.columns[0]] = total_label

    if isinstance(percentage_denominators, Sequence) and not isinstance(
        percentage_denominators, (str, bytes)
    ) and len(percentage_denominators) != len(table):
        raise ValueError("Row denominators must match the number of data rows.")

    def denominator_for(column, row_index):
        source = percentage_denominators
        if isinstance(source, Mapping):
            return source.get(column, source.get("Total selections") if column == "Total" else None)
        if isinstance(source, Sequence) and not isinstance(source, (str, bytes)):
            return sum(source) if row_index == len(table) else source[row_index]
        return source

    def display_value(column, value, row_index):
        if pd.isna(value):
            return "—"
        count = count_value(column, value)
        if total_counts_only and count is not None and (
            column == "Total" or row_index == len(table)
        ):
            return f"{count:,}"
        denominator = denominator_for(column, row_index)
        if count is not None and percentage_denominators is not None and denominator is None:
            raise ValueError(f"Missing percentage denominator for count column: {column}")
        if count is not None and denominator is not None:
            if denominator < 0:
                raise ValueError("Percentage denominators must be nonnegative.")
            return f"{count:,} ({100 * count / denominator:.1f}%)" if denominator else f"{count:,} (—)"
        if isinstance(value, Integral) and not isinstance(value, bool):
            return f"{value:,}"
        if isinstance(value, float):
            return f"{value:,.{decimals}f}"
        return str(value)

    display_rows = [
        {column: display_value(column, row[column], row_index) for column in table.columns}
        for row_index, (_, row) in enumerate(table.iterrows())
    ]
    display_rows.append(
        {column: display_value(column, totals[column], len(table)) for column in table.columns}
    )
    table = pd.DataFrame(display_rows, columns=table.columns)

    headers = [str(col) for col in table.columns]
    rows = [["—" if pd.isna(value) else str(value) for value in row]
            for row in table.itertuples(index=False, name=None)]
    widths = [max(len(header), *(len(row[i]) for row in rows))
              for i, header in enumerate(headers)]

    def render_row(values):
        return "  ".join(str(value).ljust(widths[i]) for i, value in enumerate(values))

    print(f"\n{title}")
    print(render_row(headers))
    print("  ".join("─" * width for width in widths))
    for row in rows:
        print(render_row(row))
    if note:
        print(f"\nNote. {note}")
    print()

    if word_document is None:
        import __main__
        source_file = source_file or getattr(__main__, "__file__", None)
        if not source_file:
            raise RuntimeError("Run the analysis from a Python script to name the output document.")
        output_path = word_output_path_for_script(source_file, overwrite=overwrite)
        document = Document()
    else:
        output_path = Path(word_document)
        if not output_path.is_file():
            raise FileNotFoundError(f"Word report to append to does not exist: {output_path}")
        document = Document(output_path)

    section = document.sections[0]
    if len(headers) > 5:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = section.page_height, section.page_width
        section.left_margin = section.right_margin = Inches(0.45)
    else:
        section.left_margin = section.right_margin = Inches(0.7)
    section.top_margin = section.bottom_margin = Inches(0.65)

    title_paragraph = document.add_paragraph()
    title_paragraph.paragraph_format.space_after = Pt(6)
    title_run = title_paragraph.add_run(title)
    title_run.bold = True
    title_run.font.name = "Arial"
    title_run.font.size = Pt(11)

    word_table = document.add_table(rows=1, cols=len(headers))
    word_table.style = "Table Grid"
    word_table.autofit = True

    def shade(cell, fill):
        properties = cell._tc.get_or_add_tcPr()
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), fill)
        properties.append(shading)

    def format_cell(cell, *, header=False, total=False):
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cell.margin_top = cell.margin_bottom = 70
        cell.margin_left = cell.margin_right = 90
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(0)
            for run in paragraph.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5 if len(headers) > 5 else 9.5)
                if header:
                    run.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                elif total:
                    run.bold = True
        if header:
            shade(cell, "1F4E78")
        elif total:
            shade(cell, "D9EAF7")

    for i, header in enumerate(headers):
        word_table.rows[0].cells[i].text = header
        format_cell(word_table.rows[0].cells[i], header=True)
    for row_index, row in enumerate(rows):
        cells = word_table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = value
        is_total_row = row_index == len(rows) - 1
        for i, cell in enumerate(cells):
            format_cell(cell, total=is_total_row or i == len(headers) - 1)

    if note:
        note_paragraph = document.add_paragraph()
        note_paragraph.paragraph_format.space_before = Pt(6)
        note_run = note_paragraph.add_run(f"Note. {note}")
        note_run.font.name = "Arial"
        note_run.font.size = Pt(9)
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            if run.font.size is None:
                run.font.size = Pt(10)

    document.save(output_path)
    print(f"Word table saved: {output_path}")
    table.attrs["word_output_path"] = output_path
    return table
