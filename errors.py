class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"[Line {line}, Col {column}] LexerError: {message}")
