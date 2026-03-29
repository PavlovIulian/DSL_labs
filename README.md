# Lab 4 — Regular Expression String Generator

**Course:** Formal Languages & Finite Automata  
**Author:** Iulian Pavlov  
**Variant:** 1

---

## Variant 1 Patterns

| # | Pattern | Example outputs |
|---|---------|-----------------|
| 1 | `(a\|b)(c\|d)E^+G?` | `acEEE`, `bdE`, `adEEG` |
| 2 | `P(Q\|R\|S)T(UV\|W\|X)^*Z^+` | `PQTUVUVZ`, `PRTWWWZ`, `PSTZ` |
| 3 | `1(0\|1)^*2(3\|4)^5*36` | `1023333336`, `124344436` |

> **Notation note:** `^+` and `^*` are superscript quantifiers meaning one-or-more and zero-or-more.
> `^5` means exactly 5 repetitions. The `*` in `(3|4)^5*36` is a visual separator — not a quantifier.

---

## Project Structure

```
nodes.py       — AST node dataclasses (Literal, Alternation, Concatenation, Repetition)
parser.py      — RegexParser: pattern string → AST
generator.py   — RegexGenerator, RegexTracer, and convenience functions
main.py        — demo entry point
README.md      — this file
```

Dependency flow is strictly one-way:

```
main.py  →  parser.py    →  nodes.py
         →  generator.py →  nodes.py
```

---

## How It Works

### 1. Parsing → AST

`RegexParser` uses **recursive descent**. The call chain encodes precedence (low → high):

```
_alternation → _concatenation → _quantified → _atom
```

Each grammar rule is one method. Precedence is implicit in which method calls which — no priority table needed.

For example, `(a|b)(c|d)E^+G?` produces:

```
Concatenation
├── Alternation ['a', 'b']
├── Alternation ['c', 'd']
├── Repetition [1..5]        ← E^+
│   └── Literal 'E'
└── Repetition [0..1]        ← G?
    └── Literal 'G'
```

And `1(0|1)^*2(3|4)^5*36` produces:

```
Concatenation
├── Literal '1'
├── Repetition [0..5]        ← (0|1)^*
│   └── Alternation ['0', '1']
├── Literal '2'
├── Repetition [5..5]        ← (3|4)^5
│   └── Alternation ['3', '4']
├── Literal '3'              ← the '36' suffix
└── Literal '6'
```

### 2. Generation → string

`RegexGenerator` walks the AST with a single recursive method:

- **Literal** → return the character
- **Alternation** → `random.choice()` among options, recurse
- **Concatenation** → recurse on each item, join results
- **Repetition** → `random.randint(min, max)`, recurse that many times

Unbounded quantifiers (`^*` and `^+`) are capped at **MAX_REPEAT = 5**.

### 3. Tracing → step log (bonus)

`RegexTracer` mirrors the generator exactly but logs every decision:

```
Step  1: Concatenation of 4 parts
Step  2: Alternation — chose option 2 of 2
Step  3: Emit literal 'b'
Step  4: Alternation — chose option 1 of 2
Step  5: Emit literal 'c'
Step  6: Repetition [1..5] — chose 4 repeat(s)
Step  7: Emit literal 'E'
...
```

---

## Supported Syntax

| Syntax | Meaning | Example |
|--------|---------|---------|
| `a` | Literal character | `P`, `3`, `Z` |
| `(a\|b\|c)` | Alternation — pick one | `(Q\|R\|S)` |
| `ab` | Concatenation — both in order | `UV`, `36` |
| `a^*` | Zero or more (max 5) | `(0\|1)^*` |
| `a^+` | One or more (max 5) | `E^+`, `Z^+` |
| `a?` | Zero or one | `G?` |
| `a^n` | Exactly n times | `(3\|4)^5` |
| `a{n}` | Exactly n times (brace notation) | `(3\|4){5}` |
| ` ` or `*` after `^n` | Visual separator — ignored | `^5*36`, `^5 36` |

---

## Challenges

### Superscript notation (`^*`, `^+`, `^n`)
Standard regex engines treat `^` as a start-of-line anchor. The parser handles it by peeking at the character after `^`: if `*` or `+`, map to the standard unbounded quantifier; if a digit, read the full number and return an exact-count repetition node.

### The `*` separator in `(3|4)^5*36`
The `*` here is a visual separator in the handwritten assignment, not a Kleene star. Without special handling, the parser would emit a literal `*` character into the output. The fix: immediately after reading the digits of a `^n` quantifier, consume any following `*` or space characters before returning.

### Operator precedence
In a naive implementation, `ab|cd` parses as `a(b|c)d` instead of `(ab)|(cd)`. The recursive-descent call chain fixes this naturally — alternation is the outermost rule, concatenation is inner, so `|` always has lower precedence than concatenation.

---

## Conclusions

This lab produced a working regex-to-string generator built around a clean recursive-descent parser and an AST-walking generator. Key takeaways:

Recursive descent maps directly to grammar** — each rule becomes a method, making the parser easy to read, extend, and debug without any external library.
AST separation of concerns** — parsing and generation are completely independent. The parser knows nothing about randomness; the generator knows nothing about syntax. Either half can be replaced without touching the other.
Determinism via seeding** — passing a seed to `random` makes output fully reproducible, which is essential for debugging a program whose output is otherwise random by design.
Tracing as a first-class feature** — implementing `RegexTracer` alongside `RegexGenerator` required almost no extra code and makes the entire generation process fully transparent.
Notation resilience** — the parser handles three non-standard superscript quantifiers (`^*`, `^+`, `^n`) and two separator styles (space and `*`) without ambiguity, by placing separator-skip logic precisely where it can only fire after a `^n` quantifier.

The broader lesson is that the same tree-walking pattern used in interpreters and compilers — build a structured representation first, then traverse it — scales naturally from evaluating expressions all the way to generating strings from formal language definitions.

---

## References

- Course materials: Formal Languages & Finite Automata, TUM
- [Wikipedia: Regular Expression](https://en.wikipedia.org/wiki/Regular_expression)
- [Wikipedia: Recursive Descent Parser](https://en.wikipedia.org/wiki/Recursive_descent_parser)
- [Wikipedia: Abstract Syntax Tree](https://en.wikipedia.org/wiki/Abstract_syntax_tree)
- [Crafting Interpreters — Robert Nystrom](https://craftinginterpreters.com)
- [Python `random` module documentation](https://docs.python.org/3/library/random.html)