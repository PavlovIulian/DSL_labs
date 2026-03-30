import random

from parser import RegexParser
from generator import generate_string, generate_with_trace

# ── Variant 1 patterns ────────────────────────────────────────────
PATTERNS = [
 "(a|b)(c|d)E^+G?\n"
 "P(Q|R|S)T(UV|W|X)^*Z^+\n"
 "1(0|1)^*2(3|4)^5*36"
]


def main():
    random.seed(42)

    print("=" * 60)
    print("  Lab 4 — Variant 1  |  Regular Expression Generator")
    print("=" * 60)

    # ── Sample outputs ────────────────────────────────────────────
    for pattern in PATTERNS:
        ast = RegexParser(pattern).parse()
        samples = [generate_string(ast) for _ in range(6)]
        print(f"\nPattern : {pattern}")
        print(f"Samples : {samples}")

    # ── Step-by-step traces ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Processing traces (one example per pattern)")
    print("=" * 60)

    for pattern in PATTERNS:
        ast = RegexParser(pattern).parse()
        result, steps = generate_with_trace(ast, seed=7)
        print(f"\nPattern : {pattern}")
        print(f"Result  : {result}")
        print("Trace   :")
        for step in steps:
            print(step)


if __name__ == "__main__":
    main()
