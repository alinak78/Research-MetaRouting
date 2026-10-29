# Revision based on reviewer feedback

The feedback was treated as review evidence. The added experiments are **post-review exploratory analyses**, designed after the original test and challenge results were known. The original fitted operation model and task generator were preserved. No external-validation claim is made.

## Changes and findings

| Concern | Implemented change | Observed result |
| --- | --- | --- |
| One-operation baseline is incapable by construction | Added a multiclass complete-route learner with the same training examples, train-only word/character vocabulary, optimization schedule and regularization; constrained inference selects a feasible complete class | Standard success 100%, challenge 93.5%, versus the original independent heads' 100% and 75.9%. Costs: 2.04/1.72 versus 1.76/1.56. No claim of independent-head superiority remains. |
| Static advantage confounded by outage handling | Added explicit prompt-health fallback to the historical workload workflow | 100% on both splits, at cost 3.11. This removes the original accuracy margin but retains five support operations on document tasks, so it is a diagnostic rather than a fully feasible comparator. |
| Baselines do not share constraints | Exhaustively evaluated all 32 canonical subsets on development examples to select a route per workload and explicit-health stratum under the same cost budget and three-operation cap | Feasible static success is 87.0% on both splits at budget 4.5, cost 2.29. It misses invoice and cross-field document families. |
| Cost budget cannot bind | Added budgets 1.00, 1.75, 2.50, 3.00, 3.85, and 4.50 on both evaluation splits; measured route changes and feasible success | At 1.75, enforcement changes 40/108 test routes and restores compliance from 63.0% to 100%. Feasible success is 63.0% in both enforcement arms. At 3.0 seven routes change; at 3.85 and 4.5 none do. This demonstrates enforcement, not an accuracy benefit. |
| No-budget ablation also removes the action cap | Retained max_actions=3 in the cost ablation and added an explicit no-cost-budget arm | Cost enforcement is now isolated from route capacity. |
| Task uncertainty counts repeated templates as independent | Added paired macro-family bootstrap intervals and family-level sign tests | The original standard static comparison has one improving family out of 11, macro effect .091, interval [0,.273], sign p=1. Task-level p=.0156 is no longer interpreted as evidence across independent phenomena. |
| Calibration contribution unclear | Counted changed routes at a fixed threshold and after development-only retuning | Unscaled scores change 20/72 development routes at .40 and no evaluation routes; retuning to .45 removes all differences. No demonstrated evaluated-outcome benefit. |
| One-shot control called threshold-matched but was not | Made its threshold configurable and used .40 in the new run; kept .50 in the historical experiment | Standard success remains 56.5%; challenge success is 45.4% at .40 versus historical 41.7% at .50. The historical comparison is labeled accordingly. |
| Composition implies learned planning | Revised title, abstract, contribution list, novelty discussion, and first-use definition | Defined as pre-execution subset selection followed by fixed canonical order. Dependencies, order, and replanning are not learned. |
| Template counts and outage markers unclear | Exported all templates, counts, marker audit, full task/source hashes, and executor example | 11 families, one template per family per split, 44 total. All seven outages in each evaluation split have explicit health wording; no non-outage task triggers the fallback rule. |
| Missing closely related work | Added verified TaskBench and LLM-as-Scheduler references and narrowed positioning | Contribution is a controlled executable integration and diagnostic protocol, rather than a new workflow-control paradigm. |
| Router/executor boundary opaque | Added an actual prompt, predicted scores, route and per-operation state snapshots | The example identifies payload access as executor-only and demonstrates extraction, computation, verification and answering. |

The complete-route classifier uses unweighted multiclass cross entropy, while the original independent heads retain class-balanced binary losses. Its temperature is selected on development data. This is a capable alternative with matched input features and optimization settings, not a single-variable causal ablation of the learning objective. Its classes are training-observed routes, so it cannot predict an unseen combination. The feasible static control additionally uses workload metadata and prompt-health rules; learned policies use only prompt text and budget.

The new run uses one route/execution timing repetition per task. Its latency columns measure local implementation overhead and are not directly comparable to the original five-repeat hardware measurements or live-tool latency.

## Remaining evidence gaps

- **Independent evaluation and realism:** the suite is still synthetic and uses family-specific deterministic Python handlers. A fresh independently authored suite or a real, fallible tool/LLM experiment is still required before making transfer or deployment claims. The new baseline results do not resolve this gap.
- **Historical provenance:** current hashes establish reproducibility from this revision. They cannot prove when the original challenge was locked or reconstruct every benchmark/feature/executor change made after standard-test inspection. No independently verifiable historical lock record or complete development log was found in the supplied project.
- **Generalization:** the added comparisons reused already known splits. Their challenge results must not be described as a new blind confirmation. A semantic router and learned sequential planner remain unevaluated.
- **Cost validity:** units are declared relative operation costs, not empirical dollars, tokens, or deployed latency. The budget sweep establishes behavior under this declared model only.

## Reproduce and inspect

```bash
PYTHONPATH=src python experiments/meta-routing/aaai2027/run_review_revision.py
python experiments/meta-routing/aaai2027/check_revision_results.py
pytest -q
```

Results are in `results/meta-routing/aaai2027/revision/`: task traces, full summary metrics, per-family outcomes, family comparisons, binding counts, calibration route changes, template inventory, execution example, and manifest. Paper tables are generated directly by the runner in `revision_tables.tex`.

The current revised source is `main.tex`; the revised PDF is `output/pdf/MetaRouting_Revised.pdf` at repository root. Previously submitted PDFs and arXiv/source archives under `submission/` are historical and have not been replaced. The code/data supplement can be rebuilt with `package_anonymous.py`.

Verified related work: [TaskBench](https://proceedings.neurips.cc/paper_files/paper/2024/hash/085185ea97db31ae6dcac7497616fd3e-Abstract.html), [LLM-as-Scheduler](https://aclanthology.org/2026.acl-long.581/).
