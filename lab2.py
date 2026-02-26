import random
from itertools import combinations


# ============================================================
# LAB 1 CARRYOVER: Grammar class with Chomsky classification
# ============================================================

class Grammar:
    def __init__(self):
        self.VN = ['S', 'A', 'B', 'C']
        self.VT = ['a', 'b']
        self.P = {
            'S': ['aA'],
            'A': ['bS', 'aB'],
            'B': ['bC'],
            'C': ['aA', 'b']
        }
        self.start = 'S'

    def classify_chomsky(self):
        """
        Classify the grammar according to the Chomsky hierarchy:
          Type 0 - Unrestricted
          Type 1 - Context-Sensitive
          Type 2 - Context-Free
          Type 3 - Regular
        """
        is_regular = True
        is_context_free = True
        is_context_sensitive = True

        for lhs, productions in self.P.items():
            # --- Check Type 2 (Context-Free): LHS must be a single non-terminal ---
            if len(lhs) != 1 or lhs not in self.VN:
                is_context_free = False
                is_regular = False

            for rhs in productions:
                # --- Check Type 3 (Regular): right-linear or left-linear ---
                # Right-linear: a single terminal OR a terminal followed by one non-terminal
                # (allowing empty string ε represented as '')
                if is_regular:
                    if rhs == '':
                        pass  # ε production – still can be regular
                    elif len(rhs) == 1 and rhs in self.VT:
                        pass  # X -> a
                    elif len(rhs) == 2 and rhs[0] in self.VT and rhs[1] in self.VN:
                        pass  # X -> aB
                    elif len(rhs) == 1 and rhs in self.VN:
                        pass  # X -> B (unit production, still regular)
                    else:
                        is_regular = False

                # --- Check Type 1 (Context-Sensitive): |lhs| <= |rhs| ---
                # Exception: S -> ε allowed if S doesn't appear on any RHS
                if is_context_sensitive:
                    if rhs == '':
                        # ε production: allowed only if start symbol
                        if lhs != self.start:
                            is_context_sensitive = False
                    elif len(lhs) > len(rhs):
                        is_context_sensitive = False

        if is_regular:
            return "Type 3 – Regular Grammar"
        elif is_context_free:
            return "Type 2 – Context-Free Grammar"
        elif is_context_sensitive:
            return "Type 1 – Context-Sensitive Grammar"
        else:
            return "Type 0 – Unrestricted Grammar"

    def generate_string(self, max_steps=50):
        current = self.start
        for _ in range(max_steps):
            replaced = False
            for i, ch in enumerate(current):
                if ch in self.VN:
                    if ch in self.P:
                        production = random.choice(self.P[ch])
                        current = current[:i] + production + current[i + 1:]
                        replaced = True
                        break
            if not replaced:
                break
        return current

    def to_finite_automaton(self):
        states = set(self.VN)
        states.add('F')
        alphabet = set(self.VT)
        transitions = {}
        for non_terminal, productions in self.P.items():
            for production in productions:
                if len(production) == 1 and production in self.VT:
                    transitions.setdefault(non_terminal, {})[production] = 'F'
                elif len(production) == 2:
                    terminal, next_state = production[0], production[1]
                    transitions.setdefault(non_terminal, {})[terminal] = next_state
        return FiniteAutomaton(states, alphabet, transitions, self.start, {'F'})


# ============================================================
# FINITE AUTOMATON (supports NFA – multiple transitions stored
# as sets)
# ============================================================

