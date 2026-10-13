# Source review and audit decisions

## Accepted sources

1. **ESPN's own public scoreboard API**, queried for each UTC date from 11 June to 19 July 2026. These responses supplied 104 unique completed World Cup matches, exact UTC kickoff timestamps, listed team order, venue country and final scores. The API URLs and each daily payload's SHA-256 are recorded in `data/sources/espn_download_audit.json`; the actual selected original event objects are retained in `espn_events.json`.
   - URL pattern: `https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=YYYYMMDD`
   - Example: [ESPN final-day feed](https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260719).
2. **Mart Jürisoo's international-results dataset**, pinned at Git commit `b7a3a8ee5d37780c6a03101c188658fd439e241d`. The downloaded CSV contains 49,945 results. It is the source for earlier-match features and corroborates the scores of all 104 target matches. The author documents final scores including extra time and excluding shootouts, and uses current successor team names for historical continuity. The source data is CC0; the original license and README are bundled.
   - [Dataset repository](https://github.com/martj42/international_results).
   - [Pinned CSV](https://raw.githubusercontent.com/martj42/international_results/b7a3a8ee5d37780c6a03101c188658fd439e241d/results.csv).
3. **FIFA's tournament context** identifies Canada, Mexico and the USA as hosts. Venue countries come from the recorded ESPN fixture. Host-country indicators are a pre-match scheduled-context assumption; they are not evidence of an archived lineup or a measured player attribute.
   - [FIFA tournament page](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026).

All snapshots were collected on 10 October 2026. Source hashes are in `source_manifest.json`. The model build checks hashes; rebuilding from these saved inputs is offline and deterministic. A fresh live API download may change after source corrections and should be audited as a new dataset, not silently substituted.

## Sources inspected but not used as feature inputs

- [Mominul Islam's World Cup dataset](https://github.com/mominullptr/FIFA-World-Cup-2026-Dataset) offers 104 completed matches and a predictive feature table. Its [feature generator](https://github.com/mominullptr/FIFA-World-Cup-2026-Dataset/blob/main/generate_prediction_features.py) supplies first-game and missing-statistic defaults. Its documentation also describes estimated valuations for some players. Those precomputed features were rejected for this assignment's genuine-data requirement; none enter the final regressions.
- [stiles/world-cup](https://github.com/stiles/world-cup) provides FIFA-derived schedule/results collectors. The retrieved working results snapshot had incomplete later fixtures, so it was not used as the complete final-result source.
- [MrBridge's ESPN dataset card](https://huggingface.co/datasets/Mr-Bridge/fifa-world-cup-2026-espn) helped identify an ESPN-backed 104/208-table resource. The final package instead retrieves original ESPN match responses and reconstructs its own team rows and features.

These checks matter: a CSV with 104 rows is not automatically 104 verified final results, and a column labelled pre-match is not automatically a measured historical value.

## Course alignment

The supplied Assign.zip contains 26 EPUBs and no football dataset. `course_inventory.json` records their names, SHA-256 hashes and extracted text lengths from the earlier inspection. The relevant course material guided this implementation:

| EPUB | Relevant content | Use here |
|---|---|---|
| `5 (2).epub` | pandas merging, concatenation and missing values. | Validated opposing-team joins, the 208-row table, fold-local imputation. |
| `6 (2).epub` | Histograms/boxplots, scatterplots, correlations and heatmaps. | Training descriptive plots, predictor relationships, correlation diagnostics. |
| `8 (1).epub` | sklearn regression, MAE/MSE/RMSE/NRMSE and mean baseline. | Both OLS models and honest baseline comparisons. |
| `9.epub`, `9 (1).epub` | Multiple regression, equations, R², adjusted R², scaling, statsmodels and collinearity. | Eight-input equations, training-only scaling, robust summaries, VIF and residual diagnostics. |

Chronological validation, whole-match grouping, source evidence, conservative eligibility bounds and clustered standard errors extend the introductory examples to this paired tournament setting. Normal predictor distributions are not an OLS prerequisite, so no arbitrary Gaussian transformation is applied. No genuine score outlier is automatically deleted.

## Limits to the source claims

The dataset is a retrospective reconstruction, not an archive of forecasts or feature snapshots published before the matches. Two-source score agreement is corroboration; the providers may share upstream sources. Historical result corrections can be reflected in the current snapshot. The declared date/time bounds conservatively prevent using current/future games in feature computation under normal result availability, but are not measured publication times. Confirm rescheduling/delay exceptions and the extra-time definition before submission.
