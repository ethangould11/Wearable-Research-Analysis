"""Run every wearable-research analysis and create Word reports in Output/."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys


PROJECT_DIR = Path(__file__).resolve().parent
QUESTION_DIR = PROJECT_DIR / "Questions"
OUTPUT_DIR = PROJECT_DIR / "Output"


def reports_for(script: Path) -> set[Path]:
    """Find the base document and numbered copies for one question."""
    name = script.stem
    return {path for path in OUTPUT_DIR.glob(f"{name}*.docx")
            if path.name == f"{name}.docx"
            or (path.name.startswith(f"{name} (")
                and path.name.removeprefix(f"{name} (").removesuffix(").docx").isdigit())}


def run_reports() -> None:
    """Run each question with this Python interpreter and validate its output."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    scripts = sorted(QUESTION_DIR.glob("*.py"), key=lambda path: path.name)
    if not scripts:
        raise FileNotFoundError(f"No Python question files found in {QUESTION_DIR}")

    created_reports = []
    for script_path in scripts:
        before = {path: (path.stat().st_mtime_ns, path.stat().st_size)
                  for path in reports_for(script_path)}
        print(f"\nRunning {script_path.name}...", flush=True)
        subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            cwd=PROJECT_DIR,
        )
        changed_reports = {path for path in reports_for(script_path)
                           if before.get(path) != (path.stat().st_mtime_ns, path.stat().st_size)}
        if len(changed_reports) != 1:
            raise RuntimeError(
                f"Expected one created or updated Word report from {script_path.name}; "
                f"found {len(changed_reports)}."
            )
        created_reports.extend(changed_reports)

    print("\nReports created in:")
    for report in created_reports:
        print(f"  {report}")


if __name__ == "__main__":
    try:
        run_reports()
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"Report generation stopped while running: {error.cmd[-1]}") from error
