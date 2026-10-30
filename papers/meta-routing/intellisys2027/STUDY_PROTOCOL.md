# IntelliSys 2027: separate recovery and verification study

Recorded before the first new evaluation run on 2026-10-29. This is a local prospective protocol, not external preregistration. The source and protocol hashes are recorded by the runner before test execution. Later repairs must be documented.

## Primary research question
Under a fixed tool-call budget, when should a controller retry, switch computation engines, or seek agreement to avoid silently wrong answers, and how does correlated failure alter the trade-off?

1. **RQ1 — Feedback and recovery:** Do retry and switch-on-error policies recover from transient and persistent explicit failures, and do those benefits extend to silent output corruption?
2. **RQ2 — Verification and resource allocation:** Can a development-tuned verification gate match or improve the correctness, wrong-answer rate, and call count of capable fixed verification/majority policies under budgets of 1, 2, and 3 actual engine invocations?
3. **RQ3 — Dependence and shift:** How do shared corruptions and higher independent corruption rates change the benefits of agreement and development-selected policies?

## What is new
No AAAI tasks, fitted lexical models, operation labels, result tables, or normalized action costs are used. This study has structured analytical queries over three externally supplied real datasets; SQLite, Python, and NumPy executions; response-conditioned control; explicit abstention; and counterfactual fault schedules hidden from controllers. It is not an LLM experiment or an independently authored query benchmark.

## Data and units
UCI Iris, Wine, and Banknote Authentication archives, downloaded from UCI. Their numerical feature columns are used; no class prediction is performed. COUNT, SUM, MEAN, and MAX queries filter one feature and aggregate another. Three target columns and two filter quantiles produce 24 queries per dataset per split, 72 development and 72 test queries. Development quantiles are .25/.75; test quantiles .35/.65. Ten fault seeds are repeated measurements, not new queries or templates. There are four authored query families. Public data independence does not make the query generator externally independent.

## Fault interventions
Fault-free; SQL transient exception; SQL persistent exception; independent silent corruption; doubled independent corruption; correlated silent corruption. Only the first four appear during development. Explicit faults affect the SQLite primary. Silent schedules are seeded per query/engine and persistent within an episode; repeated calls do not cleanse them. Correlated corruption applies the same numeric response offset to all engines. Faults are injected stress interventions, not empirically estimated production rates. No fault mode or affected-engine label is passed to controllers. Counterfactuals share the same query/seed/engine/attempt fault outcome.

## Policies and tuning
Single-engine policies for each engine; retry-SQL; switch-on-error; two-engine agreement with a third-engine tie breaker when affordable; fixed majority; operation-risk-gated verification; and a development-selected fixed policy. All obey the same hard cap on invocations; exceptions consume a call. No gold answer is available during a policy run. COUNT disagreement is numeric, without extra quality cues. Risk gating uses development primary silent-error rates by query family. Its threshold is selected on development among 0, .05, .10, .20, and 1. The common utility is correct=+1, wrong=-4, abstain=0, minus .05 per call. Report the full outcome components so the chosen utility cannot hide abstention. Fixed-policy selection maximizes the same development utility separately for each budget. Test regimes are never used for selection.

## Outcomes and inference
Report correct, wrong, abstention, answered fraction, wrong conditional on answered, mean actual calls, hard-budget compliance, and local execution time. Correctness uses an offline Decimal reference and numerical tolerance; it does not score route labels. For paired comparisons, average seeds per query and bootstrap queries within each dataset with a fixed seed, 1,000 draws. Report per-dataset and per-family results. Three datasets/four query families limit generalization; intervals describe the authored query suite under stipulated faults.

## Scope and submission status
The AAAI study is still under review. This manuscript must describe the related submission and substantive overlap honestly, following venue procedures for anonymous related-work disclosure. New experiments and different questions do not themselves certify simultaneous-submission compliance. No external submission is authorized by this protocol. Human authors must review the new design, arguments, conclusions, and AI-assisted manuscript before submission.
