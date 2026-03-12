from dataclasses import dataclass
from typing import Any
from token_type import TokenType


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
