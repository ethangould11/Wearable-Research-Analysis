# Publication boundary

This initial publication contains source code, method descriptions and broad
category definitions. It includes no observed results or participant data.

Excluded material includes raw and cleaned datasets, respondent subsets,
response identifiers, IP addresses, contact information, dates, location data,
free-text answers, input-file fingerprints, local machine paths, audit outputs,
small-group counts, detailed cross-tabulations, generated images, Word reports,
PDFs, archives, editor settings and credentials. No source-file link is provided.

Removing names alone does not make respondent data anonymous. Detailed counts
and cross-tabulations can expose small groups, so they are excluded from this
release as well. No claim of a universal anonymity guarantee is made; the
publication boundary avoids releasing study observations entirely.

The default-deny `.gitignore` admits only the documented code and documentation
paths. Do not use `git add --force` for data, outputs or archives. Private input
and generated outputs must remain local. Before a future release, review the
exact tracked files and Git history, including hardcoded values in code and
documentation. Ignoring a file does not remove it from existing Git history.
