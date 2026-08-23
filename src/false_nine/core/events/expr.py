from __future__ import annotations

import operator
from collections.abc import Callable, Mapping, Sequence
from typing import Any

# 05 §5. Deliberately tiny: no arithmetic, no variables, no function calls. If a
# condition wants one of those, GameState gains a named property and the JSON
# references that instead. See 04's note on not adding a scripting language.
_COMPARE: dict[str, Callable[[Any, Any], bool]] = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "in": lambda left, right: left in right,
    "not_in": lambda left, right: left not in right,
    "contains": lambda left, right: right in left,
    "not_contains": lambda left, right: right not in left,
}
OPS = frozenset(_COMPARE)
LEAF_KEYS = frozenset({"path", "op", "value"})

Expr = Mapping[str, Any]


class ExprError(ValueError):
    """Raised at load time, never at week 94. 05 §5: a typo in a path is a startup
    error and not a silent False."""


def evaluate(node: Expr, state: object) -> bool:
    """`validate` has already run over every authored expression, so this trusts its
    input and stays the shape of the language rather than a parser."""
    if "all" in node:
        return all(evaluate(child, state) for child in node["all"])
    if "any" in node:
        return any(evaluate(child, state) for child in node["any"])
    if "not" in node:
        return not evaluate(node["not"], state)
    return _COMPARE[node["op"]](resolve(node["path"], state), node["value"])


def resolve(path: str, state: object) -> Any:
    """A dotted accessor. Mappings are indexed and everything else is an attribute,
    so `relationships.npc_agent.trust` walks a dict and then a Bond."""
    value: Any = state
    for segment in path.split("."):
        value = (
            value[segment] if isinstance(value, Mapping) else getattr(value, segment)
        )
    return value


def validate(node: Any, probe: object, where: str) -> None:
    """Walk an authored expression against a real GameState. `probe` carries the
    starting bonds, which is what makes a relationship path checkable at all — the
    npc ids live in `data/` and no dataclass field names them."""
    if not isinstance(node, Mapping):
        raise ExprError(f"{where}: expression must be an object, got {node!r}")

    keys = set(node)
    for combiner in ("all", "any"):
        if combiner in keys:
            _only(keys, combiner, where)
            children = node[combiner]
            if not isinstance(children, Sequence) or isinstance(children, str):
                raise ExprError(f"{where}: {combiner} takes a list")
            if not children:
                raise ExprError(f"{where}: {combiner} is empty")
            for child in children:
                validate(child, probe, where)
            return
    if "not" in keys:
        _only(keys, "not", where)
        validate(node["not"], probe, where)
        return

    if keys != LEAF_KEYS:
        raise ExprError(
            f"{where}: leaf keys are {sorted(keys)}, not {sorted(LEAF_KEYS)}"
        )
    if node["op"] not in OPS:
        raise ExprError(f"{where}: unknown op {node['op']!r}")
    try:
        resolve(node["path"], probe)
    except (AttributeError, KeyError, TypeError) as exc:
        raise ExprError(f"{where}: bad path {node['path']!r}") from exc


def _only(keys: set[str], combiner: str, where: str) -> None:
    if keys != {combiner}:
        raise ExprError(f"{where}: {combiner} takes no other keys, got {sorted(keys)}")
