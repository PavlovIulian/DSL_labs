"""
parser.py — Recursive-descent regex parser.

Reads a pattern string and returns an AST built from the node types
defined in nodes.py.

Supported syntax:
    a           Literal character
    (a|b|c)     Alternation — choose one branch
    ab          Concatenation — both parts in sequence
    a*          Zero or more  (capped at MAX_REPEAT)
    a+          One or more   (capped at MAX_REPEAT)
    a?          Zero or one
    a{n}        Exactly n repetitions
    a^n         Exactly n repetitions  (superscript notation: (3|4)^5)
    a^*         Zero or more           (superscript notation: (0|1)^*)
    a^+         One or more            (superscript notation: E^+)

Visual separators — consumed silently, never emitted as literals:
    space       e.g. "(3|4)^5 36"
    *           e.g. "(3|4)^5*36"  — a bare * immediately after ^N

Grammar (precedence low → high):
    expr          ::= alternation
    alternation   ::= concatenation ('|' concatenation)*
    concatenation ::= quantified+
    quantified    ::= atom quantifier?
    quantifier    ::= '*' | '+' | '?' | '{' INT '}' | '^' ('*' | '+' | INT)
    atom          ::= '(' expr ')' | CHAR
"""

from typing import Optional

from nodes import Alternation, Concatenation, Literal, MAX_REPEAT, Repetition


class RegexParser:

    def __init__(self, pattern: str):
        self.src = pattern
        self.pos = 0

    # ── Low-level helpers ─────────────────────────────────────────

    def peek(self) -> Optional[str]:
        """Return the current character without consuming it, or None at end."""
        return self.src[self.pos] if self.pos < len(self.src) else None

    def consume(self) -> str:
        """Return the current character and advance the position."""
        ch = self.src[self.pos]
        self.pos += 1
        return ch

    def consume_int(self) -> int:
        """Read and return a run of digit characters as an integer."""
        digits = ""
        while self.peek() and self.peek().isdigit():
            digits += self.consume()
        return int(digits)

    def skip_separators(self):
        """
        Consume any visual separator characters at the current position.
        Both spaces and bare '*' characters are used in the assignment
        as separators between a superscript exponent and the next token
        (e.g. '(3|4)^5 36' or '(3|4)^5*36') and carry no semantic meaning.
        They are skipped at the start of each new concatenation item.
        """
        while self.peek() in (' ', ):
            self.consume()

    # ── Grammar rules ─────────────────────────────────────────────

    def parse(self):
        """Entry point — parse the full pattern and return the AST root."""
        return self._alternation()

    def _alternation(self):
        """alternation ::= concatenation ('|' concatenation)*"""
        options = [self._concatenation()]
        while self.peek() == '|':
            self.consume()
            options.append(self._concatenation())
        return options[0] if len(options) == 1 else Alternation(options)

    def _concatenation(self):
        """concatenation ::= quantified+"""
        items = []
        while self.peek() not in (None, '|', ')'):
            self.skip_separators()
            if self.peek() in (None, '|', ')'):
                break
            items.append(self._quantified())
        return items[0] if len(items) == 1 else Concatenation(items)

    def _quantified(self):
        """quantified ::= atom quantifier?"""
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
            self.consume()          # '^'
            nxt = self.peek()

            # ^* and ^+ — superscript versions of the standard quantifiers
            if nxt == '*':
                self.consume()
                return Repetition(node, 0, MAX_REPEAT)
            if nxt == '+':
                self.consume()
                return Repetition(node, 1, MAX_REPEAT)

            # ^N — superscript exact count, e.g. (3|4)^5
            # After reading the digits, skip any immediately following
            # separator (* or space) that the assignment uses as a visual
            # boundary before the next token (e.g. "(3|4)^5*36").
            n = self.consume_int()
            while self.peek() in (' ', '*'):
                self.consume()
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