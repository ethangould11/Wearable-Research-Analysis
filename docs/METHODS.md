# Research methods

[Project overview](../README.md) · [Public results](../RESULTS.md) · [Privacy policy](../PRIVACY.md)

## Design and scope

This repository analyzes self-reported wearable-device survey responses.
Eligibility for the wearable analyses requires reported current wearable use.
The unit is a survey response. Unique response identifiers support record
checks but cannot establish that each person answered only once.

No study dates, recruitment frame, response rate, or population weighting are
established by this repository. Findings apply to the analyzed responses;
representativeness should not be assumed.

## Cleaning and missingness

The reviewed Q2–Q4 pipeline trims whitespace, detects export metadata and
formatting artifacts, checks exact duplicate rows, and stops on conflicting
duplicate identifiers. Preview responses are excluded from the research scope.
Invalid eligibility or question answers are flagged. Valid Other selections
remain in the analysis. Unfinished responses remain eligible when the required
paired answers are usable.

Selected checkbox values must match the export metadata. Blank options count
as unselected only when the question has at least one valid selection. An
entirely blank checkbox question is missing. No answer is inferred or imputed.
Counts are independently reconciled to the input records; source integrity
is checked locally. Detailed audits remain private.

Questions 1 and 5–8 retain their separate existing processing. They have not
been standardized to every cleaning rule in the Q2–Q4 pipeline.

## Denominators and measures

| Analysis | Measure | Denominator or comparison |
| --- | --- | --- |
| Q1 | Brand-use percentage | Current wearable users; multiple brand selection is permitted |
| Q2 | Within-brand ability composition | Brand users with a usable ability answer |
| Q3 | Within-brand gender composition | Brand users with a usable gender answer |
| Q4 | Within-brand feature-selection composition | Sum of feature selections within the brand among usable paired answers |
| Q5 | Agreement percentage | Respondents selecting the brand who answered the attitude statement |
| Q6 | Likert means and feature-user comparisons | Available statement scores within feature-user and nonuser groups |
| Q7 | Agreement and ordinal group comparisons | Available statement answers within composite-score-use groups |
| Q8 | Within-frequency-group percentage | Respondents with usable score-use and wearing-frequency answers in that frequency group |
| Public feature overview | Pooled feature-use percentage, released as a range | Current users with a usable feature answer, across all brands |

Q2 and Q3 categories are mutually exclusive within each brand. They sum to
100% because each usable respondent has one category answer. Their count
tables follow the same brand and category order as the percentage figures.
Athletic ability follows Beginner, Recreational, Competent, Advanced, Elite.

Q4 allows multiple features. Its 100% chart describes the **composition of
feature selections**, not the proportion of people using each feature. Its
separate count view is retained in the local report. Pooled feature-use
percentages on the public results page answer a different question and can
sum above 100% across features.

## Statistical comparisons

Agreement combines somewhat agree and strongly agree in Q5 and Q7. Q6 uses
two-sided Mann–Whitney U comparisons and rank-biserial effect sizes. Q7 uses
Kruskal–Wallis comparisons across score-use categories. The scripts apply
Benjamini–Hochberg false-discovery-rate adjustment within their respective
families of performed comparisons. These are exploratory associations.

One limitation of the existing Q6 processing is that a blank feature cell is
treated as unselected, including when the whole feature question is blank.
Interpret its user-versus-nonuser comparisons with that limitation in mind.

## Public results release

Only four broad pooled feature-use summaries are released. Each percentage
is calculated from respondent rows and placed into a ten-percentage-point
band. Exact counts, denominators, brand breakdowns, demographic combinations,
and small-group results are withheld. The release method checks the size of
the pooled set and both selected and unselected groups before emitting a band.

These bands reduce precision and disclosure exposure; they are not confidence
intervals, differential privacy, or a formal guarantee of anonymity. The
method is inspectable in [public_summary.py](../Analysis/public_summary.py).

## Limitations

- Multiple brands create overlapping groups; bars are not independent samples.
- Reported features cannot be attributed to a specific device for multi-brand users.
- Small groups can produce extreme percentages from few responses.
- Missingness changes usable samples and question-specific denominators.
- Self-reports, eligibility filtering, and participation may introduce bias.
- Overall tests do not identify specific group differences or establish causation.

Detailed local findings should be interpreted alongside their question-specific
notes and sample sizes. GitHub intentionally presents a narrower view.
