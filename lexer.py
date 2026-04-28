from typing import Iterator
from tok import Token
from token_type import TokenType
from errors import LexerError


# Reserved keywords → TokenType mapping
KEYWORDS: dict[str, TokenType] = {
    "let":    TokenType.LET,
    "fn":     TokenType.FN,
    "return": TokenType.RETURN,
    "if":     TokenType.IF,
    "else":   TokenType.ELSE,
    "true":   TokenType.TRUE,
    "false":  TokenType.FALSE,
    "while":  TokenType.WHILE,
    "for":    TokenType.FOR,
    # Trigonometric functions
    "sin":    TokenType.SIN,
    "cos":    TokenType.COS,
}

# Single-character tokens
SINGLE_CHAR: dict[str, TokenType] = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "%": TokenType.PERCENT,
    "^": TokenType.CARET,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
    ":": TokenType.COLON,
    ".": TokenType.DOT,      # ← add this if missing
}


class Lexer:
    """
    Converts a source string into a flat stream of Token objects.

    Usage:
        lexer = Lexer(source_code)
        tokens = list(lexer.tokenize())
    """

    def __init__(self, source: str):
        self._source = source
        self._pos = 0
        self._line = 1
        self._column = 1

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def tokenize(self) -> Iterator[Token]:
        """Yield tokens one by one until EOF."""
        while not self._at_end():
            yield from self._next_token()

        yield self._make_token(TokenType.EOF, None)

    # ------------------------------------------------------------------ #
    #  Core dispatch                                                       #
    # ------------------------------------------------------------------ #

    def _next_token(self) -> Iterator[Token]:
        self._skip_whitespace_and_comments()

        if self._at_end():
            return

        ch = self._current()

        # --- Numbers (integer and float) ---
        if ch.isdigit() or (ch == "." and self._peek_next().isdigit()):
            yield self._read_number()
            return

        # --- Strings ---
        if ch == '"':
            yield self._read_string()
            return

        # --- Identifiers / keywords (including sin, cos) ---
        if ch.isalpha() or ch == "_":
            yield self._read_identifier()
            return

        # --- Two-character operators ---
        two = self._peek_two()
        if two == "==":
            yield self._consume_two(TokenType.EQ, "==");    return
        if two == "!=":
            yield self._consume_two(TokenType.NEQ, "!=");   return
        if two == "<=":
            yield self._consume_two(TokenType.LTE, "<=");   return
        if two == ">=":
            yield self._consume_two(TokenType.GTE, ">=");   return
        if two == "&&":
            yield self._consume_two(TokenType.AND, "&&");   return
        if two == "||":
            yield self._consume_two(TokenType.OR, "||");    return

        # --- Single-character operators / delimiters ---
        if ch in SINGLE_CHAR:
            yield self._make_token(SINGLE_CHAR[ch], ch)
            self._advance()
            return

        if ch == "=":
            yield self._make_token(TokenType.ASSIGN, ch); self._advance(); return
        if ch == "<":
            yield self._make_token(TokenType.LT, ch);     self._advance(); return
        if ch == ">":
            yield self._make_token(TokenType.GT, ch);     self._advance(); return
        if ch == "!":
            yield self._make_token(TokenType.BANG, ch);   self._advance(); return

        # --- Illegal character ---
        tok = self._make_token(TokenType.ILLEGAL, ch)
        self._advance()
        yield tok

    # ------------------------------------------------------------------ #
    #  Readers                                                             #
    # ------------------------------------------------------------------ #

    def _read_number(self) -> Token:
        """
        Read an integer or float literal.
        Supports:  42  |  3.14  |  .5  |  1_000 (underscores as separators)
        A leading minus is a separate MINUS token; the parser handles unary negation.
        """
        start_col = self._column
        start_line = self._line
        buf: list[str] = []
        is_float = False

        # Leading dot case: .5
        if self._current() == ".":
            is_float = True
            buf.append(self._advance())

        while not self._at_end():
            ch = self._current()
            if ch.isdigit():
                buf.append(self._advance())
            elif ch == "_":
                # Numeric separators like 1_000; underscore skipped in value
                self._advance()
            elif ch == "." and not is_float:
                next_ch = self._peek_next()
                if next_ch.isdigit() or next_ch == "":
                    is_float = True
                    buf.append(self._advance())
                else:
                    break
            else:
                break

        raw = "".join(buf)
        value = float(raw) if is_float else int(raw)
        tok_type = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(tok_type, value, start_line, start_col)

    def _read_string(self) -> Token:
        start_col = self._column
        start_line = self._line
        self._advance()  # consume opening "
        buf: list[str] = []

        while not self._at_end() and self._current() != '"':
            if self._current() == "\\":
                self._advance()
                escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}
                esc = self._advance()
                buf.append(escape_map.get(esc, esc))
            else:
                buf.append(self._advance())

        if self._at_end():
            raise LexerError("Unterminated string literal", start_line, start_col)

        self._advance()  # consume closing "
        return Token(TokenType.STRING, "".join(buf), start_line, start_col)

    def _read_identifier(self) -> Token:
        start_col = self._column
        start_line = self._line
        buf: list[str] = []

        while not self._at_end() and (self._current().isalnum() or self._current() == "_"):
            buf.append(self._advance())

        word = "".join(buf)
        tok_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(tok_type, word, start_line, start_col)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _skip_whitespace_and_comments(self) -> None:
        while not self._at_end():
            ch = self._current()
            if ch in (" ", "\t", "\r"):
                self._advance()
            elif ch == "\n":
                self._advance()
            elif ch == "/" and self._peek_two() == "//":
                while not self._at_end() and self._current() != "\n":
                    self._advance()
            elif ch == "/" and self._peek_two() == "/*":
                self._advance(); self._advance()
                while not self._at_end():
                    if self._peek_two() == "*/":
                        self._advance(); self._advance()
                        break
                    self._advance()
            else:
                break

    def _consume_two(self, tok_type: TokenType, value: str) -> Token:
        tok = self._make_token(tok_type, value)
        self._advance()
        self._advance()
        return tok

    def _make_token(self, tok_type: TokenType, value) -> Token:
        return Token(tok_type, value, self._line, self._column)

    def _current(self) -> str:
        return self._source[self._pos]

    def _advance(self) -> str:
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return ch

    def _peek_two(self) -> str:
        return self._source[self._pos: self._pos + 2]

    def _peek_next(self) -> str:
        """Peek one character ahead without consuming."""
        if self._pos + 1 < len(self._source):
            return self._source[self._pos + 1]
        return ""

    def _at_end(self) -> bool:
        return self._pos >= len(self._source)