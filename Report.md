# Lab 1 — Lexer / Scanner

**Course:** Formal Languages & Finite Automata
**Author:** Iulian Pavlov

---

## Table of Contents

1. [Overview](#overview)
2. [Objectives](#objectives)
3. [Token Types Defined](#token-types-defined)
4. [Project Structure](#project-structure)
5. [Implementation](#implementation)
6. [How It Works — Step by Step](#how-it-works--step-by-step)
7. [Testing](#testing)
8. [Challenges Encountered](#challenges-encountered)
9. [Conclusions](#conclusions)
10. [References](#references)

---

## Overview

This lab implements a **Lexer** (also called a Scanner or Tokenizer) — the first stage in the pipeline of a compiler or interpreter. The lexer reads raw source code as a plain string and converts it into a flat sequence of **tokens**, where each token represents one meaningful unit of the language: a keyword, an operator, a literal value, or a delimiter.

The term lexer comes from *lexical analysis* — the process of extracting lexical tokens from a string of characters. It sits directly after raw source code and directly before parsing in the standard compiler pipeline:

```
Source Code  →  [Lexer / Scanner]  →  Tokens  →  [Parser]  →  Abstract Syntax Tree
```

The lexer does not understand the meaning or grammar of the language — it only recognises surface patterns. It knows that `fn` is a keyword, `3.14` is a float, and `==` is a comparison operator. What those things mean together is the parser's job.

---

## Objectives

1. Understand what lexical analysis is and where it fits in a compiler pipeline.
2. Get familiar with the inner workings of a lexer / scanner / tokenizer.
3. Implement a sample lexer in Python with clean, modular architecture.
4. Handle all common token categories: literals, keywords, operators, delimiters.
5. Implement accurate line and column tracking for precise error reporting.
6. Write a test suite that verifies correctness across all token categories.

---

## Token Types Defined

The lexer recognises the following categories of tokens:

| Category | Token Names | Examples |
|---|---|---|
| Literals | `INTEGER`, `FLOAT`, `STRING`, `IDENTIFIER` | `42`, `3.14`, `"hello"`, `myVar` |
| Keywords | `LET`, `FN`, `RETURN`, `IF`, `ELSE`, `TRUE`, `FALSE`, `WHILE`, `FOR` | `let`, `fn`, `return` |
| Arithmetic | `PLUS`, `MINUS`, `STAR`, `SLASH`, `PERCENT`, `CARET` | `+ - * / % ^` |
| Comparison | `EQ`, `NEQ`, `LT`, `GT`, `LTE`, `GTE` | `== != < > <= >=` |
| Assignment | `ASSIGN` | `=` |
| Logical | `AND`, `OR`, `BANG` | `&& \|\| !` |
| Delimiters | `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `LBRACKET`, `RBRACKET`, `COMMA`, `SEMICOLON`, `COLON`, `DOT` | `( ) { } [ ] , ; : .` |
| Special | `EOF`, `ILLEGAL` | end of input, unrecognised char |

`ILLEGAL` is emitted for any character the lexer does not recognise (e.g. `?`, `@`, `#`). This is intentional — instead of crashing, the lexer flags unknown input so a later stage can produce a meaningful error message with the exact location.

---

## Project Structure

```
DSL_labs/
  token_type.py    —  TokenType enum (all token categories)
  tok.py           —  Token dataclass (type + value + line + column)
  errors.py        —  LexerError with location information
  lexer.py         —  Core Lexer class
  main.py          —  CLI: interactive REPL or file tokenizer
  demo.py          —  Hardcoded demonstration examples
  test_lexer.py    —  22 unit tests
```

> **Note:** The token file is named `tok.py` rather than `token.py` because Python's standard library already ships a built-in module named `token`. Naming a project file the same way shadows the built-in, causing an `ImportError` at runtime. Renaming to `tok.py` avoids the collision entirely. The same rule applies to other built-in names like `types.py`, `string.py`, `os.py`.

---

## Implementation

### `token_type.py` — TokenType Enum

Defines every token category as a member of a Python `Enum`. Using an Enum rather than plain string constants provides type safety, prevents typos, and makes token comparisons readable:

```python
from enum import Enum, auto

class TokenType(Enum):
    INTEGER    = auto()    # e.g. 42
    FLOAT      = auto()    # e.g. 3.14
    STRING     = auto()    # e.g. "hello"
    IDENTIFIER = auto()    # e.g. myVar
    LET        = auto()    # keyword: let
    FN         = auto()    # keyword: fn
    # ... (all remaining types)
    EOF        = auto()    # end of input
    ILLEGAL    = auto()    # unrecognised character
```

### `tok.py` — Token Dataclass

Each token found in the source is represented as a frozen (immutable) dataclass with four fields. The `line` and `column` fields make it possible to point to an exact location when reporting errors:

```python
@dataclass(frozen=True)
class Token:
    type:   TokenType   # the category
    value:  Any         # actual text or parsed number
    line:   int         # 1-based line number
    column: int         # 1-based column number
```

### `errors.py` — LexerError

A custom exception that attaches line and column to the error message, making it immediately actionable:

```python
class LexerError(Exception):
    def __init__(self, message, line, column):
        super().__init__(
            f'[Line {line}, Col {column}] LexerError: {message}'
        )
```

Example output: `[Line 3, Col 12] LexerError: Unterminated string literal`

### `lexer.py` — Core Lexer

The `Lexer` class takes a source string and exposes one public method, `tokenize()`, which is a Python generator that yields `Token` objects lazily — one at a time, only when requested.

The core dispatch loop in `_next_token()` handles cases in this priority order:

1. **Whitespace and comments** — skipped silently. Both `//` single-line and `/* */` multi-line comment styles are supported.
2. **Digits** — `_read_number()` collects all consecutive digits and optional decimal point, then parses to `int` or `float`.
3. **Double quote** — `_read_string()` collects characters until the closing quote, handling escape sequences (`\n`, `\t`, `\\`, `\"`).
4. **Letter or underscore** — `_read_identifier()` collects the full word, then checks the `KEYWORDS` dictionary to determine whether it is a keyword or a plain identifier.
5. **Two-character operators** — `_peek_two()` reads ahead without consuming; matches `==`, `!=`, `<=`, `>=`, `&&`, `||`.
6. **Single-character operators and delimiters** — looked up in the `SINGLE_CHAR` dictionary.
7. **Anything else** — `ILLEGAL` token emitted; processing continues.

### `main.py` — CLI Entry Point

Two modes depending on whether a filename argument is supplied:

```bash
# Interactive REPL
python main.py
>>> let x = 5 + 5;
  [  1: 1]  LET         ->  'let'
  [  1: 5]  IDENTIFIER  ->  'x'
  [  1: 7]  ASSIGN      ->  '='
  [  1: 9]  INTEGER     ->  5
  ...

# File tokenizer
python main.py source.txt
```

### `demo.py` — Demonstration Script

Runs the lexer on six hardcoded source snippets and pretty-prints each token with its location. The snippets cover: variable binding, array and map literals, function declaration and call, if/else branching, recursive fibonacci, and comments.

---

## How It Works — Step by Step

Consider this source string:

```
let average = (min + max) / 2;
```

The `Lexer` starts at position 0 with `_line=1, _column=1` and processes the input character by character:

| Step | Input | Action | Token Emitted |
|---|---|---|---|
| 1 | `l e t` | `_read_identifier()` | `LET 'let' [1:1]` |
| 2 | ` ` | skip whitespace | — |
| 3 | `a v e r a g e` | `_read_identifier()` — not in KEYWORDS | `IDENTIFIER 'average' [1:5]` |
| 4 | ` ` | skip | — |
| 5 | `=` | peek ahead sees space, not `=` | `ASSIGN '=' [1:13]` |
| 6 | ` ` | skip | — |
| 7 | `(` | `SINGLE_CHAR` lookup | `LPAREN '(' [1:15]` |
| 8 | `m i n` | `_read_identifier()` | `IDENTIFIER 'min' [1:16]` |
| 9 | `+` | `SINGLE_CHAR` | `PLUS '+' [1:20]` |
| 10 | `m a x` | `_read_identifier()` | `IDENTIFIER 'max' [1:22]` |
| 11 | `)` | `SINGLE_CHAR` | `RPAREN ')' [1:25]` |
| 12 | `/` | `SINGLE_CHAR` | `SLASH '/' [1:27]` |
| 13 | `2` | `_read_number()` — no dot | `INTEGER 2 [1:29]` |
| 14 | `;` | `SINGLE_CHAR` | `SEMICOLON ';' [1:30]` |
| 15 | (end) | `_at_end() == True` | `EOF None [1:31]` |

Final token stream:
```
[LET, IDENTIFIER('average'), ASSIGN, LPAREN, IDENTIFIER('min'),
 PLUS, IDENTIFIER('max'), RPAREN, SLASH, INTEGER(2), SEMICOLON, EOF]
```

---

## Testing

The test suite in `test_lexer.py` contains **22 unit tests** split across 7 test classes. All 22 pass.

| Test Class | Coverage | Tests |
|---|---|---|
| `TestLiterals` | INTEGER, FLOAT, STRING; escape sequences; unterminated string raises `LexerError` | 5 |
| `TestKeywords` | All 9 keywords; identifier vs keyword disambiguation | 6 |
| `TestOperators` | Single-char arithmetic; two-char operators; ASSIGN vs EQ | 3 |
| `TestDelimiters` | Parentheses, braces, brackets, semicolons, commas | 2 |
| `TestComments` | Single-line `//` and multi-line `/* */` comments stripped | 2 |
| `TestLineTracking` | Line numbers on newlines; column numbers within a line | 2 |
| `TestFullExpression` | Full variable assignment; full function declaration end-to-end | 2 |

Run the tests:

```bash
python -m unittest discover tests/ -v
```

Output:
```
..............................
----------------------------------------------------------------------
Ran 22 tests in 0.002s

OK
```

---

## Challenges Encountered

### Challenge 1 — Naming conflict with Python's built-in `token` module

The file was initially named `token.py`. However, Python's standard library ships a built-in module also named `token` used internally by the tokenizer. When `token.py` existed in the project directory, Python's internals grabbed the project file instead, causing:

```
ImportError: cannot import name 'EXACT_TOKEN_TYPES' from 'token'
```

**Fix:** Rename `token.py` → `tok.py` and update the single import in `lexer.py`. Avoid naming files after any standard-library module.

### Challenge 2 — Relative imports in a flat directory

The initial code used relative imports (`from .token_type import TokenType`), which only work inside a proper Python package (a directory with `__init__.py`). With a flat layout this raised:

```
ImportError: attempted relative import with no known parent package
```

**Fix:** Remove the leading dot from all imports (`from token_type import TokenType`). Python resolves plain absolute imports by searching the directory of the running script, which is correct for a flat project layout.

### Challenge 3 — Two-character operator lookahead

Operators like `==` and `=` share the same first character. Checking single-character operators first caused `=` to be emitted before the second `=` was read — turning `==` into two separate `ASSIGN` tokens.

**Fix:** Always check two-character operators before single-character ones in the dispatch loop, using `_peek_two()` to read ahead without consuming any characters.

---

## Conclusions

This lab produced a working, well-structured lexer in Python that correctly tokenizes a small programming language supporting variables, functions, arithmetic, comparisons, strings, and comments. Key takeaways:

- **Separation of concerns:** keeping token types, token data, error handling, and the lexer algorithm in separate files makes each part easy to understand, test, and modify independently.
- **Defensive behavior:** emitting `ILLEGAL` instead of crashing means the lexer always produces output, allowing error recovery at a higher level.
- **Lazy evaluation via generators:** `tokenize()` yields tokens on demand — memory-efficient and allows the caller to stop early if needed.
- **Standard library name collisions:** Python's namespace is large; short intuitive names like `token`, `string`, or `types` are already taken.

The main takeaway is that a lexer's job is purely **pattern recognition**, not understanding. By keeping this scope narrow and well-defined, the lexer stays simple, fast, and easy to test, while the layers above it can focus entirely on structure and meaning.

---

## References

- Course materials: Formal Languages & Finite Automata
- [LLVM Kaleidoscope Tutorial — Lexer implementation reference](https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl01.html)
- [Wikipedia: Lexical Analysis](https://en.wikipedia.org/wiki/Lexical_analysis)
- [Crafting Interpreters — Robert Nystrom](https://craftinginterpreters.com)
- [Python Enum documentation](https://docs.python.org/3/library/enum.html)
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)