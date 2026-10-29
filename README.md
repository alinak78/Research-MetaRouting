# Research MetaRouting

This repository contains the meta-routing research project: benchmarks and
policies for the meta-decision layer of agentic systems, including when to
decompose, retrieve, execute code, delegate, verify, or answer directly.

The COA-Bench project has been separated into the sibling
`../Research-COAGeneration` repository. MetaRouting should contain only
meta-routing source code, experiments, papers, results, benchmark specs, and
dataset tooling.

```text
src/metarouter/        # Meta-routing models, policies, simulator, benchmarks
benchmarks/            # Operational, executable, and multilingual specs
experiments/           # DAI/AAAI/ORACLE experiment runners and checks
papers/                # Meta-routing and ORACLE paper artifacts
results/               # Generated benchmark artifacts
output/hf_dataset/     # Staged meta-routing dataset artifacts
tests/                 # Meta-routing unit tests
```

## MetaRoute-Bench

The DAI track compares routing policies across synthetic operational workload
profiles. It separates tasks, policies, seeded offline execution, traces, and
aggregate metrics so policies can be swapped without changing the evaluation
environment.

```bash
metarouter-benchmark --seeds 30 --output results/meta-routing/dai2026/main
python experiments/meta-routing/dai2026/run_ablations.py
python experiments/meta-routing/dai2026/plot_results.py
python experiments/meta-routing/dai2026/check_paper_results.py
```

## Executable Meta-Routing

The AAAI track adds a raw-text, budget-aware router and an executable benchmark
with exact answer checking. It includes held-out templates, a locked lexical
shift challenge split, and component-outage cases.

```bash
python experiments/meta-routing/aaai2027/run_executable.py
python experiments/meta-routing/aaai2027/run_ablations.py
python experiments/meta-routing/aaai2027/run_sensitivity.py
python experiments/meta-routing/aaai2027/plot_executable.py
python experiments/meta-routing/aaai2027/check_paper_results.py
```

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

## Reproducing Results

```bash
./run_all.sh
```

Runs the meta-routing test suite, DAI benchmark and ablations, DAI figure
generation and claim checks, AAAI executable benchmark, AAAI ablations,
sensitivity analysis, plotting, and claim checks. No GPU or API keys required;
everything uses synthetic/offline tasks and seeded execution.

## Primary Locations

- `src/metarouter/`: meta-routing models, policies, simulator, and executable benchmark
- `experiments/meta-routing/dai2026/`: DAI meta-routing benchmark runners
- `experiments/meta-routing/aaai2027/`: AAAI executable benchmark runners
- `experiments/oracle2026/`: multilingual/cultural routing extension placeholder
- `papers/meta-routing/dai2026/`: DAI Industry Track meta-routing paper
- `papers/meta-routing/aaai2027/`: AAAI meta-routing paper
- `papers/oracle2026/`: ORACLE paper placeholder
- `results/meta-routing/`: generated meta-routing artifacts
- `results/oracle2026/`: ORACLE result placeholder

## License

MIT - see [LICENSE](LICENSE) when present in this repository.

## Citation

```bibtex
@misc{metarouting2026,
  title   = {MetaRoute-Bench: Evaluating Meta-Decision Policies for Agentic Workflows},
  author  = {Anote AI},
  year    = {2026},
  url     = {https://github.com/anote-ai/research-metarouting}
}
```

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
