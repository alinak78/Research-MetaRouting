# Relationship to the AAAI study and reviewer feedback

The AAAI manuscript remains under review, as confirmed by the author on 2026-10-29. The IntelliSys paper is now a new study, replacing the initial adaptation draft.

| Dimension | AAAI submission | New IntelliSys study |
| --- | --- | --- |
| Research question | Predict a support-operation subset from prompt text | Decide whether to accept, retry, switch, or seek agreement after observing tool responses |
| Data | 504 synthetic tasks in 11 authored families | UCI Iris, Wine, Banknote numerical data; 72 new development and 72 new test queries in four authored aggregation families |
| Components | Five family-specific deterministic handlers | Executed SQLite queries, Python reductions, NumPy reductions, with explicit and silent fault interventions |
| Policy | Lexical logistic heads; fixed canonical ordering | Response-conditioned recovery/verification rules, development-estimated risk gate, and a development-selected capable fixed policy |
| Budget | Declared normalized action costs | Enforced counts of actual engine invocations, including errors |
| Main outcomes | Answer success, route labels, lexical shift | Correct, wrong, abstained, coverage, actual calls; failure dependence and wrong-value agreement |
| Evidence | Existing AAAI test/challenge results | Entirely fresh execution traces; AAAI results are not used in new tables |
| Inference | Repeated synthetic templates; added family analyses | Average fault repeats within query; paired query-cluster bootstrap within each of three datasets; limited to four query families |

## How the feedback changed the design

- **“Substantive addition, not a rewording” / realism:** replaced the study, added public real data and executed database/numerical engines. Injection is still controlled and local; this is not live-LLM or production-endpoint validation.
- **Weak, incapable baseline:** included all three standalone engines, retry, switching, agreement, fixed majority, and a development-selected policy. The selected fixed policy is NumPy alone at every budget; it is prominently reported even where it beats the more complex controller.
- **Outage marker confound:** no prompt or structured query reveals the hidden fault regime. Controllers observe only actual success/error responses and returned values.
- **Inactive budgets:** budgets are 1, 2, or 3 actual invocations. Exceptions consume budget. Calls stop at the cap.
- **Unsupported calibration/gating benefit:** tested the gate. Development selects always verify for budgets 2/3; the paper reports collapse to the simple agreement baseline, rather than claiming a selective-learning advance.
- **Repeated templates and statistics:** four authored query families are disclosed. Repeated fault seeds are not counted as independent queries. Public data do not make our query generator independently authored.
- **Development leakage/provenance:** saved protocol, source hashes, development choices, and query hashes before the first main test evaluation. This is local evidence, not independently timestamped preregistration. The later collision sensitivity is explicitly labeled post-run and exploratory; no original policies were retuned.
- **Construction-driven success:** engine-specific offsets make two corrupted outputs disagree by construction. The paper says so. A separate sensitivity lets independent failures return the same wrong value; common-mode corruption is also tested. No headline zero-error claim is generalized to natural failures.
- **Novelty:** contribution is a controlled empirical comparison of response-conditioned tool acceptance and its dependence assumptions, not a new learning, planning, or fault-tolerance algorithm.

## Before submission

This separation documents real methodological and empirical differences; it does not certify compliance with either venue's overlap policy. The human authors should review both complete manuscripts, disclose the related submission through the venue's permitted anonymous procedure, and obtain clarification if needed. The new manuscript includes an anonymized related-submission reference. Supply the companion manuscript where required. Do not claim the two works are unrelated or that rewriting alone resolves overlap.

The new design, argument, conclusions, and AI-assisted draft require human-author review under IntelliSys's GenAI policy. No human approval or review is asserted to have occurred. No paper has been submitted by this task.
