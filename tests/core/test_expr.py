from __future__ import annotations

import pytest

from false_nine.core.events import expr
from false_nine.core.state import Bond, GameState

PROBE = GameState(seed="t", relationships={"npc_agent": Bond(trust=40.0)})


def leaf(path: str, op: str, value: object) -> dict[str, object]:
    return {"path": path, "op": op, "value": value}


def test_every_op_in_the_table_evaluates() -> None:
    """05 §5 names ten. If one were missing, an authored condition using it would
    raise a KeyError in the middle of a week rather than fail validation."""
    assert expr.OPS == {
        "==",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        "in",
        "not_in",
        "contains",
        "not_contains",
    }


@pytest.mark.parametrize(
    ("op", "value", "expected"),
    [
        (">=", 27.0, True),
        (">=", 99.0, False),
        ("<", 99.0, True),
        ("==", PROBE.ability, True),
        ("!=", PROBE.ability, False),
    ],
)
def test_leaf_comparisons(op: str, value: object, expected: bool) -> None:
    assert expr.evaluate(leaf("ability", op, value), PROBE) is expected


def test_paths_walk_dicts_and_dataclasses() -> None:
    """`relationships.npc_agent.trust` indexes a mapping and then reads an attribute.
    Nothing else in the language needs two kinds of step in one path."""
    assert expr.resolve("relationships.npc_agent.trust", PROBE) == 40.0


def test_membership_ops_read_flags() -> None:
    flagged = GameState(seed="t", flags=("asked_about_wages",))
    assert expr.evaluate(leaf("flags", "contains", "asked_about_wages"), flagged)
    assert expr.evaluate(leaf("flags", "not_contains", "left_football"), flagged)


def test_combiners_nest() -> None:
    node = {
        "all": [
            leaf("ability", ">=", 10),
            {"any": [leaf("form", ">=", 999), leaf("week_index", "==", 1)]},
            {"not": leaf("is_injured", "==", True)},
        ]
    }
    assert expr.evaluate(node, PROBE)


@pytest.mark.parametrize(
    "node",
    [
        {"path": "nonsense", "op": ">=", "value": 1},
        {"path": "relationships.npc_nobody.trust", "op": ">=", "value": 1},
        {"path": "ability", "op": "=~", "value": 1},
        {"path": "ability", "op": ">=", "value": 1, "extra": 2},
        {"all": []},
        {"all": [leaf("ability", ">=", 1)], "any": [leaf("form", ">=", 1)]},
        "not an object",
    ],
)
def test_validate_rejects(node: object) -> None:
    """05 §5: a typo in a path is a startup error, not a silent False. Each of these
    would otherwise evaluate to something rather than fail."""
    with pytest.raises(expr.ExprError):
        expr.validate(node, PROBE, "where")


def test_validate_accepts_what_evaluate_can_run() -> None:
    node = {"all": [leaf("relationships.npc_agent.trust", ">=", 20)]}
    expr.validate(node, PROBE, "where")
    assert expr.evaluate(node, PROBE)