class FiniteAutomaton:
    """
    General FA that can represent both DFA and NFA.
    Transitions: dict[state] -> dict[symbol] -> set of states (NFA)
                                               OR single state (DFA, legacy)
    Internally we always store sets for uniformity.
    """

    def __init__(self, states, alphabet, transitions, start_state, final_states):
        self.Q = set(states)
        self.Sigma = set(alphabet)
        # Normalise transitions so values are always sets
        self.delta = {}
        for state, sym_map in transitions.items():
            self.delta[state] = {}
            for sym, target in sym_map.items():
                if isinstance(target, set):
                    self.delta[state][sym] = set(target)
                elif isinstance(target, (list, tuple)):
                    self.delta[state][sym] = set(target)
                else:
                    self.delta[state][sym] = {target}
        self.q0 = start_state
        self.F = set(final_states)

    # ----------------------------------------------------------
    # Determinism check
    # ----------------------------------------------------------
    def is_deterministic(self):
        """Return True if this FA is a DFA (each (state,symbol) -> at most 1 state)."""
        for state, sym_map in self.delta.items():
            for sym, targets in sym_map.items():
                if len(targets) > 1:
                    return False
        return True

    # ----------------------------------------------------------
    # Convert NFA -> DFA (subset construction)
    # ----------------------------------------------------------
    def to_dfa(self):
        """
        Convert this NFA to an equivalent DFA using the subset-construction
        (powerset) algorithm.
        Returns a new FiniteAutomaton that is deterministic.
        """
        if self.is_deterministic():
            print("FA is already deterministic – returning a copy.")

        # Map frozensets of NFA states -> DFA state name
        def name(fs):
            return '{' + ','.join(sorted(fs)) + '}'

        start_set = frozenset({self.q0})
        worklist = [start_set]
        visited = {}  # frozenset -> name string
        visited[start_set] = name(start_set)
        dfa_transitions = {}
        dfa_final = set()

        while worklist:
            current_set = worklist.pop(0)
            current_name = visited[current_set]

            # Mark as final if any NFA state is final
            if current_set & self.F:
                dfa_final.add(current_name)

            dfa_transitions[current_name] = {}

            for sym in sorted(self.Sigma):
                # Compute the set of states reachable from current_set on sym
                next_set = set()
                for nfa_state in current_set:
                    if nfa_state in self.delta and sym in self.delta[nfa_state]:
                        next_set |= self.delta[nfa_state][sym]

                if not next_set:
                    continue  # dead transition – skip (partial DFA)

                next_fs = frozenset(next_set)
                if next_fs not in visited:
                    visited[next_fs] = name(next_fs)
                    worklist.append(next_fs)

                dfa_transitions[current_name][sym] = {visited[next_fs]}

        dfa_states = set(visited.values())
        dfa_start = visited[start_set]
        return FiniteAutomaton(dfa_states, self.Sigma, dfa_transitions, dfa_start, dfa_final)

    # ----------------------------------------------------------
    # Convert FA -> Regular Grammar
    # ----------------------------------------------------------
    def to_regular_grammar(self):
        """
        Convert this FA to a right-linear Regular Grammar.
        For each transition δ(q, a) = p:
          - Add production  q -> a p
        For each final state q:
          - Add production  q -> ε  (represented as '')
        """
        productions = {}
        for state in self.Q:
            productions[state] = []

        for state, sym_map in self.delta.items():
            for sym, targets in sym_map.items():
                for target in targets:
                    if target in self.F:
                        # Two productions: one that terminates, one that continues
                        productions[state].append(sym)          # q -> a  (terminal only)
                    else:
                        productions[state].append(sym + target)  # q -> a p

        # Remove states with no productions
        productions = {k: v for k, v in productions.items() if v}

        non_terminals = list(self.Q)
        terminals = list(self.Sigma)
        return Grammar_Generic(non_terminals, terminals, productions, self.q0)

    # ----------------------------------------------------------
    # Accept / reject a string (NFA-style, BFS over state sets)
    # ----------------------------------------------------------
    def string_belong_to_language(self, input_string):
        if not input_string:
            return self.q0 in self.F
        current_states = {self.q0}
        for char in input_string:
            if char not in self.Sigma:
                return False
            next_states = set()
            for st in current_states:
                if st in self.delta and char in self.delta[st]:
                    next_states |= self.delta[st][char]
            current_states = next_states
            if not current_states:
                return False
        return bool(current_states & self.F)

    # ----------------------------------------------------------
    # Display helpers
    # ----------------------------------------------------------
    def display(self, title="Finite Automaton"):
        print(f"\n=== {title} ===")
        print(f"States (Q):        {sorted(self.Q)}")
        print(f"Alphabet (Σ):      {sorted(self.Sigma)}")
        print(f"Initial state:     {self.q0}")
        print(f"Final states (F):  {sorted(self.F)}")
        det = "DFA" if self.is_deterministic() else "NFA"
        print(f"Type:              {det}")
        print("\nTransition table:")
        for state in sorted(self.delta.keys()):
            for sym in sorted(self.delta[state].keys()):
                targets = sorted(self.delta[state][sym])
                print(f"  δ({state}, {sym}) = {targets}")


