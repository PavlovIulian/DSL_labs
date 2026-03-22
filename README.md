# Lab 4 — Regular Expression String Generator

**Course:** Formal Languages & Finite Automata  
**Author:** Iulian Pavlov  
**Variant:** 1

---

## Overview

This lab implements a **regular expression interpreter and string generator**.
Given a regex pattern as input, the program parses it into an Abstract Syntax Tree
(AST) and randomly generates valid strings that belong to the language described
by that pattern.

The approach is fully dynamic — the pattern is interpreted at runtime, not
hardcoded. Any pattern using the supported syntax will work.

---

## Variant 1 Patterns

| # | Pattern | Example outputs |
|---|---------|-----------------|
| 1 | `(a\|b)(c\|d)E+G?` | `acEEE`, `bdE`, `adEEG` |
| 2 | `P(Q\|R\|S)T(UV\|W\|X)*Z+` | `PQTUVUVZ`, `PRTWWWZ`, `PSTZ` |
| 3 | `1(0\|1)*2(3\|4){5}36` | `1023333336`, `124344436` |

---

## Project Structure

```
nodes.py       — AST node dataclasses (Literal, Alternation, Concatenation, Repetition)
parser.py      — RegexParser: pattern string → AST
generator.py   — RegexGenerator, RegexTracer, and convenience functions
main.py        — demo entry point
README.md      — this file
```

Each file has a single responsibility and the dependency flow is strictly one-way:

```
main.py  →  parser.py  →  nodes.py
         →  generator.py  →  nodes.py
```

---

## How It Works

### 1. Parsing → AST

The `RegexParser` class uses **recursive descent** to convert a pattern string
into a tree of four node types:

```
Literal       — a single character  →  emit it verbatim
Alternation   — (a|b|c)            →  pick one branch randomly
Concatenation — abc                →  emit all parts in sequence
Repetition    — a*, a+, a?, a{n}   →  repeat child node N times
```

Precedence is encoded in the call chain (low → high):

```
_alternation → _concatenation → _quantified → _atom
```

### 2. Generation → string

The `RegexGenerator` walks the AST recursively:
- **Literal** → return the character
- **Alternation** → `random.choice()` among options, recurse
- **Concatenation** → recurse on each item, join results
- **Repetition** → `random.randint(min, max)`, recurse that many times

Unbounded quantifiers (`*` and `+`) are capped at **5 repetitions**
to prevent extremely long output.

### 3. Tracing → step log (bonus)

The `RegexTracer` class mirrors the generator but logs every decision:

```
Step  1: Concatenation of 4 parts
Step  2: Alternation — chose option 2 of 2
Step  3: Emit literal 'b'
Step  6: Repetition [1..5] — chose 4 repeat(s)
...
```

---

## Supported Syntax

| Syntax | Meaning | Example |
|--------|---------|---------|
| `a` | Literal character | `a` matches `a` |
| `(a\|b)` | Alternation — pick one | `(x\|y\|z)` |
| `ab` | Concatenation — both in order | `PQ` |
| `a*` | Zero or more (max 5) | `E*` |
| `a+` | One or more (max 5) | `Z+` |
| `a?` | Zero or one | `G?` |
| `a{n}` | Exactly n times | `(3\|4){5}` |
| `a^n` | Exactly n times (assignment notation) | `(3\|4)^5` |

---

## Usage

### Run the built-in demo

```bash
python main.py
```

Output:
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

### Use as a module

```python
from regex_generator import generate_string, generate_with_trace

# Generate one string
s = generate_string("(a|b)(c|d)E+G?")
print(s)   # e.g. 'adEEG'

# Generate with a fixed seed for reproducibility
s = generate_string("P(Q|R|S)T(UV|W|X)*Z+", seed=42)
print(s)   # always the same string

# Generate with a step-by-step trace
result, steps = generate_with_trace("(a|b)(c|d)E+G?", seed=7)
print(result)
for step in steps:
    print(step)
```

---

## Implementation Notes

### Why a custom parser instead of Python's `re` module?

Python's `re` module can *match* strings against patterns but cannot *generate*
strings from them. Building the AST ourselves gives full control over the
generation process and makes the step tracer possible.

### Naming: `Repetition.max_rep` vs actual cap

The `max_rep` field stores the parsed upper bound. For `*` and `+` this is set
to `MAX_REPEAT` (5) at parse time. For `{n}` and `^n` it stores the exact
count `n`. The generator always calls `random.randint(min_rep, max_rep)`, so
`{5}` always produces exactly 5 and `*` produces 0–5.

### Superscript notation `^n`

The assignment uses `(3|4)^5` to mean "exactly 5 repetitions". Standard regex
engines treat `^` as a start-of-line anchor. The parser handles this by
detecting `^` followed by digits in the quantifier position and mapping it to
`Repetition(node, n, n)`, identical to `{n}`.

---

## Requirements

- Python 3.7+
- No external dependencies (standard library only)
