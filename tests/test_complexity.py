"""Complexity scoring tests with exact, hand-computed expectations."""

import ast

from codeatlas.complexity import cyclomatic_complexity


def cx(source: str) -> int:
    return cyclomatic_complexity(ast.parse(source).body[0])


def test_flat_function_scores_one():
    assert cx("def f():\n    return 1") == 1


def test_each_branch_adds_one():
    assert cx("def f(x):\n    if x:\n        return 1\n    return 0") == 2


def test_boolop_counts_operators():
    # a and b and c -> two operators -> 1 + 2
    assert cx("def f(a, b, c):\n    return a and b and c") == 3


def test_comprehension_and_its_filters():
    # base 1 + comprehension 1 + two filters 2
    assert cx("def f(xs):\n    return [x for x in xs if x if x > 2]") == 4


def test_except_handler_counts():
    assert cx("def f():\n    try:\n        pass\n    except ValueError:\n        pass") == 2


def test_match_cases_count():
    source = (
        "def f(x):\n"
        "    match x:\n"
        "        case 1:\n"
        "            pass\n"
        "        case 2:\n"
        "            pass"
    )
    assert cx(source) == 3


def test_ternary_counts():
    assert cx("def f(x):\n    return 1 if x else 0") == 2


def test_nested_functions_score_separately():
    source = (
        "def outer(xs):\n"
        "    def inner(x):\n"
        "        if x:\n"
        "            return 1\n"
        "        return 0\n"
        "    return [inner(x) for x in xs]"
    )
    tree = ast.parse(source)
    outer = tree.body[0]
    inner = outer.body[0]

    # outer owns only the comprehension; the if belongs to inner
    assert cyclomatic_complexity(outer) == 2
    assert cyclomatic_complexity(inner) == 2


def test_lambda_decisions_do_not_leak_into_enclosing_scope():
    source = "def f(xs):\n    g = lambda x: x if x else 0\n    return [g(x) for x in xs]"
    assert cx(source) == 2  # comprehension only; the ternary belongs to the lambda
