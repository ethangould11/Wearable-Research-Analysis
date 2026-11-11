# Results overview

[Project overview](README.md) · [Research methods](docs/METHODS.md) · [Privacy policy](PRIVACY.md)

## Everyday activity and heart monitoring are prominent uses

In the pooled feature responses, step tracking, heart monitoring, and
workout/fitness tracking were each reported by roughly three quarters of
respondents with usable feature answers. Sleep tracking was reported by
just under half. These findings describe reported use within the survey,
not device effectiveness or the wider population.

### Selected feature-use findings

| Frequently used feature | Share of usable feature respondents, broad range |
| --- | :---: |
| Step tracking | 70% to <80% |
| Heart monitoring | 70% to <80% |
| Workout/fitness tracking | 70% to <80% |
| Sleep tracking | 40% to <50% |

**Denominator:** current wearable users who provided at least one valid feature
selection, pooled across all brands. Each respondent contributes once to each
selected feature. Missing or invalid feature questions are excluded. People
could select multiple features, so these rows should not be stacked or summed
as a 100% whole.

**Precision:** ranges are ten-percentage-point bands containing the calculated
percentage. For example, “70% to <80%” includes 70% and excludes 80%. These are
disclosure-limiting ranges, not uncertainty intervals. Exact counts and sample
sizes are intentionally withheld from the public overview.

## What the broader project investigates

| Theme | Analysis | Public presentation |
| --- | --- | --- |
| Device choices | Q1: brand distribution | Question and method available; detailed results remain private |
| Who uses each brand | Q2–Q3: athletic ability and gender | Within-brand 100% charts generated locally; subgroup results withheld |
| What devices are used for | Q4: feature selections by brand | Pooled feature ranges above; detailed brand combinations withheld |
| Attitudes toward wearable feedback | Q5–Q6: brand and feature comparisons | Methods and code available; detailed comparisons remain private |
| Composite health score engagement | Q7–Q8: attitudes and wearing frequency | Methods and code available; detailed comparisons remain private |

## Reading the local 100% figures

Q2 and Q3 show the ability and gender composition of respondents within each
wearable brand. Their denominator is usable respondents selecting that brand.
Q4 instead shows each feature’s share of all feature selections within a brand.
The vertical bars reach 100% in each case, but the units differ. A larger Q4
segment does not directly mean that a larger proportion of people use that feature.

## Interpretation and limits

The selected pooled findings show that activity and heart-monitoring functions
are commonly reported in this sample. They support further research into how
people engage with wearable feedback. They do not establish that a device
improves health, that one brand performs better, or that usage causes an attitude.

The four features are selected for a concise overview; this is not a complete
ranking of every survey option. Responses are self-reported, missing answers
affect eligibility, and the sampling frame is not established here. Fine-grained
brand and demographic comparisons can expose small groups and remain private.

## Evidence and reproducibility

The ranges are calculated in Python from respondent-level answers and checked
independently against the private input. The public calculation is defined in
[public_summary.py](Analysis/public_summary.py); [research methods](docs/METHODS.md)
describe cleaning and denominator choices. The private input, precise audit
results, and detailed report images are excluded from this repository.
