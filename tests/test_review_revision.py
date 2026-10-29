"""Scientific controls: constraints, hidden annotation leakage, and paired clusters."""
from dataclasses import replace

import pytest

from metarouter.executable_benchmark import run_executable_benchmark
from metarouter.executable_evaluation import compare_executable_families
from metarouter.executable_tasks import generate_executable_tasks
from metarouter.models import RouteAction, Workload
from metarouter.review_baselines import CompleteRoutePolicy, FeasibleStaticPolicy, StaticFallbackPolicy, route_cost
from metarouter.text_router import CalibratedTextOperationModel, LearnedBudgetPolicy, OraclePolicy


@pytest.fixture(scope='module')
def controls():
    train = generate_executable_tasks('train', 72)
    dev = generate_executable_tasks('dev', 24)
    model = CalibratedTextOperationModel().fit(train, dev)
    return (CompleteRoutePolicy(model).fit(train, dev), FeasibleStaticPolicy(dev), model)


def test_controls_share_constraints_and_do_not_read_hidden_fields(controls):
    joint, static, _ = controls
    for task in generate_executable_tasks('challenge', 10):
        for budget in (1.0, 1.75, 2.5, 3.0, 4.5):
            task = replace(task, cost_budget=budget)
            hidden_changed = replace(task, kind='unknown', payload={}, expected_answer='hidden',
                                     required_actions=(), unavailable_actions=())
            for policy in (joint, static):
                plan = policy.route(task)
                assert plan.actions == policy.route(hidden_changed).actions
                support = plan.actions[:-1]
                assert len(support) <= 3
                assert route_cost(support) <= budget + 1e-9


def test_outage_fallback_removes_failed_tool_without_using_hidden_health():
    task = next(task for task in generate_executable_tasks('challenge', 10)
                if task.kind == 'research_outage')
    policy = StaticFallbackPolicy()
    assert RouteAction.USE_TOOL not in policy.route(task).actions
    assert RouteAction.DELEGATE in policy.route(task).actions
    assert policy.route(task).actions == policy.route(replace(task, unavailable_actions=())).actions
    assert run_executable_benchmark([task], [policy])[0].success


def test_cost_ablation_keeps_action_cap_and_changes_binding_routes(controls):
    _, _, model = controls
    full = LearnedBudgetPolicy(model, threshold=0.4)
    unconstrained = LearnedBudgetPolicy(model, threshold=0.4, enforce_budget=False)
    tasks = [replace(task, cost_budget=1.75) for task in generate_executable_tasks('test', 36)]
    assert sum(full.route(task).actions != unconstrained.route(task).actions for task in tasks) == 40
    assert all(len(unconstrained.route(task).actions) <= 4 for task in tasks)


def test_one_family_gain_is_one_inferential_unit():
    tasks = generate_executable_tasks('test', 10)
    traces = run_executable_benchmark(tasks, [OraclePolicy(), StaticFallbackPolicy()])
    # Turn one whole family into a baseline loss; duplicating its instances must
    # not turn this single phenomenon into several significant independent wins.
    modified = [replace(trace, success=False) if trace.policy == 'static_outage_fallback'
                and trace.kind == 'research_outage' else trace for trace in traces]
    result = compare_executable_families(modified, 'oracle', 'static_outage_fallback')
    assert result['n_families'] == 11
    assert result['treatment_only_families'] == 1
    assert result['family_sign_p'] == 1.0
    with pytest.raises(ValueError, match='identical nonempty'):
        compare_executable_families(modified[1:], 'oracle', 'static_outage_fallback')
    with pytest.raises(ValueError, match='duplicate'):
        compare_executable_families(modified + modified[:1], 'oracle', 'static_outage_fallback')


def test_execution_inspector_records_real_prerequisite_states():
    from metarouter.executable_executor import inspect_execution
    from metarouter.models import RoutePlan
    task = next(task for task in generate_executable_tasks('test', 10)
                if task.kind == 'invoice_reconcile')
    result = inspect_execution(task, OraclePolicy().route(task))
    assert result['steps'][0]['candidate'] == str(task.payload['stated_total'])
    assert 'computed_total' not in result['steps'][0]['artifacts']
    assert result['steps'][1]['artifacts']['computed_total'] == sum(task.payload['items'])
    assert result['answer'] == task.expected_answer
    reversed_plan = RoutePlan(actions=(RouteAction.VERIFY, RouteAction.EXECUTE_CODE,
                                      RouteAction.USE_TOOL, RouteAction.ANSWER))
    assert inspect_execution(task, reversed_plan)['failure_mode'] == 'incorrect_answer'
