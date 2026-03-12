import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lexer import Lexer, TokenType, LexerError


def lex(src: str):
    return list(Lexer(src).tokenize())


class TestLiterals(unittest.TestCase):

    def test_integer(self):
        tokens = lex("42")
        self.assertEqual(tokens[0].type, TokenType.INTEGER)
        self.assertEqual(tokens[0].value, 42)

    def test_float(self):
        tokens = lex("3.14")
        self.assertEqual(tokens[0].type, TokenType.FLOAT)
        self.assertAlmostEqual(tokens[0].value, 3.14)

    def test_string(self):
        tokens = lex('"hello world"')
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, "hello world")

    def test_string_escape_sequences(self):
        tokens = lex(r'"line1\nline2"')
        self.assertEqual(tokens[0].value, "line1\nline2")

    def test_unterminated_string_raises(self):
        with self.assertRaises(LexerError):
            lex('"oops')


class TestKeywords(unittest.TestCase):

    def test_let_keyword(self):
        self.assertEqual(lex("let")[0].type, TokenType.LET)

    def test_fn_keyword(self):
        self.assertEqual(lex("fn")[0].type, TokenType.FN)

    def test_return_keyword(self):
        self.assertEqual(lex("return")[0].type, TokenType.RETURN)

    def test_if_else(self):
        tokens = lex("if else")
        self.assertEqual(tokens[0].type, TokenType.IF)
        self.assertEqual(tokens[1].type, TokenType.ELSE)

    def test_true_false(self):
        tokens = lex("true false")
        self.assertEqual(tokens[0].type, TokenType.TRUE)
        self.assertEqual(tokens[1].type, TokenType.FALSE)

    def test_identifier_not_keyword(self):
        self.assertEqual(lex("foobar")[0].type, TokenType.IDENTIFIER)


class TestOperators(unittest.TestCase):

    def test_single_char_ops(self):
        mapping = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "^": TokenType.CARET,
            "?": TokenType.QUESTION,
        }
        for ch, expected in mapping.items():
            self.assertEqual(lex(ch)[0].type, expected, f"Failed for {ch!r}")

    def test_two_char_ops(self):
        mapping = {
            "==": TokenType.EQ,
            "!=": TokenType.NEQ,
            "<=": TokenType.LTE,
            ">=": TokenType.GTE,
            "&&": TokenType.AND,
            "||": TokenType.OR,
        }
        for src, expected in mapping.items():
            self.assertEqual(lex(src)[0].type, expected, f"Failed for {src!r}")

    def test_assign_vs_eq(self):
        tokens = lex("= ==")
        self.assertEqual(tokens[0].type, TokenType.ASSIGN)
        self.assertEqual(tokens[1].type, TokenType.EQ)


class TestDelimiters(unittest.TestCase):

    def test_parens_and_braces(self):
        tokens = lex("(){}")
        types = [t.type for t in tokens[:-1]]   # skip EOF
        self.assertEqual(types, [
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.LBRACE, TokenType.RBRACE,
        ])

    def test_semicolon_comma(self):
        tokens = lex(";,")
        self.assertEqual(tokens[0].type, TokenType.SEMICOLON)
        self.assertEqual(tokens[1].type, TokenType.COMMA)


class TestComments(unittest.TestCase):

    def test_single_line_comment(self):
        tokens = lex("let x // this is ignored\nlet y")
        types = [t.type for t in tokens[:-1]]
        self.assertEqual(types, [TokenType.LET, TokenType.IDENTIFIER,
                                  TokenType.LET, TokenType.IDENTIFIER])

    def test_multiline_comment(self):
        tokens = lex("let /* ignored\nstuff */ x")
        types = [t.type for t in tokens[:-1]]
        self.assertEqual(types, [TokenType.LET, TokenType.IDENTIFIER])


class TestLineTracking(unittest.TestCase):

    def test_line_numbers(self):
        tokens = lex("let\nx")
        self.assertEqual(tokens[0].line, 1)
        self.assertEqual(tokens[1].line, 2)

    def test_column_numbers(self):
        tokens = lex("let x")
        self.assertEqual(tokens[0].column, 1)
        self.assertEqual(tokens[1].column, 5)


class TestFullExpression(unittest.TestCase):

    def test_variable_assignment(self):
        tokens = lex("let average = (min + max) / 2;")
        types = [t.type for t in tokens[:-1]]
        self.assertEqual(types, [
            TokenType.LET,
            TokenType.IDENTIFIER,   # average
            TokenType.ASSIGN,
            TokenType.LPAREN,
            TokenType.IDENTIFIER,   # min
            TokenType.PLUS,
            TokenType.IDENTIFIER,   # max
            TokenType.RPAREN,
            TokenType.SLASH,
            TokenType.INTEGER,      # 2
            TokenType.SEMICOLON,
        ])

    def test_function_declaration(self):
        src = "fn add(x, y) { return x + y; }"
        tokens = lex(src)
        self.assertEqual(tokens[0].type, TokenType.FN)
        self.assertEqual(tokens[1].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[1].value, "add")


if __name__ == "__main__":
    unittest.main(verbosity=2)
