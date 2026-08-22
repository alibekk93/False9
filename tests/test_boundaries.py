from __future__ import annotations

import ast
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "src" / "false_nine" / "core"


def imported_modules(source: str) -> set[str]:
    """Every imported module in `source`, as its full dotted name."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module)
    return found


def core_modules() -> list[Path]:
    paths = sorted(CORE.rglob("*.py"))
    assert paths, f"no modules found under {CORE}"
    return paths


def test_core_imports_only_stdlib() -> None:
    for path in core_modules():
        for module in imported_modules(path.read_text(encoding="utf-8-sig")):
            if module.split(".")[0] == "false_nine":
                assert module.startswith("false_nine.core"), f"{path.name}: {module}"
            else:
                assert module.split(".")[0] in sys.stdlib_module_names, (
                    f"{path.name} imports non-stdlib: {module}"
                )


def test_checker_rejects_pygame() -> None:
    """The check above is only worth having if it catches the thing it names."""
    for source in ("import pygame\n", "from pygame.event import Event\n"):
        found = imported_modules(source)
        assert any(m.split(".")[0] == "pygame" for m in found)
        assert not any(m.split(".")[0] in sys.stdlib_module_names for m in found)


def test_random_is_confined_to_rng() -> None:
    for path in core_modules():
        tops = {
            m.split(".")[0]
            for m in imported_modules(path.read_text(encoding="utf-8-sig"))
        }
        assert ("random" in tops) == (path.name == "rng.py"), (
            f"{path.name} imports random"
        )
