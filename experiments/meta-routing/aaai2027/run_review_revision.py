"""Post-review diagnostics, preserving the original fit and evaluation splits.

All added comparisons are exploratory because the feedback exposes test/challenge
behavior. A current hash manifest is not evidence of historical preregistration.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from statistics import mean

from metarouter.executable_benchmark import run_executable_benchmark
from metarouter.executable_evaluation import compare_executable_families, summarize_executable_all
from metarouter.executable_executor import ACTION_COST, inspect_execution
from metarouter.executable_tasks import _TEMPLATES, generate_executable_tasks
from metarouter.models import RouteAction
from metarouter.review_baselines import CompleteRoutePolicy, FeasibleStaticPolicy, StaticFallbackPolicy, outage_in_prompt
from metarouter.text_router import (CalibratedTextOperationModel, LearnedBudgetPolicy,
                                   LearnedOneShotPolicy, StaticExecutablePolicy, tune_threshold)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'results/meta-routing/aaai2027/revision'
BUDGETS = (1.0, 1.75, 2.5, 3.0, 3.85, 4.5)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tasks = {split: generate_executable_tasks(split, count)
             for split, count in [('train', 72), ('dev', 24), ('test', 36), ('challenge', 36)]}
    model = CalibratedTextOperationModel().fit(tasks['train'], tasks['dev'])
    threshold = tune_threshold(model, tasks['dev'])
    joint = CompleteRoutePolicy(model).fit(tasks['train'], tasks['dev'])
    feasible_static = FeasibleStaticPolicy(tasks['dev'])
    full = LearnedBudgetPolicy(model, threshold)
    no_budget = LearnedBudgetPolicy(model, threshold, max_actions=3,
                                    enforce_budget=False, name='no_cost_budget')
    policies = [full, no_budget, joint, feasible_static, StaticFallbackPolicy(),
                StaticExecutablePolicy(), LearnedOneShotPolicy(model, threshold)]
    summaries, family_rows, trace_rows, comparisons, binding = [], [], [], [], []
    for split in ('test', 'challenge'):
        for budget in BUDGETS:
            evaluation = [replace(task, cost_budget=budget) for task in tasks[split]]
            traces = run_executable_benchmark(evaluation, policies,
                                             route_timing_repetitions=1,
                                             execution_timing_repetitions=1)
            for summary in summarize_executable_all(traces):
                selected = [trace for trace in traces if trace.policy == summary.policy]
                summaries.append({'split': split, 'budget': budget, **summary.to_dict(),
                                  'action_limit_compliance': mean(len(trace.actions) - 1 <= 3 for trace in selected),
                                  'feasible_success_rate': mean(trace.success and trace.within_cost_budget
                                                                and len(trace.actions) - 1 <= 3 for trace in selected)})
            trace_rows.extend({'budget': budget, **trace.to_dict()} for trace in traces)
            grouped = defaultdict(list)
            for trace in traces:
                grouped[trace.policy, trace.kind].append(trace)
            for (policy, kind), group in sorted(grouped.items()):
                family_rows.append({'split': split, 'budget': budget, 'policy': policy,
                                    'kind': kind, 'n': len(group),
                                    'success_rate': mean(trace.success for trace in group),
                                    'mean_cost': mean(trace.cost for trace in group),
                                    'budget_compliance': mean(trace.within_cost_budget for trace in group)})
            for baseline in ('static_workload', 'static_outage_fallback', 'feasible_static_fallback', 'complete_route'):
                comparisons.append({'split': split, 'budget': budget,
                                    **compare_executable_families(traces, full.name, baseline)})
            changed = sum(full.route(task).actions != no_budget.route(task).actions for task in evaluation)
            binding.append({'split': split, 'budget': budget, 'n': len(evaluation),
                            'cost_enforcement_changed_routes': changed,
                            'unconstrained_routes_over_budget': sum(sum(ACTION_COST[a] for a in no_budget.route(task).actions)
                                                                   > budget + 1e-9 for task in evaluation)})
        print(f'Evaluated {split} at {len(BUDGETS)} budgets', flush=True)
    write_csv(OUTPUT / 'summary.csv', summaries)
    write_csv(OUTPUT / 'families.csv', family_rows)
    write_csv(OUTPUT / 'traces.csv', trace_rows)
    write_csv(OUTPUT / 'budget_binding.csv', binding)
    (OUTPUT / 'family_comparisons.json').write_text(json.dumps(comparisons, indent=2) + '\n')

    uncalibrated = CalibratedTextOperationModel().fit(tasks['train'], tasks['dev'])
    uncalibrated.temperatures = {action: 1.0 for action in uncalibrated.temperatures}
    uncalibrated_threshold = tune_threshold(uncalibrated, tasks['dev'])
    calibration = []
    for split in ('dev', 'test', 'challenge'):
        for label, cutoff in [('fixed_threshold', threshold), ('retuned_on_dev', uncalibrated_threshold)]:
            policy = LearnedBudgetPolicy(uncalibrated, cutoff)
            calibration.append({'split': split, 'comparison': label, 'uncalibrated_threshold': cutoff,
                                'changed_routes': sum(full.route(task).actions != policy.route(task).actions
                                                      for task in tasks[split])})
    write_csv(OUTPUT / 'calibration_routes.csv', calibration)
    write_csv(OUTPUT / 'templates.csv', [
        {'kind': kind, 'split': split, 'template_count': len(templates),
         'task_count': sum(task.kind == kind for task in tasks[split]),
         'templates': json.dumps(templates)}
        for kind, splits in sorted(_TEMPLATES.items()) for split, templates in sorted(splits.items())])
    example = next(task for task in tasks['test'] if task.kind == 'invoice_reconcile')
    example_plan = full.route(example)
    (OUTPUT / 'execution_example.json').write_text(json.dumps({
        'task_id': example.task_id, 'prompt': example.prompt,
        'scores': {action.value: score for action, score in model.predict_proba(example.prompt).items()},
        'selected_route': [action.value for action in example_plan.actions],
        'router_inputs': 'prompt and budget only; payload is executor-only',
        'executor_kind': example.kind, 'expected_answer': example.expected_answer,
        **inspect_execution(example, example_plan),
    }, indent=2) + '\n')
    manifest = {
        'status': 'post-review exploratory analysis; current fingerprints, not historical lock evidence',
        'threshold': threshold, 'joint_temperature': joint.temperature,
        'budgets': BUDGETS, 'max_support_actions': 3,
        'maximum_three_support_route_cost': sum(sorted((cost for action, cost in ACTION_COST.items()
                                                       if action != RouteAction.ANSWER), reverse=True)[:3]) + ACTION_COST[RouteAction.ANSWER],
        'split_sha256': {split: hashlib.sha256(json.dumps([asdict(task) for task in examples],
                                                          sort_keys=True).encode()).hexdigest()
                         for split, examples in tasks.items()},
        'outage_prompt_markers': {split: {'outage_tasks': sum(task.kind == 'research_outage' for task in examples),
                                         'marked_outage_tasks': sum(task.kind == 'research_outage' and outage_in_prompt(task.prompt)
                                                                    for task in examples),
                                         'marked_other_tasks': sum(task.kind != 'research_outage' and outage_in_prompt(task.prompt)
                                                                   for task in examples)}
                                  for split, examples in tasks.items()},
        'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sorted((ROOT / 'src/metarouter').glob('*.py'))},
        'template_independence': 'one authored template per kind per split; generated values are not independent templates',
        'unresolved': ['independently authored external evaluation', 'live fallible tool or LLM validation',
                       'historical challenge lock timestamp and complete benchmark-development log'],
    }
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    # Paper tables are generated from these records, not manually copied numbers.
    lines = [r'% Generated by run_review_revision.py; post-review exploratory results.',
             r'\begin{table}[t]\centering\small',
             r'\caption{Post-review controls at $B=4.5$. All constrained policies allow at most three support operations.}',
             r'\label{tab:revision}', r'\begin{tabular}{lrrrr}\toprule',
             r' & \multicolumn{2}{c}{Test} & \multicolumn{2}{c}{Challenge} \\',
             r'Policy & Success & Cost & Success & Cost \\\midrule']
    names = [('learned_budget', 'Independent heads'), ('complete_route', 'Complete-route learner'),
             ('static_outage_fallback', 'Static + outage fallback'),
             ('feasible_static_fallback', 'Feasible dev-static')]
    for name, label in names:
        rows = [next(row for row in summaries if row['policy'] == name and row['budget'] == 4.5 and row['split'] == split)
                for split in ('test', 'challenge')]
        lines.append(label + ' & ' + ' & '.join(f"{row['success_rate']:.3f} & {row['mean_cost']:.2f}" for row in rows) + r' \\')
    lines += [r'\bottomrule\end{tabular}\end{table}', r'\begin{table}[t]\centering\small',
              r'\caption{Binding-budget test sweep: feasible success for independent heads (IH), complete routes (CR), and feasible dev-static (FS). Changed counts compare IH with cost enforcement disabled, retaining the same action cap.}',
              r'\label{tab:budgets}', r'\begin{tabular}{rrrrr}\toprule',
              r'$B$ & IH & CR & FS & Changed \\\midrule']
    for budget in BUDGETS:
        values = [next(row for row in summaries if row['policy'] == name and row['budget'] == budget and row['split'] == 'test')['feasible_success_rate']
                  for name in ('learned_budget', 'complete_route', 'feasible_static_fallback')]
        changed = next(row['cost_enforcement_changed_routes'] for row in binding if row['budget'] == budget and row['split'] == 'test')
        lines.append(f'{budget:.2f} & ' + ' & '.join(f'{value:.3f}' for value in values) + f' & {changed}' + r' \\')
    lines += [r'\bottomrule\end{tabular}\end{table}']
    (ROOT / 'papers/meta-routing/aaai2027/revision_tables.tex').write_text('\n'.join(lines) + '\n')
    print(f'Wrote revision artifacts to {OUTPUT}', flush=True)


if __name__ == '__main__':
    main()
