from __future__ import annotations

from false_nine.core.rng import Rng


def test_stream_value_is_pinned() -> None:
    """Pinned so a switch to the salted builtin `hash()` fails here rather than
    silently voiding every stored (seed, action_log) pair."""
    assert Rng("seed").stream("match", 1).random() == 0.1893978258183554


def test_same_seed_reproduces() -> None:
    a = [Rng("s").stream("injury", w).random() for w in range(20)]
    b = [Rng("s").stream("injury", w).random() for w in range(20)]
    assert a == b


def test_different_seeds_diverge() -> None:
    a = [Rng("s1").stream("injury", w).random() for w in range(20)]
    b = [Rng("s2").stream("injury", w).random() for w in range(20)]
    assert a != b


def test_repeated_calls_advance_the_stream() -> None:
    stream = Rng("s").stream("injury", 3)
    assert stream.random() != stream.random()


def test_streams_are_independent() -> None:
    """Adding a call site in one system must not shift results in another."""
    plain = Rng("s")
    noisy = Rng("s")
    for _ in range(5):
        noisy.stream("match", 1).random()
    assert plain.stream("injury", 1).random() == noisy.stream("injury", 1).random()


def test_name_and_key_both_matter() -> None:
    rng = Rng("s")
    assert rng.stream("match", 1).random() != rng.stream("injury", 1).random()
    assert Rng("s").stream("match", 1).random() != Rng("s").stream("match", 2).random()
