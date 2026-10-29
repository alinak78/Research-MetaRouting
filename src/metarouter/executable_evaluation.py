"""Task-level metrics and paired inference for executable routing traces."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import asdict, dataclass
from statistics import mean

from .executable_models import ExecutableTrace


@dataclass(frozen=True)
class ExecutableSummary:
    policy: str
    n: int
    success_rate: float
    success_ci95_low: float
    success_ci95_high: float
    mean_cost: float
    mean_latency_ms: float
    budget_compliance: float
    route_exact_match: float
    action_precision: float
    action_recall: float
    action_f1: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutableComparison:
    treatment: str
    baseline: str
    success_difference: float
    ci95_low: float
    ci95_high: float
    treatment_only_successes: int
    baseline_only_successes: int
    exact_sign_p: float
    cost_difference: float
    latency_difference_ms: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _bootstrap_mean_interval(
    values: list[float],
    samples: int = 2000,
    seed: int = 2701,
) -> tuple[float, float]:
    rng = random.Random(seed)
    replicates = [
        mean(values[rng.randrange(len(values))] for _ in values)
        for _ in range(samples)
    ]
    return _percentile(replicates, 0.025), _percentile(replicates, 0.975)


def _action_counts(traces: list[ExecutableTrace]) -> tuple[int, int, int]:
    true_positive = false_positive = false_negative = 0
    for trace in traces:
        predicted = set(trace.actions) - {"answer"}
        required = set(trace.required_actions)
        true_positive += len(predicted & required)
        false_positive += len(predicted - required)
        false_negative += len(required - predicted)
    return true_positive, false_positive, false_negative


def summarize_executable_policy(
    traces: list[ExecutableTrace],
) -> ExecutableSummary:
    if not traces:
        raise ValueError("at least one trace is required")
    policies = {trace.policy for trace in traces}
    if len(policies) != 1:
        raise ValueError("traces must belong to one policy")
    outcomes = [float(trace.success) for trace in traces]
    low, high = _bootstrap_mean_interval(outcomes)
    true_positive, false_positive, false_negative = _action_counts(traces)
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 1.0
    recall = true_positive / recall_denominator if recall_denominator else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return ExecutableSummary(
        policy=next(iter(policies)),
        n=len(traces),
        success_rate=mean(outcomes),
        success_ci95_low=low,
        success_ci95_high=high,
        mean_cost=mean(trace.cost for trace in traces),
        mean_latency_ms=mean(
            trace.route_latency_ms + trace.execution_latency_ms for trace in traces
        ),
        budget_compliance=mean(float(trace.within_cost_budget) for trace in traces),
        route_exact_match=mean(float(trace.route_exact_match) for trace in traces),
        action_precision=precision,
        action_recall=recall,
        action_f1=f1,
    )


def summarize_executable_all(
    traces: list[ExecutableTrace],
) -> list[ExecutableSummary]:
    grouped: dict[str, list[ExecutableTrace]] = defaultdict(list)
    for trace in traces:
        grouped[trace.policy].append(trace)
    return sorted(
        (summarize_executable_policy(items) for items in grouped.values()),
        key=lambda summary: (-summary.success_rate, summary.mean_cost),
    )


def _exact_sign_p(treatment_only: int, baseline_only: int) -> float:
    discordant = treatment_only + baseline_only
    if discordant == 0:
        return 1.0
    smaller = min(treatment_only, baseline_only)
    tail = sum(math.comb(discordant, index) for index in range(smaller + 1)) / (
        2**discordant
    )
    return min(1.0, 2.0 * tail)


def compare_executable(
    traces: list[ExecutableTrace],
    treatment: str,
    baseline: str,
) -> ExecutableComparison:
    grouped = {(trace.policy, trace.task_id): trace for trace in traces}
    task_ids = sorted(
        {task_id for policy, task_id in grouped if policy == treatment}
        & {task_id for policy, task_id in grouped if policy == baseline}
    )
    if not task_ids:
        raise ValueError("no paired tasks found")
    differences = [
        float(grouped[(treatment, task_id)].success)
        - float(grouped[(baseline, task_id)].success)
        for task_id in task_ids
    ]
    low, high = _bootstrap_mean_interval(differences, seed=2702)
    treatment_only = sum(difference == 1.0 for difference in differences)
    baseline_only = sum(difference == -1.0 for difference in differences)
    return ExecutableComparison(
        treatment=treatment,
        baseline=baseline,
        success_difference=mean(differences),
        ci95_low=low,
        ci95_high=high,
        treatment_only_successes=treatment_only,
        baseline_only_successes=baseline_only,
        exact_sign_p=_exact_sign_p(treatment_only, baseline_only),
        cost_difference=mean(
            grouped[(treatment, task_id)].cost
            - grouped[(baseline, task_id)].cost
            for task_id in task_ids
        ),
        latency_difference_ms=mean(
            (
                grouped[(treatment, task_id)].route_latency_ms
                + grouped[(treatment, task_id)].execution_latency_ms
            )
            - (
                grouped[(baseline, task_id)].route_latency_ms
                + grouped[(baseline, task_id)].execution_latency_ms
            )
            for task_id in task_ids
        ),
    )


def workload_success(
    traces: list[ExecutableTrace],
) -> dict[str, dict[str, float]]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for trace in traces:
        grouped[(trace.policy, trace.workload)].append(float(trace.success))
    result: dict[str, dict[str, float]] = defaultdict(dict)
    for (policy, workload), outcomes in grouped.items():
        result[policy][workload] = mean(outcomes)
    return dict(result)


def compare_executable_families(
    traces: list[ExecutableTrace], treatment: str, baseline: str,
) -> dict[str, object]:
    """Paired macro-family effect; resample whole kinds, not template instances.

    The repeated direct-literal family is one cluster across workloads. This is
    exploratory uncertainty over the observed families, not an external-population
    guarantee. Complete pairing is required; missing tasks must not vanish silently.
    """
    arms = {policy: [trace for trace in traces if trace.policy == policy]
            for policy in (treatment, baseline)}
    indexed = {policy: {trace.task_id: trace for trace in arm}
               for policy, arm in arms.items()}
    if any(len(indexed[policy]) != len(arm) for policy, arm in arms.items()):
        raise ValueError('duplicate task IDs in comparison')
    if not indexed[treatment] or indexed[treatment].keys() != indexed[baseline].keys():
        raise ValueError('comparison requires identical nonempty paired task sets')
    families: dict[str, list[float]] = defaultdict(list)
    for task_id, treated in indexed[treatment].items():
        control = indexed[baseline][task_id]
        if treated.kind != control.kind or treated.split != control.split:
            raise ValueError('paired task family and split must agree')
        families[treated.kind].append(float(treated.success) - float(control.success))
    effects = [mean(values) for values in families.values()]
    low, high = _bootstrap_mean_interval(effects, seed=2703)
    wins = sum(effect > 0 for effect in effects)
    losses = sum(effect < 0 for effect in effects)
    return {
        'treatment': treatment, 'baseline': baseline, 'n_families': len(effects),
        'macro_family_success_difference': mean(effects),
        'family_bootstrap_ci95_low': low, 'family_bootstrap_ci95_high': high,
        'treatment_only_families': wins, 'baseline_only_families': losses,
        'family_sign_p': _exact_sign_p(wins, losses),
        'family_effects': {kind: mean(values) for kind, values in sorted(families.items())},
    }
