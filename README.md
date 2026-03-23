# Lab 4 — Regular Expression String Generator

**Course:** Formal Languages & Finite Automata  
**Author:** Iulian Pavlov  
**Variant:** 1

---

## Table of Contents

1. [Overview](#overview)
2. [Objectives](#objectives)
3. [Variant 1 Patterns](#variant-1-patterns)
4. [Project Structure](#project-structure)
5. [Implementation](#implementation)
6. [How It Works — Step by Step](#how-it-works--step-by-step)
7. [Testing](#testing)
8. [Challenges Encountered](#challenges-encountered)
9. [Conclusions](#conclusions)
10. [References](#references)

---

## Overview

This lab implements a **regular expression interpreter and string generator** — a program that reads a regex pattern as input, builds an Abstract Syntax Tree (AST) from it, and randomly generates valid strings that belong to the language described by that pattern.

The approach is fully dynamic — the pattern is interpreted at runtime, not hardcoded. Any pattern using the supported syntax will work without modifying the source code.

This sits naturally after the lexer built in Lab 3 in the compiler pipeline. Where the lexer tokenizes input, this lab focuses on the generative side: given a formal language definition (a regex), produce members of that language.

```
Pattern String  →  [Parser]  →  AST  →  [Generator]  →  Valid String
```

---

## Objectives

1. Understand how regular expressions define formal languages and how to represent them structurally.
2. Implement a recursive descent parser that converts a regex pattern into an AST.
3. Implement a generator that walks the AST and produces valid strings randomly.
4. Support all common regex quantifiers: `*`, `+`, `?`, `{n}`, and the assignment-specific `^n` notation.
5. Implement a step-by-step tracer that logs every decision made during generation.
6. Demonstrate the generator on all three Variant 1 patterns.

---

## Variant 1 Patterns

| # | Pattern | Example Outputs |
|---|---------|-----------------|
| 1 | `(a\|b)(c\|d)E+G?` | `acEEE`, `bdE`, `adEEG` |
| 2 | `P(Q\|R\|S)T(UV\|W\|X)*Z+` | `PQTUVUVZ`, `PRTWWWZ`, `PSTZ` |
| 3 | `1(0\|1)*2(3\|4){5}36` | `1023333336`, `124344436` |

---

## Project Structure

```
DSL_labs/
  nodes.py       —  AST node dataclasses (Literal, Alternation, Concatenation, Repetition)
  parser.py      —  RegexParser: pattern string → AST
  generator.py   —  RegexGenerator, RegexTracer, and convenience functions
  main.py        —  demo entry point
  README.md      —  this file
```

Dependency flow is strictly one-way:

```
main.py  →  parser.py  →  nodes.py
         →  generator.py  →  nodes.py
```

---

## Implementation

### `nodes.py` — AST Node Dataclasses

Defines the four node types that make up the AST. Each is a frozen dataclass, making nodes immutable and safe to inspect at any stage:

```python
@dataclass(frozen=True)
class Literal:
    char: str              # single character to emit

@dataclass(frozen=True)
class Alternation:
    options: list          # list of child nodes — pick one

@dataclass(frozen=True)
class Concatenation:
    parts: list            # list of child nodes — emit all in order

@dataclass(frozen=True)
class Repetition:
    child: object          # the node to repeat
    min_rep: int           # minimum repetitions
    max_rep: int           # maximum repetitions (capped at MAX_REPEAT for * and +)
```

### `parser.py` — RegexParser

The `RegexParser` class takes a pattern string and returns the root node of an AST. It uses **recursive descent** — each grammar rule is a method, and calls between methods encode precedence from lowest to highest:

```python
class RegexParser:
    def parse(self) -> Node:
        return self._alternation()

    def _alternation(self):   # lowest precedence  — handles (a|b|c)
        ...
    def _concatenation(self): # mid precedence     — handles abc
        ...
    def _quantified(self):    # high precedence    — handles a*, a+, a?, a{n}, a^n
        ...
    def _atom(self):          # highest precedence — handles literals and (groups)
        ...
```

Precedence is implicit in the call chain:

```
_alternation → _concatenation → _quantified → _atom
```

### `generator.py` — RegexGenerator and RegexTracer

Contains two classes and two convenience functions.

**`RegexGenerator`** walks the AST recursively and produces a string:

```python
class RegexGenerator:
    def generate(self, node) -> str:
        if isinstance(node, Literal):
            return node.char
        if isinstance(node, Alternation):
            return self.generate(random.choice(node.options))
        if isinstance(node, Concatenation):
            return "".join(self.generate(p) for p in node.parts)
        if isinstance(node, Repetition):
            n = random.randint(node.min_rep, node.max_rep)
            return "".join(self.generate(node.child) for _ in range(n))
```

**`RegexTracer`** mirrors the generator but appends a log entry at every step, producing a human-readable trace of all decisions made.

**Convenience functions** exposed at module level:

```python
generate_string(pattern, seed=None) -> str
generate_with_trace(pattern, seed=None) -> tuple[str, list[str]]
```

### `main.py` — Demo Entry Point

Runs the generator on all three Variant 1 patterns and prints 6 sample outputs per pattern:

```
============================================================
  Lab 4 — Variant 1  |  Regular Expression Generator
============================================================

Pattern : (a|b)(c|d)E+G?
Samples : ['acEEE', 'acE', 'bcE', 'acEEEEE', 'adEEG', 'bcEEG']

Pattern : P(Q|R|S)T(UV|W|X)*Z+
Samples : ['PRTUVUVZZZ', 'PQTZZZZ', 'PQTWXZZZ', ...]

Pattern : 1(0|1)*2(3|4){5}36
Samples : ['11124434336', '124433436', '10101124334436', ...]
```

---

## How It Works — Step by Step

Consider pattern `(a|b)(c|d)E+G?` with seed `7`.

The parser builds this AST:

```
Concatenation
├── Alternation ['a', 'b']
├── Alternation ['c', 'd']
├── Repetition(min=1, max=5)
│   └── Literal 'E'
└── Repetition(min=0, max=1)
    └── Literal 'G'
```

The generator then walks it:

| Step | Node | Decision | Output so far |
|------|------|----------|---------------|
| 1 | Concatenation of 4 parts | recurse into each part | — |
| 2 | Alternation `[a, b]` | chose option 2 → `b` | `b` |
| 3 | Alternation `[c, d]` | chose option 1 → `c` | `bc` |
| 4 | Repetition `[1..5]` | chose 3 repeats | — |
| 5 | Literal `E` × 3 | emit `E` three times | `bcEEE` |
| 6 | Repetition `[0..1]` | chose 1 repeat | — |
| 7 | Literal `G` × 1 | emit `G` | `bcEEEG` |

Final result: **`bcEEEG`**

### Tracer output for the same run

```
Step  1: Concatenation of 4 parts
Step  2: Alternation — chose option 2 of 2
Step  3: Emit literal 'b'
Step  4: Alternation — chose option 1 of 2
Step  5: Emit literal 'c'
Step  6: Repetition [1..5] — chose 3 repeat(s)
Step  7: Emit literal 'E'
Step  8: Emit literal 'E'
Step  9: Emit literal 'E'
Step 10: Repetition [0..1] — chose 1 repeat(s)
Step 11: Emit literal 'G'
```

### Pattern 3 — `1(0|1)*2(3|4){5}36`

This pattern exercises both unbounded (`*`) and exact-count (`{5}`) repetition. The `{5}` quantifier always produces exactly 5 characters from the alternation — never more, never fewer. A sample run:

```
1        — Literal
01       — (0|1)* chose 2 repeats → '0', '1'
2        — Literal
43434    — (3|4){5} chose exactly 5 → '4','3','4','3','4'
3        — Literal
6        — Literal

Result: 101243434 36  →  10124343436
```

---

## Testing

The generator can be verified by running each pattern with a fixed seed and asserting the output is deterministic and structurally valid:

```python
from generator import generate_string

# Deterministic — same seed always gives same output
assert generate_string("(a|b)(c|d)E+G?", seed=0) == generate_string("(a|b)(c|d)E+G?", seed=0)

# Pattern 2 always starts with P and ends with at least one Z
result = generate_string("P(Q|R|S)T(UV|W|X)*Z+", seed=1)
assert result.startswith("P")
assert result.endswith("Z")

# Pattern 3 always ends with 36
result = generate_string("1(0|1)*2(3|4){5}36", seed=5)
assert result.endswith("36")
```

Run all tests:

```bash
python -m unittest discover tests/ -v
```

---

## Challenges Encountered

### Challenge 1 — Operator precedence in the parser

The initial implementation parsed `ab|cd` as `a(b|c)d` instead of `(ab)|(cd)` because alternation and concatenation were handled at the same level without any precedence distinction.

**Fix:** Encode precedence strictly in the call chain. `_alternation` calls `_concatenation`, which calls `_quantified`, which calls `_atom`. Each level can only consume constructs at its own precedence or higher. This mirrors how arithmetic parsers handle `+` vs `*`.

### Challenge 2 — Superscript `^n` notation

The assignment uses `(3|4)^5` to mean "exactly 5 repetitions". Standard regex engines treat `^` as a start-of-line anchor, so there was no existing convention to follow.

**Fix:** In `_quantified()`, after parsing an atom, peek at the next character. If it is `^` followed by one or more digits, consume both and return `Repetition(node, n, n)` — identical to `{n}`. This keeps the parser self-consistent without affecting any other rule.

### Challenge 3 — Preventing infinite-length output

The `*` quantifier allows zero or more repetitions with no upper bound. Left uncapped, a pattern like `a*` could generate a string of thousands of characters.

**Fix:** Introduce a `MAX_REPEAT = 5` constant. At parse time, any `*` or `+` quantifier sets `max_rep = MAX_REPEAT`. The cap is stored in the AST node itself — visible, inspectable, and changeable in one place — rather than being applied as a hidden check at generation time.

---

## Conclusions

This lab produced a working regex-to-string generator built around a clean recursive descent parser and an AST-walking generator. Key takeaways:

- **Recursive descent maps directly to grammar:** each rule becomes a method, making the parser easy to read, extend, and debug without any external parser library.
- **AST separation of concerns:** parsing and generation are completely independent. The parser knows nothing about randomness; the generator knows nothing about syntax. Either half can be replaced or extended without touching the other.
- **Determinism via seeding:** passing a seed to `random` makes the output fully reproducible, which is essential for debugging and testing a program whose output is otherwise random by design.
- **Tracing as a first-class feature:** implementing `RegexTracer` alongside `RegexGenerator` required almost no extra code and makes the entire generation process fully transparent.

The broader lesson is that the same tree-walking pattern used in interpreters and compilers — build a structured representation first, then traverse it — scales naturally from evaluating expressions all the way to generating strings from formal language definitions.

---

## References

- Course materials: Formal Languages & Finite Automata
- [Wikipedia: Regular Expression](https://en.wikipedia.org/wiki/Regular_expression)
- [Wikipedia: Recursive Descent Parser](https://en.wikipedia.org/wiki/Recursive_descent_parser)
- [Wikipedia: Abstract Syntax Tree](https://en.wikipedia.org/wiki/Abstract_syntax_tree)