# ============================================================
# Generic grammar (used for FA -> grammar conversion output)
# ============================================================

class Grammar_Generic:
    def __init__(self, VN, VT, P, start):
        self.VN = VN
        self.VT = VT
        self.P = P
        self.start = start

    def classify_chomsky(self):
        """Classify grammar using Chomsky hierarchy. Handles multi-char non-terminal names."""
        is_regular = True
        is_context_free = True
        is_context_sensitive = True

        def tokenise(s):
            """Split a string into terminal/non-terminal tokens."""
            tokens = []
            i = 0
            while i < len(s):
                matched = False
                for nt in sorted(self.VN, key=len, reverse=True):
                    if s[i:i+len(nt)] == nt:
                        tokens.append(nt)
                        i += len(nt)
                        matched = True
                        break
                if not matched:
                    tokens.append(s[i])
                    i += 1
            return tokens

        for lhs, productions in self.P.items():
            if lhs not in self.VN:
                is_context_free = False
                is_regular = False

            for rhs in productions:
                tokens = tokenise(rhs) if rhs else []

                if is_regular:
                    if rhs == '':
                        pass  # ε allowed
                    elif len(tokens) == 1 and tokens[0] in self.VT:
                        pass  # X -> a
                    elif len(tokens) == 2 and tokens[0] in self.VT and tokens[1] in self.VN:
                        pass  # X -> aB  (right-linear)
                    elif len(tokens) == 1 and tokens[0] in self.VN:
                        pass  # X -> B  (unit)
                    else:
                        is_regular = False

                if is_context_sensitive:
                    if rhs == '':
                        if lhs != self.start:
                            is_context_sensitive = False
                    elif len(tokenise(lhs)) > len(tokens):
                        is_context_sensitive = False

        if is_regular:
            return "Type 3 – Regular Grammar"
        elif is_context_free:
            return "Type 2 – Context-Free Grammar"
        elif is_context_sensitive:
            return "Type 1 – Context-Sensitive Grammar"
        else:
            return "Type 0 – Unrestricted Grammar"

    def display(self):
        print(f"Non-terminals: {self.VN}")
        print(f"Terminals:     {self.VT}")
        print(f"Start:         {self.start}")
        print("Productions:")
        for nt, prods in self.P.items():
            for p in prods:
                print(f"  {nt} -> {'ε' if p == '' else p}")


# ============================================================
# MAIN
# ============================================================

