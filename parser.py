from typing import Optional

from nodes import Alternation, Concatenation, Literal, MAX_REPEAT, Repetition


class RegexParser:

    def __init__(self, pattern: str):
        self.src = pattern
        self.pos = 0

    # ── Low-level helpers ─────────────────────────────────────────

    def peek(self) -> Optional[str]:
        return self.src[self.pos] if self.pos < len(self.src) else None

    def consume(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        return ch

    def consume_int(self) -> int:
        digits = ""
        while self.peek() and self.peek().isdigit():
            digits += self.consume()
        return int(digits)

    # ── Grammar rules ─────────────────────────────────────────────

    def parse(self):
        return self._alternation()

    def _alternation(self):
        options = [self._concatenation()]
        while self.peek() == '|':
            self.consume()
            options.append(self._concatenation())
        return options[0] if len(options) == 1 else Alternation(options)

    def _concatenation(self):
        items = []
        while self.peek() not in (None, '|', ')'):
            items.append(self._quantified())
        return items[0] if len(items) == 1 else Concatenation(items)

    def _quantified(self):
        node = self._atom()
        q = self.peek()

        if q == '*':
            self.consume()
            return Repetition(node, 0, MAX_REPEAT)

        if q == '+':
            self.consume()
            return Repetition(node, 1, MAX_REPEAT)

        if q == '?':
            self.consume()
            return Repetition(node, 0, 1)

        if q == '{':
            self.consume()          # '{'
            n = self.consume_int()
            self.consume()          # '}'
            return Repetition(node, n, n)

        if q == '^':
            # Superscript notation used in the assignment: (a|b)^3 == (a|b){3}
            self.consume()          # '^'
            n = self.consume_int()
            return Repetition(node, n, n)

        return node

    def _atom(self):
        """atom ::= '(' expr ')' | CHAR"""
        if self.peek() == '(':
            self.consume()          # '('
            node = self._alternation()
            self.consume()          # ')'
            return node
        return Literal(self.consume())
