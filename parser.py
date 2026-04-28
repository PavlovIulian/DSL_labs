"""
parser.py — Recursive-descent parser for the RoboScript-like language.

Consumes the token stream produced by Lexer and builds an AST
whose nodes are defined in ast_nodes.py.

Usage:
    from lexer import Lexer
    from parser import Parser

    tokens = list(Lexer(source).tokenize())
    tree   = Parser(tokens).parse()
"""
from __future__ import annotations

import json
from typing import Optional

from tok import Token
from token_type import TokenType
from errors import LexerError
from ast_nodes import (
    ASTNode, ProgramNode, BlockNode,
    LiteralNode, IdentifierNode,
    BinOpNode, UnaryOpNode,
    CallNode, IndexNode,
    ArrayLiteralNode, MapLiteralNode,
    LetNode, AssignNode, ReturnNode,
    ExprStmtNode, IfNode, WhileNode, ForNode, FnNode,
)


# ──────────────────────────────────────────────────────────────────────────────
#  Error
# ──────────────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(
            f"[Line {token.line}, Col {token.column}] ParseError: {message} "
            f"(got {token.type.name} {token.value!r})"
        )


# ──────────────────────────────────────────────────────────────────────────────
#  Parser
# ──────────────────────────────────────────────────────────────────────────────

