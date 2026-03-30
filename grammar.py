"""
Chomsky Normal Form (CNF) Converter
Variant 19 - Formal Languages & Finite Automata Lab 4

Productions are stored as lists of symbol strings internally,
printed as joined strings for readability.
"""

from copy import deepcopy


class Grammar:
    """
    Represents a Context-Free Grammar and provides methods
    to convert it to Chomsky Normal Form (CNF).

    Productions are stored as:
        P: dict[str, list[list[str]]]
    where each inner list is an ordered list of symbols (terminals or non-terminals).
    The special empty production is represented as [].
    """

    def __init__(self, VN: set, VT: set, P: dict, S: str):
        self.VN = set(VN)
        self.VT = set(VT)
        self.S = S

        # Normalise P to list[list[str]]
        self.P: dict = {}
        for lhs, rhs_list in P.items():
            self.P[lhs] = []
            for rhs in rhs_list:
                if isinstance(rhs, list):
                    self.P[lhs].append(rhs[:])
                else:
                    if rhs == 'ε':
                        self.P[lhs].append([])
                    else:
                        self.P[lhs].append(list(rhs))

    def _clone(self):
        return {A: [r[:] for r in rhs] for A, rhs in self.P.items()}

    # ── Step 1 ─────────────────────────────────────────────────────── #
    def eliminate_epsilon(self):
        nullable = set()
        changed = True
        while changed:
            changed = False
            for A, prods in self.P.items():
                if A in nullable:
                    continue
                for prod in prods:
                    if prod == [] or all(s in nullable for s in prod):
                        nullable.add(A)
                        changed = True

        new_P = {}
        for A, prods in self.P.items():
            new_set = []
            for prod in prods:
                if prod == []:
                    continue
                nullable_pos = [i for i, s in enumerate(prod) if s in nullable]
                for mask in range(1 << len(nullable_pos)):
                    to_remove = {nullable_pos[j] for j in range(len(nullable_pos)) if mask & (1 << j)}
                    new_prod = [s for i, s in enumerate(prod) if i not in to_remove]
                    if new_prod and new_prod not in new_set:
                        new_set.append(new_prod)
            new_P[A] = new_set

        if self.S in nullable:
            new_P[self.S].append([])

        self.P = new_P

    # ── Step 2 ─────────────────────────────────────────────────────── #
    def eliminate_unit_productions(self):
        changed = True
        while changed:
            changed = False
            new_P = self._clone()
            for A, prods in self.P.items():
                for prod in prods:
                    if len(prod) == 1 and prod[0] in self.VN:
                        new_P[A] = [p for p in new_P[A] if p != prod]
                        for bp in self.P.get(prod[0], []):
                            if bp not in new_P[A]:
                                new_P[A].append(bp[:])
                        changed = True
            self.P = new_P

    # ── Step 3 ─────────────────────────────────────────────────────── #
    def eliminate_inaccessible(self):
        accessible = {self.S}
        changed = True
        while changed:
            changed = False
            for A in list(accessible):
                for prod in self.P.get(A, []):
                    for sym in prod:
                        if sym in self.VN and sym not in accessible:
                            accessible.add(sym)
                            changed = True

        self.VN = self.VN & accessible
        self.P = {A: prods for A, prods in self.P.items() if A in accessible}

    # ── Step 4 ─────────────────────────────────────────────────────── #
    def eliminate_nonproductive(self):
        productive = set()
        changed = True
        while changed:
            changed = False
            for A, prods in self.P.items():
                if A in productive:
                    continue
                for prod in prods:
                    if all(s in self.VT or s in productive for s in prod):
                        productive.add(A)
                        changed = True

        self.VN = self.VN & productive
        new_P = {}
        for A in productive:
            if A in self.P:
                new_prods = [
                    prod for prod in self.P[A]
                    if all(s in self.VT or s in productive for s in prod)
                ]
                if new_prods:
                    new_P[A] = new_prods
        self.P = new_P

    # ── Step 5 ─────────────────────────────────────────────────────── #
    def to_cnf(self):
        terminal_map = {}
        extra_rules = {}
        counter = [0]

        def fresh_nt():
            while True:
                counter[0] += 1
                name = f"X{counter[0]}"
                if name not in self.VN and name not in extra_rules:
                    return name

        def terminal_nt(t):
            if t not in terminal_map:
                base = f"T{t.upper()}"
                nt = base
                n = 0
                while nt in self.VN or nt in extra_rules:
                    n += 1
                    nt = f"{base}{n}"
                terminal_map[t] = nt
                extra_rules[nt] = [[t]]
                self.VN.add(nt)
            return terminal_map[t]

        def binarize(syms):
            if len(syms) <= 2:
                return syms[:]
            rest_nt = fresh_nt()
            self.VN.add(rest_nt)
            extra_rules[rest_nt] = [binarize(syms[1:])]
            return [syms[0], rest_nt]

        new_P = {}
        for A, prods in self.P.items():
            new_prods = []
            for prod in prods:
                if prod == []:
                    new_prods.append([])
                    continue
                if len(prod) == 1:
                    new_prods.append(prod[:])
                    continue
                seq = [terminal_nt(s) if s in self.VT else s for s in prod]
                if len(seq) > 2:
                    seq = binarize(seq)
                new_prods.append(seq)
            new_P[A] = new_prods

        new_P.update(extra_rules)
        self.P = new_P

    # ── Pipeline ───────────────────────────────────────────────────── #
    def normalize(self, verbose=True):
        steps = [
            (self.eliminate_epsilon,          "Step 1: Eliminate ε-productions"),
            (self.eliminate_unit_productions, "Step 2: Eliminate unit productions"),
            (self.eliminate_inaccessible,     "Step 3: Eliminate inaccessible symbols"),
            (self.eliminate_nonproductive,    "Step 4: Eliminate non-productive symbols"),
            (self.to_cnf,                     "Step 5: Convert to CNF"),
        ]
        for fn, label in steps:
            fn()
            if verbose:
                print(f"\n{'='*55}")
                print(label)
                print(self)

    # ── Repr ───────────────────────────────────────────────────────── #
    def _prod_str(self, prod):
        return 'ε' if prod == [] else ' '.join(prod)

    def __repr__(self):
        lines = [
            "G = (VN, VT, P, S)",
            f"VN = {{{', '.join(sorted(self.VN))}}}",
            f"VT = {{{', '.join(sorted(self.VT))}}}",
            f"S  = {self.S}",
            "P:",
        ]
        for A in sorted(self.P):
            prods = self.P[A]
            if prods:
                rhs = ' | '.join(self._prod_str(p) for p in sorted(prods, key=self._prod_str))
                lines.append(f"  {A} → {rhs}")
        return '\n'.join(lines)
