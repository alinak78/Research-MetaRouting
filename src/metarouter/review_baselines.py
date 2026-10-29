"""Post-review controls; none uses task kind, answers, or route labels at inference."""

from __future__ import annotations

import itertools
import re

import numpy as np

from .executable_executor import ACTION_COST, execute_task
from .executable_models import ExecutablePolicy, ExecutableTask
from .models import RouteAction, RoutePlan, Workload
from .text_router import CalibratedTextOperationModel, SUPPORT_ACTIONS, StaticExecutablePolicy


def route_cost(actions: tuple[RouteAction, ...]) -> float:
    return sum(ACTION_COST[action] for action in actions) + ACTION_COST[RouteAction.ANSWER]


def feasible(actions: tuple[RouteAction, ...], budget: float, max_actions: int) -> bool:
    return len(actions) <= max_actions and route_cost(actions) <= budget + 1e-9


def support_subsets() -> list[tuple[RouteAction, ...]]:
    return [subset for size in range(6) for subset in itertools.combinations(SUPPORT_ACTIONS, size)]


def outage_in_prompt(prompt: str) -> bool:
    """Explicit health statements only; this is not observed execution failure."""
    return bool(re.search(r'\b(unavailable|offline|outage)\b|cannot be reached', prompt.lower()))


class StaticFallbackPolicy(StaticExecutablePolicy):
    name = 'static_outage_fallback'

    def route(self, task: ExecutableTask) -> RoutePlan:
        actions = tuple(action for action in super().route(task).actions if action != RouteAction.ANSWER)
        if outage_in_prompt(task.prompt):
            actions = tuple(action for action in SUPPORT_ACTIONS
                            if action in set(actions) - {RouteAction.USE_TOOL} or action == RouteAction.DELEGATE)
        return RoutePlan(actions=(*actions, RouteAction.ANSWER),
                         rationale='fixed workload route with explicit prompt-health fallback')


class FeasibleStaticPolicy(ExecutablePolicy):
    """Choose one dev-success-maximizing feasible route per workload/health stratum.

    Every candidate is executed on development tasks only. Ties prefer lower
    cost, then fewer operations. No per-task labels are available to route().
    """
    name = 'feasible_static_fallback'

    def __init__(self, dev_tasks: list[ExecutableTask], max_actions: int = 3) -> None:
        if not dev_tasks:
            raise ValueError('development tasks are required')
        self.dev_tasks = dev_tasks
        self.max_actions = max_actions
        self.cache: dict[tuple[Workload, bool, float], tuple[RouteAction, ...]] = {}
        self.scores: dict[tuple[Workload, bool], dict[tuple[RouteAction, ...], float]] = {}
        for workload in Workload:
            for outage in (False, True):
                tasks = [task for task in dev_tasks if task.workload == workload
                         and outage_in_prompt(task.prompt) == outage]
                if not tasks:
                    tasks = [task for task in dev_tasks if task.workload == workload]
                if not tasks:
                    raise ValueError(f'no development examples for {workload.value}')
                self.scores[workload, outage] = {
                    actions: sum(execute_task(task, RoutePlan(actions=(*actions, RouteAction.ANSWER)),
                                             self.name, 0.0, timing_repetitions=1).success
                                 for task in tasks) / len(tasks)
                    for actions in support_subsets()
                }

    def route(self, task: ExecutableTask) -> RoutePlan:
        key = task.workload, outage_in_prompt(task.prompt), task.cost_budget
        if key not in self.cache:
            scores = self.scores[key[:2]]
            candidates = [actions for actions in scores
                          if feasible(actions, task.cost_budget, self.max_actions)]
            if not candidates:
                raise ValueError('budget is below the mandatory answer cost')
            self.cache[key] = max(candidates, key=lambda actions:
                                  (scores[actions], -route_cost(actions), -len(actions)))
        return RoutePlan(actions=(*self.cache[key], RouteAction.ANSWER),
                         rationale='development-selected feasible workload/health route')


class CompleteRoutePolicy(ExecutablePolicy):
    """Multiclass logistic regression on full route labels and identical text features.

    Uses the operation model's train-only feature vocabulary, 500 gradient steps,
    learning-rate schedule, and L2 coefficient. Dev selects a softmax temperature.
    At inference, rank complete classes and select the highest-scoring feasible
    class, rather than reducing a predicted route to an arbitrary subset.
    """
    name = 'complete_route'

    def __init__(self, features: CalibratedTextOperationModel, max_actions: int = 3) -> None:
        self.features = features
        self.max_actions = max_actions
        self.routes: list[tuple[RouteAction, ...]] = []

    def _matrix(self, tasks: list[ExecutableTask]) -> np.ndarray:
        matrix = np.zeros((len(tasks), len(self.features.feature_index)))
        for row, task in enumerate(tasks):
            for feature in self.features._extract(task.prompt) & self.features.vocabulary:
                matrix[row, self.features.feature_index[feature]] = 1.0
        return matrix

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        values = np.exp(logits - logits.max(axis=-1, keepdims=True))
        return values / values.sum(axis=-1, keepdims=True)

    def fit(self, train: list[ExecutableTask], dev: list[ExecutableTask]) -> 'CompleteRoutePolicy':
        if not train or not dev:
            raise ValueError('training and development tasks are required')
        self.routes = sorted({task.required_actions for task in train},
                             key=lambda actions: tuple(action.value for action in actions))
        if () not in self.routes:
            raise ValueError('training must include the empty support route')
        targets = np.asarray([self.routes.index(task.required_actions) for task in train])
        matrix = self._matrix(train)
        self.weights = np.zeros((matrix.shape[1], len(self.routes)))
        self.bias = np.zeros(len(self.routes))
        labels = np.eye(len(self.routes))[targets]
        for epoch in range(500):
            errors = (self._softmax(matrix @ self.weights + self.bias) - labels) / len(train)
            rate = 0.35 / np.sqrt(1.0 + epoch / 50.0)
            self.weights -= rate * (matrix.T @ errors + 0.002 * self.weights)
            self.bias -= rate * errors.sum(axis=0)
        dev_logits = self._matrix(dev) @ self.weights + self.bias
        # Unknown development routes have zero target probability under every
        # temperature; a fixed penalty keeps this diagnostic well-defined.
        dev_targets = [self.routes.index(task.required_actions)
                       if task.required_actions in self.routes else None for task in dev]
        def loss(temperature: float) -> float:
            probabilities = self._softmax(dev_logits / temperature)
            return sum(-np.log(max(probabilities[i, target], 1e-12))
                       if target is not None else -np.log(1e-12)
                       for i, target in enumerate(dev_targets))
        self.temperature = min((0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0), key=loss)
        return self

    def route(self, task: ExecutableTask) -> RoutePlan:
        if not self.routes:
            raise ValueError('model must be fit before prediction')
        probabilities = self._softmax((self._matrix([task]) @ self.weights + self.bias)
                                      / self.temperature)[0]
        candidates = [index for index, actions in enumerate(self.routes)
                      if feasible(actions, task.cost_budget, self.max_actions)]
        if not candidates:
            raise ValueError('budget is below the mandatory answer cost')
        index = max(candidates, key=lambda i: (probabilities[i], -route_cost(self.routes[i])))
        return RoutePlan(actions=(*self.routes[index], RouteAction.ANSWER),
                         confidence=float(probabilities[index]),
                         rationale='highest-scoring feasible complete route class')
