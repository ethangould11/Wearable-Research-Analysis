"""Question 4: reviewed respondent-level analysis; see Data/CLEANING_SUMMARY.md."""
from pathlib import Path
import os
import sys

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from Analysis.review_q2_q4 import run

if __name__ == '__main__':
    run(questions=(4,))
