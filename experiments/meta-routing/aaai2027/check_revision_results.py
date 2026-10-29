"""Check revised paper claims and feasibility directly against exported traces."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'results/meta-routing/aaai2027/revision'


def rows(name):
    with (OUTPUT / name).open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def main():
    traces = rows('traces.csv')
    grouped = defaultdict(list)
    for trace in traces:
        grouped[trace['split'], trace['budget'], trace['policy']].append(trace)
    for summary in rows('summary.csv'):
        arm = grouped[summary['split'], summary['budget'], summary['policy']]
        assert len(arm) == int(summary['n']) == 108
        feasible = [trace['within_cost_budget'] == 'True' and len(trace['actions'].split('|')) <= 4
                    for trace in arm]
        expected = mean(trace['success'] == 'True' and valid for trace, valid in zip(arm, feasible))
        assert abs(expected - float(summary['feasible_success_rate'])) < 1e-12
        if summary['policy'] in {'learned_budget', 'complete_route', 'feasible_static_fallback'}:
            assert all(feasible), f'constraint violation: {summary}'
    base = {(r['split'], r['policy']): r for r in rows('summary.csv') if r['budget'] == '4.5'}
    assert float(base['test', 'complete_route']['success_rate']) == 1
    assert round(float(base['challenge', 'complete_route']['success_rate']), 3) == .935
    assert round(float(base['challenge', 'learned_budget']['success_rate']), 3) == .759
    assert all(float(base[split, 'static_outage_fallback']['success_rate']) == 1 for split in ('test', 'challenge'))
    assert all(round(float(base[split, 'feasible_static_fallback']['success_rate']), 3) == .870 for split in ('test', 'challenge'))
    binding = {(r['split'], r['budget']): r for r in rows('budget_binding.csv')}
    assert int(binding['test', '1.75']['cost_enforcement_changed_routes']) == 40
    assert all(int(r['cost_enforcement_changed_routes']) == 0 for r in binding.values() if float(r['budget']) >= 3.85)
    comparisons = json.loads((OUTPUT / 'family_comparisons.json').read_text())
    original = next(r for r in comparisons if r['split'] == 'test' and r['budget'] == 4.5 and r['baseline'] == 'static_workload')
    assert original['n_families'] == 11 and original['family_sign_p'] == 1
    assert all(int(r['template_count']) == 1 for r in rows('templates.csv'))
    example = json.loads((OUTPUT / 'execution_example.json').read_text())
    assert example['answer'] == example['expected_answer'] and example['failure_mode'] is None
    paper = (ROOT / 'papers/meta-routing/aaai2027/main.tex').read_text()
    tables = (ROOT / 'papers/meta-routing/aaai2027/revision_tables.tex').read_text()
    assert r'\input{revision_tables}' in paper
    assert 'Complete-route learner & 1.000 & 2.04 & 0.935 & 1.72' in tables
    assert '1.75 & 0.630 & 0.630 & 0.630 & 40' in tables
    assert 'post-review' in paper.lower()
    print('Revised claims, trace feasibility, template counts, and family controls verified.')


if __name__ == '__main__':
    main()
