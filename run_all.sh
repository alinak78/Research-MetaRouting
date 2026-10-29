#!/usr/bin/env bash
# Reproduce every meta-routing result, table, and figure in this repository.
#
# Usage:
#   ./run_all.sh
#
# Expected runtime: ~5-10 minutes on a laptop. No GPU or API keys required.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "==> Installing dependencies (editable install, dev extras)"
python -m pip install -e ".[dev]"

echo "==> Running meta-routing test suite"
python -m pytest tests/ -v

echo "==> Running DAI metarouter benchmark (30 seeds, 8 policies)"
python -m metarouter.cli --seeds 30 --output results/meta-routing/dai2026/main

echo "==> Running DAI adaptive-policy ablations"
python experiments/meta-routing/dai2026/run_ablations.py

echo "==> Generating DAI figures"
python experiments/meta-routing/dai2026/plot_results.py

echo "==> Verifying DAI paper claims"
python experiments/meta-routing/dai2026/check_paper_results.py

echo "==> Running AAAI executable benchmark"
python experiments/meta-routing/aaai2027/run_executable.py

echo "==> Running AAAI ablations"
python experiments/meta-routing/aaai2027/run_ablations.py

echo "==> Running AAAI sensitivity analysis"
python experiments/meta-routing/aaai2027/run_sensitivity.py

echo "==> Running post-review controls and binding-budget analysis"
python experiments/meta-routing/aaai2027/run_review_revision.py
python experiments/meta-routing/aaai2027/check_revision_results.py

echo "==> Generating AAAI figures"
python experiments/meta-routing/aaai2027/plot_executable.py

echo "==> Verifying AAAI paper claims"
python experiments/meta-routing/aaai2027/check_paper_results.py

echo ""
echo "==> Done. Artifacts written to results/meta-routing/"
