# Publication boundary

This publication contains source code, methods, broad category definitions,
and four pooled feature-use percentage bands on `RESULTS.md`. These bands
describe observed overall usage while withholding exact counts, sample sizes,
brand breakdowns and demographic combinations. No participant data are included.

Excluded material includes raw and cleaned datasets, respondent subsets,
response identifiers, IP addresses, contact information, dates, location data,
free-text answers, input-file fingerprints, local machine paths, audit outputs,
small-group counts, detailed cross-tabulations, generated images, Word reports,
PDFs, archives, editor settings and credentials. No source-file link is provided.

Removing names alone does not make respondent data anonymous. Detailed counts
and cross-tabulations can expose small groups, so they are excluded from this
release as well. The pooled overview uses broad ten-percentage-point bands
and minimum underlying group-size checks. These measures reduce disclosure
exposure; they do not constitute a formal anonymity guarantee. Individual
records and detailed observations are never released.

The default-deny `.gitignore` admits only the documented code and documentation
paths. Do not use `git add --force` for data, outputs or archives. Private input
and generated outputs must remain local. Before a future release, review the
exact tracked files and Git history, including hardcoded values in code and
documentation. Ignoring a file does not remove it from existing Git history.
