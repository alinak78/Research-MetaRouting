# AAAI 2027 Experiments

- `run_executable.py`: generate splits, fit and calibrate the raw-text router,
  run eight held-out policies, and export task-level traces and paired tests.
- `run_ablations.py`: evaluate character features, calibration, composition,
  and budget enforcement.
- `plot_executable.py`: generate the paper tradeoff figure from exported CSVs.
- `run_sensitivity.py`: evaluate training-set size and route-threshold sensitivity
  on standard and locked challenge splits.
- `prepare_submission.py`: compile with PDFLaTeX, clear PDF metadata, scan for
  identity strings, verify page size/count and font embedding, and write the
  two OpenReview PDFs.

Run from the repository root after `pip install -e ".[dev]"`. These experiments
use machine-checked executable outcomes. The earlier DAI seeded simulator is not
used as AAAI evidence.

## Post-review revision

The paper and evaluation now include complete-route classification, explicit
outage fallback, a constraint-matched development-selected static control,
binding-budget sweeps, and family-clustered inference. Reproduce with:

```bash
PYTHONPATH=src python experiments/meta-routing/aaai2027/run_review_revision.py
python experiments/meta-routing/aaai2027/check_revision_results.py
```

See `papers/meta-routing/aaai2027/FEEDBACK_RESPONSE.md` for changes, results, and
unresolved external-validation and historical-provenance gaps. The revised PDF
is `output/pdf/MetaRouting_Revised.pdf`. Previously submitted PDF/source bundles
are historical; they do not contain this revision. These new comparisons are
post-review exploratory analyses, not a new independent test.
