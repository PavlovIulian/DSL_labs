
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lexer import Lexer
from parser import Parser, ParseError, validate_token
from token_type import TokenType
from ast_nodes import (
    ProgramNode, LetNode, AssignNode, FnNode, ReturnNode,
    IfNode, WhileNode, ForNode, ExprStmtNode, BlockNode,
    LiteralNode, IdentifierNode, BinOpNode, UnaryOpNode,
    CallNode, IndexNode, ArrayLiteralNode, MapLiteralNode,
)


def parse(src: str) -> ProgramNode:
    tokens = list(Lexer(src).tokenize())
    return Parser(tokens).parse()


def first(src: str):
    """Return the first top-level statement from a parsed snippet."""
    return parse(src).stmts[0]


# ─────────────────────────────────────────────────────────────
#  Literals
# ─────────────────────────────────────────────────────────────

class TestLiteralParsing(unittest.TestCase):

    def test_integer_literal(self):
        node = first("42;")
        self.assertIsInstance(node, ExprStmtNode)
        lit = node.expr
        self.assertIsInstance(lit, LiteralNode)
        self.assertEqual(lit.value, 42)
        self.assertEqual(lit.kind, "int")

    def test_float_literal(self):
        lit = first("3.14;").expr
        self.assertEqual(lit.kind, "float")
        self.assertAlmostEqual(lit.value, 3.14)

    def test_string_literal(self):
        lit = first('"hello";').expr
        self.assertEqual(lit.kind, "string")
        self.assertEqual(lit.value, "hello")

    def test_true_literal(self):
        lit = first("true;").expr
        self.assertEqual(lit.kind, "bool")
        self.assertTrue(lit.value)

    def test_false_literal(self):
        lit = first("false;").expr
        self.assertFalse(lit.value)

    def test_array_literal(self):
        node = first("[1, 2, 3];").expr
        self.assertIsInstance(node, ArrayLiteralNode)
        self.assertEqual(len(node.elements), 3)

    def test_map_literal(self):
        node = first('{"a": 1, "b": 2};').expr
        self.assertIsInstance(node, MapLiteralNode)
        self.assertEqual(len(node.pairs), 2)

    def test_empty_array(self):
        node = first("[];").expr
        self.assertIsInstance(node, ArrayLiteralNode)
        self.assertEqual(len(node.elements), 0)


# ─────────────────────────────────────────────────────────────
#  Let bindings
# ─────────────────────────────────────────────────────────────

class TestLetStatement(unittest.TestCase):

    def test_let_integer(self):
        node = first("let x = 10;")
        self.assertIsInstance(node, LetNode)
        self.assertEqual(node.name, "x")
        self.assertEqual(node.value.value, 10)

    def test_let_string(self):
        node = first('let s = "hi";')
        self.assertEqual(node.name, "s")
        self.assertEqual(node.value.value, "hi")

    def test_let_expression(self):
        node = first("let r = 2 + 3;")
        self.assertIsInstance(node.value, BinOpNode)
        self.assertEqual(node.value.op, "+")

    def test_let_no_semicolon(self):
        # Semicolon is optional
        node = first("let x = 5")
        self.assertIsInstance(node, LetNode)


# ─────────────────────────────────────────────────────────────
#  Assignments
# ─────────────────────────────────────────────────────────────

class TestAssignment(unittest.TestCase):

    def test_simple_assign(self):
        node = first("x = 42;")
        self.assertIsInstance(node, AssignNode)
        self.assertIsInstance(node.name, IdentifierNode)
        self.assertEqual(node.name.name, "x")
        self.assertEqual(node.value.value, 42)


# ─────────────────────────────────────────────────────────────
#  Expressions — operators & precedence
# ─────────────────────────────────────────────────────────────

