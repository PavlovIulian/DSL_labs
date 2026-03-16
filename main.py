3import sys
from lexer import Lexer, LexerError


def tokenize_and_print(source: str) -> None:
    try:
        tokens = list(Lexer(source).tokenize())
        if not tokens:
            print("(no tokens)")
            return
        max_len = max(len(t.type.name) for t in tokens)
        for tok in tokens:
            loc  = f"[{tok.line:3d}:{tok.column:2d}]"
            name = tok.type.name.ljust(max_len)
            val  = f"  →  {tok.value!r}" if tok.value is not None else ""
            print(f"  {loc}  {name}{val}")
    except LexerError as e:
        print(f"\n  {e}\n")


def repl() -> None:
    print("Lexer REPL  (type 'exit' or Ctrl-C to quit)")
    print("─" * 45)
    while True:
        try:
            source = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if source.strip().lower() in ("exit", "quit"):
            print("Bye!")
            break
        tokenize_and_print(source)
        print()


def from_file(path: str) -> None:
    try:
        with open(path) as f:
            source = f.read()
    except FileNotFoundError:
        print(f"File not found: {path}")
        sys.exit(1)

    print(f"Tokenizing: {path}")
    print("─" * 45)
    tokenize_and_print(source)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        from_file(sys.argv[1])
    else:
        repl()
