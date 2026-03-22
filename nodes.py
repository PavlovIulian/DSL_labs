from dataclasses import dataclass
from typing import Any, List


# Maximum repetitions produced for unbounded quantifiers (* and +).
# Prevents infinitely long output while still covering all structural cases.
MAX_REPEAT = 5


@dataclass
class Literal:
    """A single character to be emitted verbatim."""
    char: str


@dataclass
class Alternation:
    """Choose exactly one option at random."""
    options: List[Any]  # list of child nodes


@dataclass
class Concatenation:
    """Emit every item in sequence."""
    items: List[Any]  # list of child nodes


@dataclass
class Repetition:
    """Repeat the child node between min_rep and max_rep times (inclusive)."""
    node: Any
    min_rep: int
    max_rep: int  # for * and + this is set to MAX_REPEAT at parse time
