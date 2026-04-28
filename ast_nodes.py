"""
ast_nodes.py — AST node hierarchy for the RoboScript-like language.

Every node is a frozen dataclass that extends ASTNode.
All nodes implement:
  - to_dict()  → JSON-serialisable dict
  - __str__()  → human-readable one-liner
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


# ──────────────────────────────────────────────────────────────────────────────
#  Base
# ──────────────────────────────────────────────────────────────────────────────

class ASTNode:
    """Abstract base for every node in the tree."""

    def to_dict(self) -> dict:
        raise NotImplementedError

    def __str__(self) -> str:
        return repr(self)


# ──────────────────────────────────────────────────────────────────────────────
#  Expressions
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class LiteralNode(ASTNode):
    """An integer, float, string, or boolean constant."""
    value: Any
    kind:  str        # 'int' | 'float' | 'string' | 'bool' | 'nil'

    def to_dict(self):
        return {"node": "Literal", "kind": self.kind, "value": self.value}

    def __str__(self):
        return f"Literal({self.kind}) {self.value!r}"


@dataclass
class IdentifierNode(ASTNode):
    """A reference to a named symbol."""
    name: str

    def to_dict(self):
        return {"node": "Identifier", "name": self.name}

    def __str__(self):
        return f"Identifier {self.name!r}"


@dataclass
class BinOpNode(ASTNode):
    """Binary expression: left <op> right."""
    left:  ASTNode
    op:    str
    right: ASTNode

    def to_dict(self):
        return {"node": "BinOp", "op": self.op,
                "left": self.left.to_dict(), "right": self.right.to_dict()}

    def __str__(self):
        return f"BinOp {self.op!r}"


@dataclass
class UnaryOpNode(ASTNode):
    """Unary expression: <op> operand."""
    op:      str
    operand: ASTNode

    def to_dict(self):
        return {"node": "UnaryOp", "op": self.op,
                "operand": self.operand.to_dict()}

    def __str__(self):
        return f"UnaryOp {self.op!r}"


@dataclass
class CallNode(ASTNode):
    """Function call: callee(args…)."""
    callee: ASTNode          # usually IdentifierNode
    args:   list[ASTNode] = field(default_factory=list)

    def to_dict(self):
        return {"node": "Call", "callee": self.callee.to_dict(),
                "args": [a.to_dict() for a in self.args]}

    def __str__(self):
        return f"Call {self.callee}"


@dataclass
class IndexNode(ASTNode):
    """Array/map index: collection[index]."""
    collection: ASTNode
    index:      ASTNode

    def to_dict(self):
        return {"node": "Index",
                "collection": self.collection.to_dict(),
                "index": self.index.to_dict()}

    def __str__(self):
        return f"Index"


@dataclass
class ArrayLiteralNode(ASTNode):
    """Array literal: [elem, …]."""
    elements: list[ASTNode] = field(default_factory=list)

    def to_dict(self):
        return {"node": "ArrayLiteral",
                "elements": [e.to_dict() for e in self.elements]}

    def __str__(self):
        return f"ArrayLiteral [{len(self.elements)} elems]"


@dataclass
class MapLiteralNode(ASTNode):
    """Map / object literal: {{key: value, …}}."""
    pairs: list[tuple[ASTNode, ASTNode]] = field(default_factory=list)

    def to_dict(self):
        return {"node": "MapLiteral",
                "pairs": [{"key": k.to_dict(), "value": v.to_dict()}
                           for k, v in self.pairs]}

    def __str__(self):
        return f"MapLiteral {{{len(self.pairs)} pairs}}"


# ──────────────────────────────────────────────────────────────────────────────
#  Statements
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class LetNode(ASTNode):
    """Variable binding: let name = value;"""
    name:  str
    value: ASTNode

    def to_dict(self):
        return {"node": "Let", "name": self.name,
                "value": self.value.to_dict()}

    def __str__(self):
        return f"Let {self.name!r}"


@dataclass
class AssignNode(ASTNode):
    """Assignment: name = value;  (name already declared)."""
    name:  ASTNode       # IdentifierNode or IndexNode
    value: ASTNode

    def to_dict(self):
        return {"node": "Assign",
                "name": self.name.to_dict(),
                "value": self.value.to_dict()}

    def __str__(self):
        return f"Assign"


@dataclass
class ReturnNode(ASTNode):
    """return [expr];"""
    value: Optional[ASTNode] = None

    def to_dict(self):
        return {"node": "Return",
                "value": self.value.to_dict() if self.value else None}

    def __str__(self):
        return "Return"


@dataclass
class ExprStmtNode(ASTNode):
    """An expression used as a statement (discards its value)."""
    expr: ASTNode

    def to_dict(self):
        return {"node": "ExprStmt", "expr": self.expr.to_dict()}

    def __str__(self):
        return f"ExprStmt"


@dataclass
class BlockNode(ASTNode):
    """A brace-enclosed sequence of statements."""
    stmts: list[ASTNode] = field(default_factory=list)

    def to_dict(self):
        return {"node": "Block", "stmts": [s.to_dict() for s in self.stmts]}

    def __str__(self):
        return f"Block [{len(self.stmts)} stmts]"


@dataclass
class IfNode(ASTNode):
    """if condition { then_body } [else { else_body }]"""
    condition: ASTNode
    then_body: BlockNode
    else_body: Optional[BlockNode] = None

    def to_dict(self):
        d: dict = {"node": "If",
                   "condition": self.condition.to_dict(),
                   "then": self.then_body.to_dict()}
        if self.else_body:
            d["else"] = self.else_body.to_dict()
        return d

    def __str__(self):
        return "If"


@dataclass
class WhileNode(ASTNode):
    """while condition { body }"""
    condition: ASTNode
    body:      BlockNode

    def to_dict(self):
        return {"node": "While",
                "condition": self.condition.to_dict(),
                "body": self.body.to_dict()}

    def __str__(self):
        return "While"


@dataclass
class ForNode(ASTNode):
    """for identifier in iterable { body }"""
    var:      str
    iterable: ASTNode
    body:     BlockNode

    def to_dict(self):
        return {"node": "For", "var": self.var,
                "iterable": self.iterable.to_dict(),
                "body": self.body.to_dict()}

    def __str__(self):
        return f"For {self.var!r}"


@dataclass
class FnNode(ASTNode):
    """fn name(params) { body }"""
    name:   str
    params: list[str]
    body:   BlockNode

    def to_dict(self):
        return {"node": "Fn", "name": self.name,
                "params": self.params, "body": self.body.to_dict()}

    def __str__(self):
        return f"Fn {self.name!r}({', '.join(self.params)})"


@dataclass
class ProgramNode(ASTNode):
    """Root node — the entire program."""
    stmts: list[ASTNode] = field(default_factory=list)

    def to_dict(self):
        return {"node": "Program",
                "stmts": [s.to_dict() for s in self.stmts]}

    def __str__(self):
        return f"Program [{len(self.stmts)} stmts]"
