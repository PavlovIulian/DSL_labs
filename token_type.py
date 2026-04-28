from enum import Enum, auto


class TokenType(Enum):
    # Literals
    INTEGER    = auto()
    FLOAT      = auto()
    STRING     = auto()
    IDENTIFIER = auto()

    # Keywords
    LET        = auto()
    FN         = auto()
    RETURN     = auto()
    IF         = auto()
    ELSE       = auto()
    TRUE       = auto()
    FALSE      = auto()
    WHILE      = auto()
    FOR        = auto()

    # Trigonometric functions
    SIN        = auto()
    COS        = auto()

    # Math operators
    PLUS       = auto()
    MINUS      = auto()
    STAR       = auto()
    SLASH      = auto()
    PERCENT    = auto()
    CARET      = auto()

    # Comparison operators
    EQ         = auto()   # ==
    NEQ        = auto()   # !=
    LT         = auto()   # <
    GT         = auto()   # >
    LTE        = auto()   # <=
    GTE        = auto()   # >=

    # Assignment
    ASSIGN     = auto()   # =

    # Logical
    AND        = auto()   # &&
    OR         = auto()   # ||
    BANG       = auto()   # !

    # Delimiters
    LPAREN     = auto()   # (
    RPAREN     = auto()   # )
    LBRACE     = auto()   # {
    RBRACE     = auto()   # }
    LBRACKET   = auto()   # [
    RBRACKET   = auto()   # ]
    COMMA      = auto()   # ,
    SEMICOLON  = auto()   # ;
    COLON      = auto()   # :
    DOT        = auto()   # .

    # Special
    EOF        = auto()
    ILLEGAL    = auto()