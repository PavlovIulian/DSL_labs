from grammar import Grammar


def variant19_grammar() -> Grammar:
    VN = {'S', 'A', 'B', 'C', 'E'}
    VT = {'a', 'd'}
    P = {
        'S': ['dB', 'B'],
        'A': ['d', 'dS', 'aAdCB'],
        'B': ['aC', 'bA', 'AC'],
        'C': ['ε'],
        'E': ['AS'],
    }
    return Grammar(VN, VT, P, 'S')


# ──────────────────────────────────────────────
#  Extra test grammar (bonus – accepts any grammar)
# ──────────────────────────────────────────────
def extra_grammar() -> Grammar:
    """A simple grammar to show the converter works generically."""
    VN = {'S', 'A', 'B'}
    VT = {'a', 'b'}
    P = {
        'S': ['AB', 'ε'],
        'A': ['aA', 'ε'],
        'B': ['bB', 'b'],
    }
    return Grammar(VN, VT, P, 'S')


# ──────────────────────────────────────────────
#  Runner
# ──────────────────────────────────────────────
def main():
    separator = "\n" + "█" * 60 + "\n"

    print(separator)
    print("  VARIANT 19 GRAMMAR")
    print(separator)

    g = variant19_grammar()
    print("Original grammar:")
    print(g)

    g.normalize(verbose=True)

    print(separator)
    print("  FINAL CNF GRAMMAR")
    print(separator)
    print(g)

    # ── Bonus: run on a second grammar ─────────────────────
    print(separator)
    print("  BONUS – EXTRA GRAMMAR")
    print(separator)

    g2 = extra_grammar()
    print("Original grammar:")
    print(g2)
    g2.normalize(verbose=True)

    print(separator)
    print("  FINAL CNF (extra grammar)")
    print(separator)
    print(g2)


if __name__ == '__main__':
    main()
