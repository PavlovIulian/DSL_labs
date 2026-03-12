"""
examples/demo.py — Demonstrates the lexer on several code snippets.
Run from the project root:  python examples/demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lexer import Lexer, TokenType

DIVIDER = "─" * 60

SAMPLES = {
    "Variable binding": """\
let age = 1;
let name = "Alice";
let result = 10 * (20 / 2);
""",

    "Array & map literals": """\
let myArray = [0, 1, 2, 3, 4, 5];
let map = {"name": "First_Name", "age": 28};
""",

    "Function declaration & call": """\
fn add(first, second) {
    return first + second;
}

let sum = add(2, 4);
""",

    "If / else": """\
if x == 0 {
    return false;
} else {
    return true;
}
""",

    "Fibonacci (recursive)": """\
fn fibonacci(n) {
    if n <= 1 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}
""",

    "Comments": """\
// single-line comment — ignored
let x = 42; /* multi-line
                comment */
let y = x + 1;
""",
}


def print_tokens(source: str) -> None:
    tokens = list(Lexer(source).tokenize())
    max_type_len = max(len(t.type.name) for t in tokens)
    for tok in tokens:
        location = f"[{tok.line:2d}:{tok.column:2d}]"
        type_str  = tok.type.name.ljust(max_type_len)
        value_str = repr(tok.value) if tok.value is not None else ""
        print(f"  {location}  {type_str}  {value_str}")


def main() -> None:
    for title, source in SAMPLES.items():
        print(DIVIDER)
        print(f"  {title}")
        print(DIVIDER)
        print("  Source:")
        for line in source.splitlines():
            print(f"    {line}")
        print()
        print("  Tokens:")
        try:
            print_tokens(source)
        except Exception as e:
            print(f"  ERROR: {e}")
        print()


if __name__ == "__main__":
    main()
