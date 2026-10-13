# Verification

Verified on Windows using Python 3.12.14 and the exact dependency versions in `requirements-tested.txt`.

**20 automated tests passed.** The captured run is `test_log.txt`. Tests cover schema/row-count constraints, exactly eight inputs and four shared concepts, target/opponent joins, duplicate IDs/fixtures, wrong year, numeric errors, provenance/timestamp checks, whole-match chronological separation, purged delayed labels, training-only imputation/scaling, rank deficiency, complete model/plot generation and saved-model prediction equivalence.

Five additional historical/source tests verify the prior-ten calculation and population standard deviation, exclusion of current/future outcomes, exclusion at the exact conservative eligibility boundary, real-data row counts/no missing values/forward warm-up, and deterministic rebuilding with all 104 source-score agreements. Synthetic fixtures are explicitly marked `TEST_NOT_REAL_*` and created only in temporary test folders. Real fitted outputs in `results/` use the bundled ESPN and international-results snapshots.

All four named scripts were separately executed successfully. Independent task runs and the integration run produced identical saved model JSON and holdout metrics. `cli_checks.json` records their exit codes and messages. Both actual diagnostic panels were visually inspected for readable layout and the influence findings recorded in RESULTS_REVIEW.md.

Reproduce tests with:

```text
python -m unittest discover -s tests -v
```

The final verification used `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` to keep numerical-library startup predictable on this Windows machine. These are optional execution settings, not fitted model parameters. Inputs, folds and OLS fitting are deterministic; input SHA-256 hashes and package versions are recorded in the run manifest.

Software tests do not certify historical completeness, first-publication times, source independence or causal interpretation. The explicit timing assumptions and source limitations still apply. The two ambiguous unrelated 1974 historical records are flagged and do not enter participating teams' histories.

## Presentation revision verification

23 automated tests pass, including escaping, preservation of saved metrics, no-open behaviour and browser-failure fallback. All four named entry scripts and the training-only sensitivity script passed. Main model JSON and holdout metrics match the previous version exactly; individual and integration outputs match. All HTML graph targets exist. Browser automation was unavailable in the restricted environment; default-browser opening is covered by mocked success/failure behaviour, and the page can always be opened manually.

The Word report was rendered with Aspose.Words after the standard LibreOffice renderer was unavailable. All four page images were visually inspected. The renderer’s evaluation overlays occur only in internal preview images; the delivered DOCX was authored with python-docx and contains no evaluation marks. Check Word page count again after adding IDs or changing text.
