from __future__ import annotations

import ast
import re
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "src" / "false_nine" / "core"

STATS = ("ability", "technique", "physical", "mental")

# 10 §4. The shapes a cheat would take. `min(...)` around a stat is a cap; a constant
# named for a maximum is a cap with a label on it; a flag consulted at the last moment
# is 03 §7.1's "invisible is_star = False". `max(...)` is deliberately absent — the
# floor in stats.STAT_FLOOR is a bound in the other direction and is not a ceiling.
SUSPICIOUS = (
    re.compile(r"\bmin\s*\([^)]*\b(" + "|".join(STATS) + r")\b"),
    re.compile(r"\b(MAX_|CAP_|LIMIT_)?(ABILITY|STAT)_(CAP|MAX|CEILING|LIMIT)\b"),
    re.compile(r"\bMAX_(ABILITY|TECHNIQUE|PHYSICAL|MENTAL)\b"),
    re.compile(r"\bis_star\b|\bstar_flag\b|\bis_elite\b"),
)

# Anything here has to carry a reason. Nothing does yet, and that is the point: if a
# line ever needs to go in, someone has to write down why it is not a cheat.
ALLOWLIST: dict[str, str] = {}


def core_files() -> list[Path]:
    files = sorted(CORE.rglob("*.py"))
    assert files, f"no modules found under {CORE}"
    return files


def code_lines(path: Path) -> list[tuple[int, str]]:
    """Comments and docstrings are where the rule is *explained*, so they are stripped
    before the scan — otherwise `# Ability has a floor, not a ceiling` would fail it."""
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    skip: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and id(node) in docstrings:
            skip.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return [
        (number, line.split("#", 1)[0])
        for number, line in enumerate(source.splitlines(), start=1)
        if number not in skip
    ]


def test_no_hidden_ceiling() -> None:
    """09 M4's acceptance. The design's one load-bearing promise is that the career
    ceiling is enforced by the world and never by a cap on a number the player is
    shown. This is the test that can catch it being broken."""
    for path in core_files():
        for number, line in code_lines(path):
            for pattern in SUSPICIOUS:
                hit = pattern.search(line)
                if not hit:
                    continue
                where = f"{path.name}:{number}"
                assert where in ALLOWLIST, (
                    f"{where} looks like a stat cap: {line.strip()!r}. "
                    "03 §7.1 forbids one. If it is not a cheat, say why in ALLOWLIST."
                )


def test_the_checker_catches_a_planted_cap(tmp_path: Path) -> None:
    """Guards the guard. A scan that matches nothing is indistinguishable from a scan
    that is broken, so it is pointed at the thing it exists to find."""
    planted = tmp_path / "cheat.py"
    planted.write_text(
        "MAX_ABILITY = 85.0\n"
        "def train(state):\n"
        "    return min(state.ability, MAX_ABILITY)\n",
        encoding="utf-8",
    )
    hits = [
        line
        for _, line in code_lines(planted)
        if any(pattern.search(line) for pattern in SUSPICIOUS)
    ]
    assert len(hits) == 2, hits


def test_the_checker_ignores_the_comments_that_explain_the_rule() -> None:
    """`stats.py` says "Ability has a floor and deliberately NO ceiling" in prose. A
    scan that failed on its own documentation would be deleted within a week."""
    stats = CORE / "stats.py"
    assert "no ceiling" in stats.read_text(encoding="utf-8-sig").lower()
    for _, line in code_lines(stats):
        assert not any(pattern.search(line) for pattern in SUSPICIOUS), line
