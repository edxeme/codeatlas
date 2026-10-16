"""Cyclomatic complexity, counted directly from the AST.

One point per branch a function owns: ``if``/``for``/``while``, ``except``
handlers, ternary ``if`` expressions, ``assert`` statements, boolean
operators (``a and b and c`` adds two), comprehension clauses and their
filters, and ``match`` cases.

Nested functions and lambdas are scored *separately* — their decisions
belong to their own scope, not to the enclosing function.
"""

from __future__ import annotations

import ast

_BRANCHES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.IfExp,
    ast.Assert,
    ast.ExceptHandler,
)

# Scopes whose decisions are scored as their own functions.
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def _own_nodes(node: ast.AST):
    """Yield descendants of *node* without crossing into nested scopes."""
    stack = list(ast.iter_child_nodes(node))
    while stack:
        current = stack.pop()
        if isinstance(current, _SCOPES):
            continue
        yield current
        stack.extend(ast.iter_child_nodes(current))


def cyclomatic_complexity(node: ast.AST) -> int:
    """Cyclomatic complexity of one function body, nested scopes excluded."""
    score = 1
    for child in _own_nodes(node):
        if isinstance(child, _BRANCHES):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            score += 1 + len(child.ifs)
        elif isinstance(child, ast.match_case):
            score += 1
    return score
