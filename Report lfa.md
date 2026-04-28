# Lab 4 – Parser & Building an Abstract Syntax Tree

**Course:** Formal Languages & Finite Automata  
**Student:** Pavlov Iulian
**Group:** FAF-241

---

## Theory

### Parsing

**Parsing** (syntactic analysis) is the second major phase of a compiler or interpreter. It receives the flat token stream produced by the lexer and checks whether the sequence of tokens conforms to the grammar of the language. When it does, it simultaneously builds a hierarchical data structure that captures the syntactic relationships between the tokens.

A **recursive-descent parser** implements each grammar production rule as a function that calls other rule-functions recursively. It is the most natural hand-written parsing technique: the call stack mirrors the grammar's derivation tree, and each level of the hierarchy corresponds to one level of operator precedence.

Operator **precedence** is encoded structurally: lower-precedence rules appear higher in the call chain and delegate to higher-precedence rules. For this language the hierarchy (weakest → strongest binding) is:

```
or → and → equality → comparison → addition → multiply → unary → postfix → primary
```

### Abstract Syntax Tree

A **parse tree** (concrete syntax tree) contains every token including punctuation, delimiters, and syntactic noise. An **Abstract Syntax Tree (AST)** strips these out and retains only semantically meaningful nodes:

- Parentheses disappear — grouping is encoded structurally.
- Delimiters (`{`, `}`, `;`) disappear once their purpose is captured in the node type.
- Keyword tokens disappear once they have selected the node type.

Each AST node carries enough information for subsequent compiler phases (type checking, interpretation, code generation) without requiring re-reading of the original source.

---

## Objectives

1. Get familiar with parsing and how it can be implemented programmatically.
2. Get familiar with the concept of an AST and its design.
3. In addition to what was done in Lab 3 (the lexer):
   - Add `TokenType` regex patterns for validating token lexemes.
   - Design a complete AST node hierarchy for the language.
   - Implement a recursive-descent parser that builds the AST.

---

## Implementation

The implementation is spread across three new files added on top of the Lab 3 lexer:

| File | Role |
|---|---|
| `token_type.py` | Existing enum — unchanged |
| `lexer.py` | Existing lexer — unchanged |
| `ast_nodes.py` | New — full AST node hierarchy |
| `parser.py` | New — recursive-descent parser + regex validation + demo |
| `test_parser.py` | New — 50 unit tests |

### TokenType regex validation

A `TOKEN_PATTERNS` dictionary in `parser.py` maps each `TokenType` to a compiled `re.Pattern`. The `validate_token(tok)` function checks a token's value against its declared type's pattern and returns a boolean:

```python
TOKEN_PATTERNS: dict[TokenType, re.Pattern] = {
    TokenType.FLOAT:      re.compile(r'^\d+\.\d+$'),
    TokenType.INTEGER:    re.compile(r'^\d+$'),
    TokenType.STRING:     re.compile(r'^"([^"\\]|\\.)*"$'),
    TokenType.IDENTIFIER: re.compile(r'^[A-Za-z_]\w*$'),
    TokenType.EQ:         re.compile(r'^==$'),
    TokenType.NEQ:        re.compile(r'^!=$'),
    TokenType.LTE:        re.compile(r'^<=$'),
    TokenType.GTE:        re.compile(r'^>=$'),
    TokenType.AND:        re.compile(r'^&&$'),
    TokenType.OR:         re.compile(r'^\|\|$'),
    # … single-char operators, delimiters, keywords …
}

def validate_token(tok) -> bool:
    pattern = TOKEN_PATTERNS.get(tok.type)
    if pattern is None:
        return True   # EOF, ILLEGAL — no pattern required
    raw = str(tok.value) if tok.value is not None else ""
    if tok.type == TokenType.STRING:
        raw = f'"{raw}"'   # lexer strips quotes, re-wrap for matching
    return bool(pattern.match(raw))
```

Running Stage 1 of the demo tokenises a 30-line program and validates every meaningful token — all pass (✓).

### AST Node Hierarchy

All nodes extend a common `ASTNode` base class defined in `ast_nodes.py`. Each node is a Python `@dataclass` and implements `to_dict()` for JSON serialisation and `__str__()` for the pretty-printer.

