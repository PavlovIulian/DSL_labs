import random
from typing import List, Optional, Tuple

from nodes import Alternation, Concatenation, Literal, Repetition


class RegexGenerator:

    def generate(self, node) -> str:
        if isinstance(node, Literal):
            return node.char

        if isinstance(node, Alternation):
            return self.generate(random.choice(node.options))

        if isinstance(node, Concatenation):
            return "".join(self.generate(item) for item in node.items)

        if isinstance(node, Repetition):
            count = random.randint(node.min_rep, node.max_rep)
            return "".join(self.generate(node.node) for _ in range(count))

        raise TypeError(f"Unknown AST node: {type(node)}")


class RegexTracer:

    def __init__(self):
        self.steps: List[str] = []
        self._n = 0

    def _log(self, msg: str):
        self._n += 1
        self.steps.append(f"  Step {self._n:2d}: {msg}")

    def generate(self, node) -> str:
        if isinstance(node, Literal):
            self._log(f"Emit literal '{node.char}'")
            return node.char

        if isinstance(node, Alternation):
            chosen = random.choice(node.options)
            idx = node.options.index(chosen) + 1
            self._log(f"Alternation — chose option {idx} of {len(node.options)}")
            return self.generate(chosen)

        if isinstance(node, Concatenation):
            self._log(f"Concatenation of {len(node.items)} parts")
            return "".join(self.generate(item) for item in node.items)

        if isinstance(node, Repetition):
            count = random.randint(node.min_rep, node.max_rep)
            self._log(
                f"Repetition [{node.min_rep}..{node.max_rep}]"
                f" — chose {count} repeat(s)"
            )
            return "".join(self.generate(node.node) for _ in range(count))

        raise TypeError(f"Unknown AST node: {type(node)}")


# ─────────────────────────────────────────────────────────────────
# Module-level convenience functions
# ─────────────────────────────────────────────────────────────────

def generate_string(ast, seed: Optional[int] = None) -> str:
    """Generate one random string from a pre-parsed AST."""
    if seed is not None:
        random.seed(seed)
    return RegexGenerator().generate(ast)


def generate_with_trace(ast, seed: Optional[int] = None) -> Tuple[str, List[str]]:

    if seed is not None:
        random.seed(seed)
    tracer = RegexTracer()
    result = tracer.generate(ast)
    return result, tracer.steps
