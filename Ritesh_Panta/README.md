# HIT140 Assessment 3: World Cup 2026 regression

This repository holds the Python code, source data and results for Objective 2 of the HIT140 Foundations of Data Science group project. Objective 2 fits two multiple linear regression models on the 104 matches of the 2026 FIFA World Cup. Every predictor uses only information available before kick-off.

| Task | Question | Unit of observation | Rows | Response |
|---|---|---|---|---|
| 2.1 | What is the goal difference between two teams? | One match | 104 | `goals_a - goals_b` |
| 2.2 | How many goals does one team score? | One team in one match | 208 | Goals scored by that team |

Team A and team B follow ESPN's listed order. The order does not imply a home-ground advantage.

## Repository layout

Keep the whole folder together. The entry scripts are short wrappers around the shared code in `project.py` and `build_dataset.py`, so none of them works alone.

```text
README.md
START_HERE.bat                      Windows: create environment, install, run everything, open results
OPEN_RESULTS.bat                    Windows: open the saved results page without running Python
project.py                          Shared pipeline: validation, splitting, OLS, diagnostics, plots
build_dataset.py                    Rebuilds the raw feature tables from the source snapshots
view_results.py                     Builds the offline results page
Avayash_Gaire_data.py               Entry point: rebuild and validate the datasets
Bijendra_Karki_goal_difference.py   Entry point: Task 2.1
Ritesh_Panta_goals_scored.py        Entry point: Task 2.2
Kalyan_Acharya_integration.py       Entry point: rebuild data, run both models, write the summary
review_models.py                    Training-only coefficient sensitivity check
requirements-tested.txt             Pinned package versions used for testing
requirements.txt                    Broader version ranges
DATA_GUIDE.md                       Predictor definitions, timing rules, cleaning steps
SOURCE_REVIEW.md                    Accepted and rejected data sources
RESULTS_REVIEW.md                   Review of the fitted results
ADDITIONAL_REVIEW.md                Forward validation and influence sensitivity
TESTING.md, test_log.txt            Test description and the captured test run
SUBMISSION_CHECKLIST.md             Remaining submission steps
PACKAGE_MANIFEST.json, cli_checks.json
HIT140_Group_Report.docx            The group report
docs/                               Member notes: Task 2.1 model, Task 2.2 data dictionary and results
.gitattributes                      Keeps source snapshots byte for byte
data/
  sources/                          Pinned source snapshots with SHA-256 hashes
  raw/                              Model inputs: matches, pre-match features, provenance
results/
  RESULTS.html                      Offline results page
  INTEGRATION_SUMMARY.md            Metrics for both tasks
  task_2_1/, task_2_2/              Equation, coefficients, diagnostics, plots, predictions
  prepared/                         Validated 104-row and 208-row tables
tests/
```

## Run the project

### On Windows

1. Install Python 3.12.
2. Extract or clone the whole repository into a new folder.
3. Double-click `START_HERE.bat`. It creates a `.venv` environment, installs `requirements-tested.txt`, runs both models and saves the output to `results_reproduced`. The terminal prints the metrics, equations and holdout predictions, and a results page opens in the browser.

Installation needs an internet connection. Rebuilding the data and fitting the models do not, because the source snapshots are bundled. To view the saved results without running anything, double-click `OPEN_RESULTS.bat` or open `results/RESULTS.html`. The page works offline.

### From a terminal

```text
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-tested.txt
python -m unittest discover -s tests -v
python Kalyan_Acharya_integration.py --out results_reproduced
```

Use a new output folder for each run. GitHub's file view does not run Python, so the repository has to be downloaded or cloned first.

To run one part on its own:

```text
python Avayash_Gaire_data.py --out results_reproduced
python Bijendra_Karki_goal_difference.py --out results_reproduced
python Ritesh_Panta_goals_scored.py --out results_reproduced
```

The two modelling scripts revalidate `data/raw/` before fitting. The data script and the integration script rebuild `data/raw/` from `data/sources/`, and the rebuild is deterministic. The optional arguments `--raw` and `--out` select other folders, and the data and integration scripts also accept `--sources`. The two modelling scripts and the integration script also accept `--no-open`, which saves results without opening the browser. Without `--out`, results are written to `results/` and replace the saved copies.

## Data

ESPN's public World Cup scoreboard feed supplies the match results, exact UTC kickoff times, venues and team order. A pinned snapshot of Mart Jürisoo's CC0 international-results dataset (commit `b7a3a8ee`) supplies the earlier matches behind each feature, and it confirms the score of all 104 matches. Both sources were collected on 10 October 2026. A public ready-made feature table was inspected and rejected because its generator fills missing values with defaults. `DATA_GUIDE.md` and `SOURCE_REVIEW.md` give the full account.