class TestExpressions(unittest.TestCase):

    def test_addition(self):
        node = first("1 + 2;").expr
        self.assertIsInstance(node, BinOpNode)
        self.assertEqual(node.op, "+")

    def test_precedence_mul_over_add(self):
        # 1 + 2 * 3  →  BinOp(+, 1, BinOp(*, 2, 3))
        node = first("1 + 2 * 3;").expr
        self.assertEqual(node.op, "+")
        self.assertIsInstance(node.right, BinOpNode)
        self.assertEqual(node.right.op, "*")

    def test_grouping_overrides_precedence(self):
        # (1 + 2) * 3  →  BinOp(*, BinOp(+, 1, 2), 3)
        node = first("(1 + 2) * 3;").expr
        self.assertEqual(node.op, "*")
        self.assertIsInstance(node.left, BinOpNode)
        self.assertEqual(node.left.op, "+")

    def test_unary_minus(self):
        node = first("-5;").expr
        self.assertIsInstance(node, UnaryOpNode)
        self.assertEqual(node.op, "-")

    def test_unary_bang(self):
        node = first("!true;").expr
        self.assertIsInstance(node, UnaryOpNode)
        self.assertEqual(node.op, "!")

    def test_comparison(self):
        node = first("x <= 10;").expr
        self.assertEqual(node.op, "<=")

    def test_equality(self):
        node = first("a == b;").expr
        self.assertEqual(node.op, "==")

    def test_logical_and(self):
        node = first("a && b;").expr
        self.assertEqual(node.op, "&&")

    def test_logical_or(self):
        node = first("a || b;").expr
        self.assertEqual(node.op, "||")


# ─────────────────────────────────────────────────────────────
#  Function declarations & calls
# ─────────────────────────────────────────────────────────────

class TestFunctions(unittest.TestCase):

    def test_fn_declaration(self):
        node = first("fn add(x, y) { return x + y; }")
        self.assertIsInstance(node, FnNode)
        self.assertEqual(node.name, "add")
        self.assertEqual(node.params, ["x", "y"])

    def test_fn_no_params(self):
        node = first("fn greet() { return 1; }")
        self.assertEqual(node.params, [])

    def test_fn_body(self):
        node = first("fn f(n) { return n; }")
        self.assertIsInstance(node.body, BlockNode)
        self.assertIsInstance(node.body.stmts[0], ReturnNode)

    def test_call_no_args(self):
        node = first("foo();").expr
        self.assertIsInstance(node, CallNode)
        self.assertEqual(len(node.args), 0)

    def test_call_with_args(self):
        node = first("add(1, 2);").expr
        self.assertIsInstance(node, CallNode)
        self.assertEqual(len(node.args), 2)

    def test_nested_call(self):
        node = first("f(g(1));").expr
        self.assertIsInstance(node, CallNode)
        self.assertIsInstance(node.args[0], CallNode)


# ─────────────────────────────────────────────────────────────
#  Control flow
# ─────────────────────────────────────────────────────────────

class TestControlFlow(unittest.TestCase):

    def test_if_only(self):
        node = first("if x { return 1; }")
        self.assertIsInstance(node, IfNode)
        self.assertIsNone(node.else_body)

    def test_if_else(self):
        node = first("if x { return 1; } else { return 2; }")
        self.assertIsInstance(node, IfNode)
        self.assertIsNotNone(node.else_body)

    def test_if_condition(self):
        node = first("if a == b { return 0; }")
        self.assertIsInstance(node.condition, BinOpNode)
        self.assertEqual(node.condition.op, "==")

    def test_while_loop(self):
        node = first("while i < 10 { i = i + 1; }")
        self.assertIsInstance(node, WhileNode)
        self.assertIsInstance(node.condition, BinOpNode)

    def test_for_loop(self):
        node = first("for x in myArray { let v = x; }")
        self.assertIsInstance(node, ForNode)
        self.assertEqual(node.var, "x")


# ─────────────────────────────────────────────────────────────
#  Return statement
# ─────────────────────────────────────────────────────────────

class TestReturn(unittest.TestCase):

    def test_return_value(self):
        node = first("fn f() { return 42; }").body.stmts[0]
        self.assertIsInstance(node, ReturnNode)
        self.assertEqual(node.value.value, 42)

    def test_return_no_value(self):
        node = first("fn f() { return; }").body.stmts[0]
        self.assertIsInstance(node, ReturnNode)
        self.assertIsNone(node.value)