```
ASTNode
├── Expressions
│   ├── LiteralNode       — integer, float, string, bool constants
│   ├── IdentifierNode    — named symbol reference
│   ├── BinOpNode         — left <op> right
│   ├── UnaryOpNode       — <op> operand
│   ├── CallNode          — callee(arg, …)
│   ├── IndexNode         — collection[index]  or  obj.attr
│   ├── ArrayLiteralNode  — [elem, …]
│   └── MapLiteralNode    — {"key": value, …}
└── Statements
    ├── LetNode           — let name = value;
    ├── AssignNode        — name = value;
    ├── ReturnNode        — return [expr];
    ├── ExprStmtNode      — expression used as statement
    ├── BlockNode         — { stmt… }
    ├── IfNode            — condition, then_body, [else_body]
    ├── WhileNode         — condition, body
    ├── ForNode           — var, iterable, body
    ├── FnNode            — name, params[], body
    └── ProgramNode       — root (stmts[])
```

Example — the `BinOpNode` dataclass:

```python
@dataclass
class BinOpNode(ASTNode):
    left:  ASTNode
    op:    str
    right: ASTNode

    def to_dict(self):
        return {"node": "BinOp", "op": self.op,
                "left": self.left.to_dict(), "right": self.right.to_dict()}
```

### Parser

The `Parser` class in `parser.py` implements recursive descent. The constructor accepts the flat token list from the lexer.

**Token-stream helpers:**

| Method | Purpose |
|---|---|
| `_cur()` | Look at the current token without consuming |
| `_peek(n)` | Look n positions ahead |
| `_advance()` | Consume and return the current token |
| `_expect(type)` | Consume expected token or raise `ParseError` |
| `_consume_optional(type)` | Consume a token only if it matches |
| `_at_end()` | True when the current token is EOF |

**Statement dispatch** — `_parse_statement()` inspects the current (and sometimes next) token to select the right rule:

```python
def _parse_statement(self) -> ASTNode:
    tok = self._cur()
    if tok.type == TokenType.LET:    return self._parse_let()
    if tok.type == TokenType.FN:     return self._parse_fn()
    if tok.type == TokenType.RETURN: return self._parse_return()
    if tok.type == TokenType.IF:     return self._parse_if()
    if tok.type == TokenType.WHILE:  return self._parse_while()
    if tok.type == TokenType.FOR:    return self._parse_for()
    # IDENTIFIER followed by ASSIGN → assignment, not expression
    if tok.type == TokenType.IDENTIFIER and self._peek(1).type == TokenType.ASSIGN:
        return self._parse_assign()
    expr = self._parse_expr()
    self._consume_optional(TokenType.SEMICOLON)
    return ExprStmtNode(expr)
```

**Expression precedence** — each level is one method that calls the next tighter level and loops on its own operators:

```python
def _parse_addition(self) -> ASTNode:
    left = self._parse_multiply()
    while self._cur().type in (TokenType.PLUS, TokenType.MINUS):
        op    = self._advance().value
        right = self._parse_multiply()
        left  = BinOpNode(left, op, right)
    return left
```

This ensures `a + b * c` produces `BinOp(+, a, BinOp(*, b, c))` correctly, because `_parse_multiply` is called for both sides and "absorbs" the `*` before `_parse_addition` can see it.

**Postfix operations** — calls and indexing are handled in `_parse_postfix`, which wraps the primary node in successive `CallNode` or `IndexNode` layers:

```python
def _parse_postfix(self) -> ASTNode:
    node = self._parse_primary()
    while True:
        if self._cur().type == TokenType.LPAREN:
            node = self._parse_call_args(node)
        elif self._cur().type == TokenType.LBRACKET:
            self._advance()
            index = self._parse_expr()
            self._expect(TokenType.RBRACKET)
            node = IndexNode(node, index)
        elif self._cur().type == TokenType.DOT:
            self._advance()
            attr = self._expect(TokenType.IDENTIFIER)
            node = IndexNode(node, LiteralNode(attr.value, "string"))
        else:
            break
    return node
```

### Pretty-Printer