Conventions that apply throughout:

- A pre-match feature is computed from a team's last ten eligible senior international results. A result with only a date becomes eligible two UTC days after that date, strictly before the target kickoff.
- Training labels count as known 24 hours after kickoff, and host-country context counts as known a week ahead. These are conservative assumptions, not measured publication times.
- Scores include extra time and exclude shootouts, for both responses and history-based predictors. The group must confirm this convention against the assignment brief.
- No match result is inferred, and the predictors have no missing cells.
- Files in `data/sources/` must stay byte for byte as they are, because `build_dataset.py` checks their hashes. The `.gitattributes` file stops git from changing their line endings.

The features are a retrospective rebuild from snapshots taken after the tournament. They are not an archive of values published before each match.

## Model design

Each model has eight predictors. Four underlying concepts appear in both models, the maximum the brief allows: goals scored, goals conceded, days since the last match and win rate. IDs, dates and team names never enter either regression.

Task 2.1 uses the difference between team A and team B for each of these:

- goals scored
- goals conceded
- win rate
- days since the last match
- matches in the last 365 days
- standard deviation of goal difference
- previous World Cup appearances
- host-country advantage

Task 2.2 uses four measures for the scoring team: goals scored, scoring rate, days since the last match and the standard deviation of goals scored. It uses four for the opponent: goals conceded, win rate, clean-sheet rate and draw rate.

Validation works as follows:

- The holdout is the last 20% of distinct UTC match days: 7 matches (14 team rows) from 10 to 19 July. The training set has 96 matches (192 rows).
- One 9 July match stays in the dataset but is left out of fitting, because its label-availability bound falls after the first held-out kickoff.
- Five expanding forward folds run inside the training period after a warm-up of at least 20 matches. Both rows of a match always stay together.
- Median imputation and z-score scaling are fitted inside each training partition. The model is ordinary least squares with an intercept. There is no feature expansion, automatic variable deletion, clipping or rounding.
- Each model is compared with a baseline that predicts the training mean.
- Task 2.1 uses HC3 robust standard errors. Task 2.2 uses standard errors clustered by match.

## Results

The table shows the chronological holdout.

| Task | Holdout size | Model | MAE | RMSE | R² |
|---|---|---|---:|---:|---:|
| 2.1 | 7 matches | Linear regression | 1.211 | 1.402 | 0.108 |
| 2.1 | 7 matches | Training mean | 1.503 | 1.690 | -0.295 |
| 2.2 | 7 matches (14 rows) | Linear regression | 1.127 | 1.646 | -0.125 |
| 2.2 | 7 matches (14 rows) | Training mean | 1.143 | 1.602 | -0.066 |

Task 2.1 beats the baseline on all three measures. Task 2.2 does not: its MAE is slightly lower, but its RMSE and R² are worse than predicting the training mean. Inside the training period, the pooled out-of-fold RMSE is 1.692 against 2.067 for Task 2.1, and 1.227 against 1.316 for Task 2.2. Good earlier validation does not guarantee the same result on a seven-match holdout from later in the tournament.

Each task folder holds the fold and holdout metrics and predictions, the split manifest, the model JSON, the equation, the robust OLS summary, coefficient inference, missingness, descriptive statistics, the correlation matrix, VIF, influence measures and four plots. Fractional and negative goal predictions are kept for evaluation. The Task 2.2 holdout produced none that were negative.

## Limitations

- Sample size. With 104 matches and a holdout of seven, the metrics are unstable.
- Count response. Goals are non-negative counts, and linear regression can predict fractional or negative values.
- Collinearity. The Task 2.2 VIF output shows moderate multicollinearity, with a maximum of about 6.5. The team kept all eight predictors rather than dropping any to improve the fit.
- Influential match. In Task 2.1, one training match (Saudi Arabia against Uruguay) has a very large influence, and removing it changes the days-since-last-match coefficient. The main model keeps it. `ADDITIONAL_REVIEW.md` explains the check.
- Dependence. Teams repeat across matches and over time, so standard errors are approximate.
- Association only. The coefficients describe statistical association, not cause.
- Retrospective features. The eligibility cut-offs are assumptions, not archived publication times.
- Extra time. The score definition includes extra time and needs confirming.

## Tests

`python -m unittest discover -s tests -v` runs 23 tests. They cover the schema and row counts, the eight-predictor and four-shared-concept rules, the opponent joins, duplicate and wrong-year records, provenance and timing checks, whole-match separation in the split, training-only imputation and scaling, rank deficiency, model and plot generation, the prior-ten calculations, and a deterministic rebuild with all 104 source scores in agreement. Synthetic test data is marked `TEST_NOT_REAL_*` and is created only in temporary folders. The tests do not certify historical completeness or first-publication times. See `TESTING.md`.
