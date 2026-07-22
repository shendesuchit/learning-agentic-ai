"""A no-network check that all teaching examples parse as Python."""

import ast
from pathlib import Path


def test_examples_parse() -> None:
    examples = Path(__file__).parents[1] / "examples"
    for example in examples.glob("*.py"):
        ast.parse(example.read_text(encoding="utf-8"), filename=str(example))
