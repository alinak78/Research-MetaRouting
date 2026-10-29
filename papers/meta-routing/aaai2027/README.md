# AAAI 2027 Main-Track Paper

The anonymous submission draft is `main.tex`. Submission-local copies of
`aaai2027.sty`, `aaai2027.bst`, `references.bib`, the result figure, and the
completed `ReproducibilityChecklist.tex` are included in this directory. The
unmodified official examples remain under `author-kit/`.

## Intended Contribution

A learned, budget-aware meta-routing policy that composes decomposition,
retrieval, code execution, delegation, and verification from raw task text.

## Evidence Included

- 504 generated natural-language tasks with executable, machine-checked outcomes
- Train, development, held-out test, and locked lexical-shift challenge splits
- Direct, random, keyword, static, fixed-agent, learned one-shot, and oracle baselines
- Local wall-clock latency and preregistered normalized operation costs
- Calibration, paired bootstrap intervals, exact sign tests, ablations, and sensitivity sweeps
- Completed AAAI reproducibility checklist

`author-kit/` contains the official AAAI-27 anonymous and camera-ready templates.
The submission manuscript must be anonymous and must not reuse the DAI paper as
a cosmetically reformatted archival submission.

## Compile

From this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

The checklist can be compiled separately with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir=build ReproducibilityChecklist.tex
```

Run `python experiments/meta-routing/aaai2027/prepare_submission.py` from the repository root
to compile, remove PDF metadata, scan for identifying strings, verify page size
and embedded fonts, and write the OpenReview PDFs.

## Historical Submission Artifacts

The historical submission directory contains:

- `AAAI27_Anonymous.pdf`: seven-page anonymous main paper
- `AAAI27_ReproducibilityChecklist.pdf`: separate completed checklist
- `code_data_supplement.zip`: identity-scanned reproducibility package

The manuscript uses executable local components, not live LLM or network tools;
normalized cost is not API pricing. This is stated throughout the paper. It must
not be submitted concurrently with a substantially similar archival DAI paper.

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