`print_ast()` in `parser.py` renders the tree using Unicode box-drawing characters. Running Stage 2 of the demo on a 30-line program produces:

```
Program
├── Let 'age'
│   └── Literal(int) 25
├── Let 'name'
│   └── Literal(string) 'Alice'
├── Let 'result'
│   └── BinOp '*'
│       ├── Literal(int) 10
│       └── BinOp '/'
│           ├── Literal(int) 20
│           └── Literal(int) 2
├── Let 'myArray'
│   └── ArrayLiteral [4 elems]
│       ├── Literal(int) 0
│       ├── Literal(int) 1
│       ├── Literal(int) 2
│       └── Literal(int) 3
├── Fn 'add'(first, second)
│   └── Block [1 stmts]
│       └── Return
│           └── BinOp '+'
│               ├── Identifier 'first'
│               └── Identifier 'second'
├── If
│   ├── BinOp '=='
│   │   ├── Identifier 'sum'
│   │   └── Literal(int) 6
│   ├── Block [1 stmts]
│   │   └── Let 'msg'
│   │       └── Literal(string) 'correct'
│   └── Block [1 stmts]
│       └── Let 'msg'
│           └── Literal(string) 'wrong'
├── Fn 'fibonacci'(n)
│   └── Block [2 stmts]
│       ├── If
│       │   ├── BinOp '<='
│       │   │   ├── Identifier 'n'
│       │   │   └── Literal(int) 1
│       │   └── Block [1 stmts]
│       │       └── Return
│       │           └── Identifier 'n'
│       └── Return
│           └── BinOp '+'
│               ├── Call …
│               └── Call …
└── While
    ├── BinOp '<'
    │   ├── Identifier 'i'
    │   └── Literal(int) 10
    └── Block [1 stmts]
        └── Assign
            ├── Identifier 'i'
            └── BinOp '+'
                ├── Identifier 'i'
                └── Literal(int) 1
```

Every node also serialises to JSON via `node.to_dict()` (Stage 3 of the demo).

---

## Results

Running `python parser.py` executes three stages:

**Stage 1 — Lexer table with regex validation:** Every meaningful token in the demo program is printed with its line/column, type, value, and a `✓` / `✗` validation symbol. All tokens validate as ✓.

**Stage 2 — AST tree:** The full Unicode tree for the demo program is printed, showing correct operator precedence (e.g. `*` binds tighter than `+`), nested control flow, and recursive function calls.

**Stage 3 — JSON dump:** The complete AST is serialised to JSON via `to_dict()`, suitable for further processing.

Running `python test_parser.py` executes **50 unit tests** covering:

- All literal types (int, float, string, bool, array, map)
- `let` bindings and assignments
- All binary and unary operators including precedence and associativity
- Function declarations and calls (with and without arguments, nested)
- `if`, `if/else`, `while`, and `for` control flow
- `return` with and without a value
- Array indexing and dot attribute access
- `ParseError` raised on malformed input
- `to_dict()` serialisation for key node types
- Regex validation for all token categories

All 50 tests pass.

---

## Conclusions

Lab 4 extends the Lab 3 lexer in three concrete ways. First, a `TOKEN_PATTERNS` dictionary maps every `TokenType` to a compiled `re.Pattern`; the `validate_token()` function uses these patterns to confirm that each token's lexeme matches its declared category. Second, a complete AST node hierarchy was designed in `ast_nodes.py` using Python `@dataclass` objects — covering all statement and expression forms of the language. Third, a full recursive-descent parser was implemented with a seven-level expression precedence hierarchy, `if/else`, `while`, `for`, `fn`, `return`, function-call, and index support.

The separation between `lexer.py`, `ast_nodes.py`, and `parser.py` mirrors the classical compiler pipeline: the lexer produces tokens; the parser consumes them and produces an AST; neither component knows the internals of the other, making both independently testable and replaceable.

---

## References

1. Crafting Interpreters — R. Nystrom, chapters 4–6 (https://craftinginterpreters.com)
2. Compilers: Principles, Techniques, and Tools — Aho, Lam, Sethi, Ullman (Dragon Book), §2.2–2.4
3. Formal Languages and Automata — UTM FCIM course materials