# ─────────────────────────────────────────────────────────────
#  Indexing & attribute access
# ─────────────────────────────────────────────────────────────

class TestIndexing(unittest.TestCase):

    def test_array_index(self):
        node = first("arr[0];").expr
        self.assertIsInstance(node, IndexNode)
        self.assertEqual(node.index.value, 0)

    def test_dot_access(self):
        node = first("obj.name;").expr
        self.assertIsInstance(node, IndexNode)
        self.assertEqual(node.index.value, "name")


# ─────────────────────────────────────────────────────────────
#  Error handling
# ─────────────────────────────────────────────────────────────

class TestParseErrors(unittest.TestCase):

    def test_missing_rbrace(self):
        with self.assertRaises(ParseError):
            parse("if x { return 1;")

    def test_missing_rparen(self):
        with self.assertRaises(ParseError):
            parse("fn f(x { }")

    def test_unexpected_token(self):
        with self.assertRaises(ParseError):
            parse("let = 5;")


# ─────────────────────────────────────────────────────────────
#  to_dict / JSON serialisation
# ─────────────────────────────────────────────────────────────

class TestToDict(unittest.TestCase):

    def test_literal_to_dict(self):
        d = LiteralNode(42, "int").to_dict()
        self.assertEqual(d["node"], "Literal")
        self.assertEqual(d["value"], 42)

    def test_binop_to_dict(self):
        l = LiteralNode(1, "int")
        r = LiteralNode(2, "int")
        d = BinOpNode(l, "+", r).to_dict()
        self.assertEqual(d["op"], "+")
        self.assertIn("left", d)

    def test_program_to_dict(self):
        d = parse("let x = 1;").to_dict()
        self.assertEqual(d["node"], "Program")
        self.assertEqual(d["stmts"][0]["node"], "Let")


# ─────────────────────────────────────────────────────────────
#  Regex token validation
# ─────────────────────────────────────────────────────────────

class TestTokenValidation(unittest.TestCase):

    def _lex(self, src):
        from lexer import Lexer
        return list(Lexer(src).tokenize())

    def test_all_tokens_validate(self):
        from lexer import Lexer
        src = 'let x = 42; let s = "hi"; fn f(a) { return a + 1; }'
        tokens = list(Lexer(src).tokenize())
        meaningful = [t for t in tokens if t.type != TokenType.EOF]
        for tok in meaningful:
            self.assertTrue(validate_token(tok),
                            f"Token failed validation: {tok}")

    def test_integer_pattern(self):
        tok = self._lex("123")[0]
        self.assertTrue(validate_token(tok))

    def test_float_pattern(self):
        tok = self._lex("1.5")[0]
        self.assertTrue(validate_token(tok))

    def test_string_pattern(self):
        tok = self._lex('"hello"')[0]
        self.assertTrue(validate_token(tok))


# ─────────────────────────────────────────────────────────────
#  Full program integration
# ─────────────────────────────────────────────────────────────

class TestFullPrograms(unittest.TestCase):

    def test_fibonacci(self):
        src = """
        fn fibonacci(n) {
            if n <= 1 {
                return n;
            }
            return fibonacci(n - 1) + fibonacci(n - 2);
        }
        """
        tree = parse(src)
        self.assertEqual(len(tree.stmts), 1)
        self.assertIsInstance(tree.stmts[0], FnNode)

    def test_while_counter(self):
        src = """
        let i = 0;
        while i < 10 {
            i = i + 1;
        }
        """
        tree = parse(src)
        self.assertEqual(len(tree.stmts), 2)
        self.assertIsInstance(tree.stmts[0], LetNode)
        self.assertIsInstance(tree.stmts[1], WhileNode)

    def test_map_and_array(self):
        src = """
        let arr = [1, 2, 3];
        let m = {"key": "val"};
        """
        tree = parse(src)
        self.assertIsInstance(tree.stmts[0].value, ArrayLiteralNode)
        self.assertIsInstance(tree.stmts[1].value, MapLiteralNode)


if __name__ == "__main__":
    unittest.main(verbosity=2)