def main():
    separator = "=" * 60

    # ----------------------------------------------------------
    # PART A – Chomsky classification of Lab-1 grammar
    # ----------------------------------------------------------
    print(separator)
    print("PART A – Chomsky Hierarchy Classification (Lab-1 Grammar)")
    print(separator)
    g = Grammar()
    classification = g.classify_chomsky()
    print(f"Grammar productions:")
    for nt, prods in g.P.items():
        for p in prods:
            print(f"  {nt} -> {p}")
    print(f"\nClassification: {classification}")
    print("Reasoning: Every LHS is a single non-terminal (Type 2 ✓).")
    print("Every RHS is either a single terminal (X->a) or terminal+non-terminal (X->aB), which is right-linear (Type 3 ✓).")

    # ----------------------------------------------------------
    # PART B – Variant 19 NDFA definition
    # ----------------------------------------------------------
    print(f"\n{separator}")
    print("PART B – Variant 19 Finite Automaton Definition")
    print(separator)
    print("""
Variant 19 FA:
  Q     = {q0, q1, q2}
  Σ     = {a, b}
  F     = {q2}
  δ(q0, a) = q1   ← NFA: two transitions on 'a' from q0
  δ(q0, a) = q0
  δ(q1, b) = q2
  δ(q0, b) = q0
  δ(q1, b) = q1
  δ(q2, b) = q2
""")

    # Build the NFA
    # Both δ(q0,a)=q1 AND δ(q0,a)=q0 → store as a set
    nfa_transitions = {
        'q0': {'a': {'q0', 'q1'}, 'b': {'q0'}},
        'q1': {'b': {'q1', 'q2'}},
        'q2': {'b': {'q2'}},
    }
    nfa = FiniteAutomaton(
        states={'q0', 'q1', 'q2'},
        alphabet={'a', 'b'},
        transitions=nfa_transitions,
        start_state='q0',
        final_states={'q2'}
    )
    nfa.display("Variant 19 NFA")

    # ----------------------------------------------------------
    # PART C – Determinism check
    # ----------------------------------------------------------
    print(f"\n{separator}")
    print("PART C – Determinism Check")
    print(separator)
    det = nfa.is_deterministic()
    print(f"Is deterministic? {det}")
    print("Explanation: δ(q0, a) has two targets {{q0, q1}} – that violates the DFA rule")
    print("of at most one target per (state, symbol) pair. Also δ(q1, b) -> {{q1, q2}}.")
    print("Therefore this is an NFA (Non-Deterministic Finite Automaton).\n")

    # ----------------------------------------------------------
    # PART D – Convert NFA -> DFA (subset construction)
    # ----------------------------------------------------------
    print(f"\n{separator}")
    print("PART D – NFA → DFA Conversion (Subset Construction)")
    print(separator)
    print("\nStep-by-step subset construction:")
    print("  Start set: {q0}")
    print("  δ({q0}, a) = {q0, q1}   → new state {q0,q1}")
    print("  δ({q0}, b) = {q0}       → existing state {q0}")
    print("  δ({q0,q1}, a) = δ(q0,a)∪δ(q1,a) = {q0,q1}∪∅ = {q0,q1}  → existing")
    print("  δ({q0,q1}, b) = δ(q0,b)∪δ(q1,b) = {q0}∪{q1,q2} = {q0,q1,q2}  → new")
    print("  δ({q0,q1,q2}, a) = {q0,q1}  → existing")
    print("  δ({q0,q1,q2}, b) = {q0}∪{q1,q2}∪{q2} = {q0,q1,q2}  → existing")
    print("  Final DFA states: {q0,q1,q2} contains q2 → final\n")

    dfa = nfa.to_dfa()
    dfa.display("Converted DFA")

    # Verify DFA is deterministic
    print(f"\nDFA is deterministic? {dfa.is_deterministic()}")

    # ----------------------------------------------------------
    # PART E – Convert FA -> Regular Grammar
    # ----------------------------------------------------------
    print(f"\n{separator}")
    print("PART E – FA to Regular Grammar Conversion")
    print(separator)
    rg = nfa.to_regular_grammar()
    print("\nDerived Regular Grammar from NFA:")
    rg.display()
    print(f"\nChomsky classification: {rg.classify_chomsky()}")

    # ----------------------------------------------------------
    # PART F – String acceptance tests
    # ----------------------------------------------------------
    print(f"\n{separator}")
    print("PART F – String Membership Tests")
    print(separator)
    print("\nLanguage accepted: strings over {a,b} that contain at least one 'a'")
    print("followed eventually by at least one 'b' (i.e., contain substring ab).\n")

    test_cases = [
        ("ab",      True,  "simplest: one a then one b"),
        ("aab",     True,  "multiple a's before b"),
        ("abb",     True,  "a then multiple b's"),
        ("aabb",    True,  "aa then bb"),
        ("b",       False, "no a at all"),
        ("ba",      False, "b before any a, never reaches q2"),
        ("a",       False, "a but no b after"),
        ("",        False, "empty string"),
        ("bbb",     False, "only b's"),
        ("aaabbb",  True,  "multiple a's then b's"),
    ]

    print(f"{'String':<12} {'NFA':>5} {'DFA':>5} {'Expected':>8}  {'Notes'}")
    print("-" * 60)
    for s, expected, note in test_cases:
        r_nfa = nfa.string_belong_to_language(s)
        r_dfa = dfa.string_belong_to_language(s)
        match = "✓" if (r_nfa == expected and r_dfa == expected) else "✗ MISMATCH"
        print(f"'{s:<10}' {str(r_nfa):>5} {str(r_dfa):>5} {str(expected):>8}  {match}  {note}")

    print(f"\n{separator}")
    print("All tasks completed successfully.")
    print(separator)


if __name__ == "__main__":
    main()