class Parser:
    """
    Recursive-descent parser.

    Operator precedence (weakest → strongest):
        or → and → equality → comparison → addition → multiply → unary → primary
    """

    def __init__(self, tokens: list[Token]):
        # Drop EOF-only stream edge case; keep the sentinel
        self._tokens = tokens
        self._pos = 0

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def parse(self) -> ProgramNode:
        """Parse the full token stream and return a ProgramNode."""
        stmts: list[ASTNode] = []
        while not self._at_end():
            stmts.append(self._parse_statement())
        return ProgramNode(stmts)

    # ------------------------------------------------------------------ #
    #  Statement dispatch                                                  #
    # ------------------------------------------------------------------ #

    def _parse_statement(self) -> ASTNode:
        tok = self._cur()

        if tok.type == TokenType.LET:
            return self._parse_let()

        if tok.type == TokenType.FN:
            return self._parse_fn()

        if tok.type == TokenType.RETURN:
            return self._parse_return()

        if tok.type == TokenType.IF:
            return self._parse_if()

        if tok.type == TokenType.WHILE:
            return self._parse_while()

        if tok.type == TokenType.FOR:
            return self._parse_for()

        # Assignment vs expression-statement
        # Peek: IDENTIFIER followed by ASSIGN  →  assignment
        if (tok.type == TokenType.IDENTIFIER
                and self._peek(1).type == TokenType.ASSIGN):
            return self._parse_assign()

        expr = self._parse_expr()
        self._consume_optional(TokenType.SEMICOLON)
        return ExprStmtNode(expr)

    # ------------------------------------------------------------------ #
    #  Statement parsers                                                   #
    # ------------------------------------------------------------------ #

    def _parse_let(self) -> LetNode:
        self._expect(TokenType.LET)
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.ASSIGN)
        value = self._parse_expr()
        self._consume_optional(TokenType.SEMICOLON)
        return LetNode(name_tok.value, value)

    def _parse_fn(self) -> FnNode:
        self._expect(TokenType.FN)
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.LPAREN)
        params: list[str] = []
        while self._cur().type != TokenType.RPAREN:
            params.append(self._expect(TokenType.IDENTIFIER).value)
            if self._cur().type == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.RPAREN)
        body = self._parse_block()
        return FnNode(name_tok.value, params, body)

    def _parse_return(self) -> ReturnNode:
        self._expect(TokenType.RETURN)
        if self._cur().type in (TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
            self._consume_optional(TokenType.SEMICOLON)
            return ReturnNode(None)
        value = self._parse_expr()
        self._consume_optional(TokenType.SEMICOLON)
        return ReturnNode(value)

    def _parse_if(self) -> IfNode:
        self._expect(TokenType.IF)
        condition = self._parse_expr()
        then_body = self._parse_block()
        else_body: Optional[BlockNode] = None
        if self._cur().type == TokenType.ELSE:
            self._advance()
            else_body = self._parse_block()
        return IfNode(condition, then_body, else_body)

    def _parse_while(self) -> WhileNode:
        self._expect(TokenType.WHILE)
        condition = self._parse_expr()
        body = self._parse_block()
        return WhileNode(condition, body)

    def _parse_for(self) -> ForNode:
        self._expect(TokenType.FOR)
        var_tok = self._expect(TokenType.IDENTIFIER)
        # expect 'in' keyword (stored as IDENTIFIER since it's not reserved)
        in_tok = self._expect(TokenType.IDENTIFIER)
        if in_tok.value != "in":
            raise ParseError("Expected 'in' after for variable", in_tok)
        iterable = self._parse_expr()
        body = self._parse_block()
        return ForNode(var_tok.value, iterable, body)

    def _parse_assign(self) -> AssignNode:
        name = IdentifierNode(self._advance().value)
        self._expect(TokenType.ASSIGN)
        value = self._parse_expr()
        self._consume_optional(TokenType.SEMICOLON)
        return AssignNode(name, value)

    def _parse_block(self) -> BlockNode:
        self._expect(TokenType.LBRACE)
        stmts: list[ASTNode] = []
        while self._cur().type not in (TokenType.RBRACE, TokenType.EOF):
            stmts.append(self._parse_statement())
        self._expect(TokenType.RBRACE)
        return BlockNode(stmts)

    # ------------------------------------------------------------------ #
    #  Expression hierarchy (weakest → strongest precedence)              #
    # ------------------------------------------------------------------ #

    def _parse_expr(self) -> ASTNode:
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._cur().type == TokenType.OR:
            op = self._advance().value
            right = self._parse_and()
            left = BinOpNode(left, op, right)
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_equality()
        while self._cur().type == TokenType.AND:
            op = self._advance().value
            right = self._parse_equality()
            left = BinOpNode(left, op, right)
        return left

    def _parse_equality(self) -> ASTNode:
        left = self._parse_comparison()
        while self._cur().type in (TokenType.EQ, TokenType.NEQ):
            op = self._advance().value
            right = self._parse_comparison()
            left = BinOpNode(left, op, right)
        return left

    def _parse_comparison(self) -> ASTNode:
        left = self._parse_addition()
        while self._cur().type in (TokenType.LT, TokenType.GT,
                                    TokenType.LTE, TokenType.GTE):
            op = self._advance().value
            right = self._parse_addition()
            left = BinOpNode(left, op, right)
        return left

    def _parse_addition(self) -> ASTNode:
        left = self._parse_multiply()
        while self._cur().type in (TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiply()
            left = BinOpNode(left, op, right)
        return left

    def _parse_multiply(self) -> ASTNode:
        left = self._parse_unary()
        while self._cur().type in (TokenType.STAR, TokenType.SLASH,
                                    TokenType.PERCENT, TokenType.CARET):
            op = self._advance().value
            right = self._parse_unary()
            left = BinOpNode(left, op, right)
        return left

    def _parse_unary(self) -> ASTNode:
        if self._cur().type in (TokenType.BANG, TokenType.MINUS):
            op = self._advance().value
            operand = self._parse_unary()
            return UnaryOpNode(op, operand)
        return self._parse_postfix()

    def _parse_postfix(self) -> ASTNode:
        """Handle call  foo()  and index  arr[0]  after a primary."""
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

    def _parse_call_args(self, callee: ASTNode) -> CallNode:
        self._expect(TokenType.LPAREN)
        args: list[ASTNode] = []
        while self._cur().type != TokenType.RPAREN:
            args.append(self._parse_expr())
            if self._cur().type == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.RPAREN)
        return CallNode(callee, args)

    def _parse_primary(self) -> ASTNode:
        tok = self._cur()

        # Integer literal
        if tok.type == TokenType.INTEGER:
            self._advance()
            return LiteralNode(tok.value, "int")

        # Float literal
        if tok.type == TokenType.FLOAT:
            self._advance()
            return LiteralNode(tok.value, "float")

        # String literal
        if tok.type == TokenType.STRING:
            self._advance()
            return LiteralNode(tok.value, "string")

        # Boolean literals
        if tok.type == TokenType.TRUE:
            self._advance()
            return LiteralNode(True, "bool")
        if tok.type == TokenType.FALSE:
            self._advance()
            return LiteralNode(False, "bool")

        # Identifier
        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return IdentifierNode(tok.value)

        # Grouped expression
        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return expr

        # Array literal
        if tok.type == TokenType.LBRACKET:
            self._advance()
            elements: list[ASTNode] = []
            while self._cur().type != TokenType.RBRACKET:
                elements.append(self._parse_expr())
                if self._cur().type == TokenType.COMMA:
                    self._advance()
            self._expect(TokenType.RBRACKET)
            return ArrayLiteralNode(elements)

        # Map literal
        if tok.type == TokenType.LBRACE:
            self._advance()
            pairs: list[tuple[ASTNode, ASTNode]] = []
            while self._cur().type != TokenType.RBRACE:
                key = self._parse_expr()
                self._expect(TokenType.COLON)
                val = self._parse_expr()
                pairs.append((key, val))
                if self._cur().type == TokenType.COMMA:
                    self._advance()
            self._expect(TokenType.RBRACE)
            return MapLiteralNode(pairs)

        raise ParseError("Unexpected token in expression", tok)

    # ------------------------------------------------------------------ #
    #  Token-stream helpers                                                #
    # ------------------------------------------------------------------ #

    def _cur(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, n: int = 1) -> Token:
        idx = self._pos + n
        if idx >= len(self._tokens):
            return self._tokens[-1]   # EOF sentinel
        return self._tokens[idx]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        if self._pos < len(self._tokens) - 1:
            self._pos += 1
        return tok

    def _at_end(self) -> bool:
        return self._cur().type == TokenType.EOF

    def _expect(self, tok_type: TokenType, value: object = None) -> Token:
        tok = self._cur()
        if tok.type != tok_type:
            raise ParseError(f"Expected {tok_type.name}", tok)
        if value is not None and tok.value != value:
            raise ParseError(f"Expected value {value!r}", tok)
        return self._advance()

    def _consume_optional(self, tok_type: TokenType) -> None:
        if self._cur().type == tok_type:
            self._advance()


# ──────────────────────────────────────────────────────────────────────────────
#  Pretty-printer
# ──────────────────────────────────────────────────────────────────────────────

def print_ast(node: ASTNode, prefix: str = "", is_last: bool = True) -> None:
    """Render the AST with Unicode box-drawing connectors."""
    connector = "└── " if is_last else "├── "
    print(prefix + connector + str(node))

    child_prefix = prefix + ("    " if is_last else "│   ")
    children = _get_children(node)
    for i, child in enumerate(children):
        print_ast(child, child_prefix, i == len(children) - 1)


def _get_children(node: ASTNode) -> list[ASTNode]:
    """Return the meaningful child nodes of a given node."""
    if isinstance(node, ProgramNode):
        return node.stmts
    if isinstance(node, BlockNode):
        return node.stmts
    if isinstance(node, FnNode):
        return [node.body]
    if isinstance(node, LetNode):
        return [node.value]
    if isinstance(node, AssignNode):
        return [node.name, node.value]
    if isinstance(node, ReturnNode):
        return [node.value] if node.value else []
    if isinstance(node, ExprStmtNode):
        return [node.expr]
    if isinstance(node, IfNode):
        children = [node.condition, node.then_body]
        if node.else_body:
            children.append(node.else_body)
        return children
    if isinstance(node, WhileNode):
        return [node.condition, node.body]
    if isinstance(node, ForNode):
        return [node.iterable, node.body]
    if isinstance(node, BinOpNode):
        return [node.left, node.right]
    if isinstance(node, UnaryOpNode):
        return [node.operand]
    if isinstance(node, CallNode):
        return [node.callee] + node.args
    if isinstance(node, IndexNode):
        return [node.collection, node.index]
    if isinstance(node, ArrayLiteralNode):
        return node.elements
    if isinstance(node, MapLiteralNode):
        result = []
        for k, v in node.pairs:
            result += [k, v]
        return result
    return []


# ──────────────────────────────────────────────────────────────────────────────
#  Token regex validation
# ──────────────────────────────────────────────────────────────────────────────

import re

TOKEN_PATTERNS: dict[TokenType, re.Pattern] = {
    TokenType.FLOAT:      re.compile(r'^\d+\.\d+$'),
    TokenType.INTEGER:    re.compile(r'^\d+$'),
    TokenType.STRING:     re.compile(r'^"([^"\\]|\\.)*"$'),
    TokenType.TRUE:       re.compile(r'^true$'),
    TokenType.FALSE:      re.compile(r'^false$'),
    TokenType.IDENTIFIER: re.compile(r'^[A-Za-z_]\w*$'),
    # Two-char operators
    TokenType.EQ:         re.compile(r'^==$'),
    TokenType.NEQ:        re.compile(r'^!=$'),
    TokenType.LTE:        re.compile(r'^<=$'),
    TokenType.GTE:        re.compile(r'^>=$'),
    TokenType.AND:        re.compile(r'^&&$'),
    TokenType.OR:         re.compile(r'^\|\|$'),
    # Single-char operators
    TokenType.PLUS:       re.compile(r'^\+$'),
    TokenType.MINUS:      re.compile(r'^-$'),
    TokenType.STAR:       re.compile(r'^\*$'),
    TokenType.SLASH:      re.compile(r'^/$'),
    TokenType.PERCENT:    re.compile(r'^%$'),
    TokenType.CARET:      re.compile(r'^\^$'),
    TokenType.ASSIGN:     re.compile(r'^=$'),
    TokenType.LT:         re.compile(r'^<$'),
    TokenType.GT:         re.compile(r'^>$'),
    TokenType.BANG:       re.compile(r'^!$'),
    # Delimiters
    TokenType.LPAREN:     re.compile(r'^\($'),
    TokenType.RPAREN:     re.compile(r'^\)$'),
    TokenType.LBRACE:     re.compile(r'^\{$'),
    TokenType.RBRACE:     re.compile(r'^\}$'),
    TokenType.LBRACKET:   re.compile(r'^\[$'),
    TokenType.RBRACKET:   re.compile(r'^\]$'),
    TokenType.COMMA:      re.compile(r'^,$'),
    TokenType.SEMICOLON:  re.compile(r'^;$'),
    TokenType.COLON:      re.compile(r'^:$'),
    TokenType.DOT:        re.compile(r'^\.$'),
    # Keywords (validated as identifier pattern)
    TokenType.LET:        re.compile(r'^let$'),
    TokenType.FN:         re.compile(r'^fn$'),
    TokenType.RETURN:     re.compile(r'^return$'),
    TokenType.IF:         re.compile(r'^if$'),
    TokenType.ELSE:       re.compile(r'^else$'),
    TokenType.WHILE:      re.compile(r'^while$'),
    TokenType.FOR:        re.compile(r'^for$'),
}


def validate_token(tok) -> bool:
    """Return True if tok.value matches its declared TokenType pattern."""
    pattern = TOKEN_PATTERNS.get(tok.type)
    if pattern is None:
        return True   # EOF, ILLEGAL — no pattern needed
    raw = str(tok.value) if tok.value is not None else ""
    # For string literals the lexer strips the quotes, so re-wrap for matching
    if tok.type == TokenType.STRING:
        raw = f'"{raw}"'
    return bool(pattern.match(raw))


# ──────────────────────────────────────────────────────────────────────────────
#  Demo / main
# ──────────────────────────────────────────────────────────────────────────────

DEMO_SOURCE = """\
let age = 25;
let name = "Alice";
let result = 10 * (20 / 2);

let myArray = [0, 1, 2, 3];
let myMap = {"name": "Alice", "age": 25};

fn add(first, second) {
    return first + second;
}

let sum = add(2, 4);

if sum == 6 {
    let msg = "correct";
} else {
    let msg = "wrong";
}

fn fibonacci(n) {
    if n <= 1 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

let i = 0;
while i < 10 {
    i = i + 1;
}
"""

DIVIDER = "─" * 65


def main() -> None:
    from lexer import Lexer

    print(DIVIDER)
    print("  Stage 1 — Lexer token table with regex validation")
    print(DIVIDER)

    tokens = list(Lexer(DEMO_SOURCE).tokenize())
    meaningful = [t for t in tokens if t.type != TokenType.EOF]

    max_type = max(len(t.type.name) for t in tokens)
    pass_count = fail_count = 0

    for tok in meaningful:
        ok = validate_token(tok)
        status = "✓" if ok else "✗"
        if ok:
            pass_count += 1
        else:
            fail_count += 1
        loc  = f"[{tok.line:2d}:{tok.column:2d}]"
        name = tok.type.name.ljust(max_type)
        val  = repr(tok.value) if tok.value is not None else ""
        print(f"  {loc}  {name}  {val:<20}  {status}")

    print()
    print(f"  {pass_count} tokens validated ✓   {fail_count} failed ✗")

    print()
    print(DIVIDER)
    print("  Stage 2 — AST tree")
    print(DIVIDER)

    tokens2 = list(Lexer(DEMO_SOURCE).tokenize())
    tree = Parser(tokens2).parse()

    # Print root manually so print_ast works nicely
    print("Program")
    children = _get_children(tree)
    for i, child in enumerate(children):
        print_ast(child, "", i == len(children) - 1)

    print()
    print(DIVIDER)
    print("  Stage 3 — AST JSON dump")
    print(DIVIDER)
    print(json.dumps(tree.to_dict(), indent=2))


if __name__ == "__main__":
    main()
