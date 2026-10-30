# IntelliSys 2027 research draft

**When Tool Agreement Is Not Enough: Budgeted Recovery and Silent-Error Acceptance in Intelligent Workflows**

This replaces the initial format-only adaptation with a separate recovery/verification study. The AAAI manuscript and its experiment files are unchanged. The new paper has three research questions:

1. Which visible failures are repaired by retrying or switching, and do these mechanisms address silent corruption?
2. At fixed invocation budgets, does a development-tuned verification gate improve on capable fixed policies?
3. How do corruption frequency, coinciding wrong values, and shared faults change agreement's reliability?

The main experiment has 72 development and 72 test queries over UCI Iris, Wine, and Banknote Authentication; four authored aggregation families; three real local computation engines; nine controllers; call caps 1/2/3; and ten paired fault seeds. There are 116,640 main policy episodes and 38,880 later exploratory collision-sensitivity episodes. These repetitions are not independent tasks. Main and extension results are kept separate.

## Reproduce

From the repository root, install the project and development dependencies (`pip install -e '.[dev]'`). For a fresh run, the results directory must not already contain traces; the runner refuses to silently overwrite an evaluated run. Preserve the supplied run when choosing a fresh checkout for replication.

```bash
PYTHONPATH=src python experiments/meta-routing/intellisys2027/run_recovery.py
PYTHONPATH=src python experiments/meta-routing/intellisys2027/run_collision_sensitivity.py
PYTHONPATH=src python experiments/meta-routing/intellisys2027/prepare_paper.py
python -m pytest -q
```

For the supplied run, use only `prepare_paper.py` to verify trace-derived summaries and regenerate tables/figures. It checks the paired fault schedule, budget ledger, outcomes, frozen source hashes, data hashes, abstract length, and citation coverage.

Build the manuscript from this folder:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

The official IntelliSys download supplies the unmodified `svproc.cls`, associated styles, and `splncs03.bst`. XeLaTeX uses Times New Roman, as specified in the provided template. Install Times New Roman if the build host lacks it; do not change the template margins to match a page count. Figures are vector PDFs.

Official requirements: https://saiconference.com/IntelliSys/CallforPapers
Template: https://saiconference.com/Downloads/SAI_Paper_Format_Latex_Conference.zip

## Validation and interpretation

The main protocol and fits were saved before faulted main-policy test evaluation. Clean engine/reference agreement was audited on both development and test query inputs before that freeze; this checks execution correctness and is disclosed in the paper. It is not an independent external preregistration. The collision model was added after seeing the structural limitation of the main injector, without retuning policies.

The fitted gate selects full verification at call caps two and three, so no selective-gating benefit is claimed. Distinct wrong offsets make zero accepted errors structural; the collision sensitivity explicitly removes that assumption. Data are public real records, but queries and fault interventions are authored for this study. This is not a live-LLM study or a claim about natural engine failure rates.

## Submission status and remaining author work

This is an anonymous **research draft**, not an externally submitted paper. The related AAAI paper is still under review. `OVERLAP_AND_FEEDBACK.md` maps the differences and the review concerns. Authors must assess both complete manuscripts under the venues' overlap policies and disclose the related submission through the permitted anonymous procedure. Methodological differences do not automatically certify eligibility.

IntelliSys requires human authors to develop and take responsibility for scientific ideas, arguments, results, and conclusions, and to review AI-assisted material. The manuscript discloses the actual AI assistance, including design and code. Human authors must review and take ownership of this work before submission; no such approval is claimed. The anonymous related-submission reference may need to be accompanied by the companion manuscript through the portal or chairs.

Initial submission is PDF only. The abstract is 201 words; the built draft is 12 pages including references, below the stated limit of 18 main-text pages plus up to 7 pages for references/appendices. These facts do not establish research acceptance or originality clearance. The Round 1 deadline listed by the CFP is 1 November 2026 AoE.
