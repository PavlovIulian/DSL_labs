from itertools import chain
from grammar import Grammar


class FiniteAutomaton:

    def __init__(self, states: set, alphabet: set, transitions: dict,
                 start: str, final_states: set):
        self.states = set(states)
        self.alphabet = set(alphabet)
        # Normalise transitions to {(state, symbol): set}
        self.transitions: dict[tuple, set] = {}
        for key, val in transitions.items():
            self.transitions[key] = set(val) if not isinstance(val, set) else val
        self.start = start
        self.final_states = set(final_states)

    # ------------------------------------------------------------------
    # 1. Convert FA -> Regular Grammar
    # ------------------------------------------------------------------

    def to_regular_grammar(self) -> Grammar:

        # Build a mapping from state name to non-terminal symbol
        state_to_nt: dict[str, str] = {}
        for state in sorted(self.states):
            # Use the state name directly; capitalise first letter for clarity
            nt = state[0].upper() + state[1:]
            state_to_nt[state] = nt

        non_terminals = set(state_to_nt.values())
        terminals = set(self.alphabet)
        start_nt = state_to_nt[self.start]
        productions: dict[str, list] = {nt: [] for nt in non_terminals}

        for (state, symbol), next_states in self.transitions.items():
            nt = state_to_nt[state]
            for next_state in next_states:
                next_nt = state_to_nt[next_state]
                # A -> aB
                productions[nt].append(f"{symbol}{next_nt}")
                # If next_state is final also add A -> a  (accept here)
                if next_state in self.final_states:
                    productions[nt].append(symbol)

        # If the start state itself is final, add S -> ε
        if self.start in self.final_states:
            productions[start_nt].append("ε")

        # Remove duplicate productions
        for nt in productions:
            productions[nt] = list(dict.fromkeys(productions[nt]))

        return Grammar(non_terminals, terminals, productions, start_nt)

    # ------------------------------------------------------------------
    # 2. Determinism check
    # ------------------------------------------------------------------

    def is_deterministic(self) -> bool:
        for (state, symbol), next_states in self.transitions.items():
            if symbol == "ε":
                return False
            if len(next_states) > 1:
                return False
        return True

    # ------------------------------------------------------------------
    # 3. NDFA -> DFA  (subset / powerset construction)
    # ------------------------------------------------------------------

    def to_dfa(self) -> "FiniteAutomaton":

        # Each DFA state is a frozenset of NDFA states
        start_set = frozenset({self.start})
        dfa_transitions: dict[tuple, set] = {}
        dfa_states: set[frozenset] = set()
        worklist: list[frozenset] = [start_set]
        visited: set[frozenset] = set()

        while worklist:
            current = worklist.pop()
            if current in visited:
                continue
            visited.add(current)
            dfa_states.add(current)

            for symbol in sorted(self.alphabet):
                if symbol == "ε":
                    continue
                # Union of all reachable NDFA states
                reachable: set = set()
                for ndfa_state in current:
                    reachable |= self.transitions.get((ndfa_state, symbol), set())

                if not reachable:
                    continue

                next_frozen = frozenset(reachable)
                dfa_transitions[(current, symbol)] = {next_frozen}

                if next_frozen not in visited:
                    worklist.append(next_frozen)

        # Label DFA states with readable names
        state_label = self._label_dfa_states(dfa_states, start_set)

        # Build new transitions with string-named states
        new_transitions: dict[tuple, set] = {}
        for (fs, sym), next_set in dfa_transitions.items():
            next_fs = next(iter(next_set))  # single element
            new_transitions[(state_label[fs], sym)] = {state_label[next_fs]}

        new_states = set(state_label.values())
        new_start = state_label[start_set]
        new_finals = {
            state_label[fs] for fs in dfa_states
            if fs & self.final_states  # non-empty intersection
        }

        return FiniteAutomaton(new_states, self.alphabet - {"ε"},
                               new_transitions, new_start, new_finals)

    @staticmethod
    def _label_dfa_states(dfa_states: set, start_set: frozenset) -> dict:
        labels: dict[frozenset, str] = {}
        # Sort so output is deterministic
        sorted_states = sorted(dfa_states, key=lambda s: (len(s), sorted(s)))
        counter = 0
        for fs in sorted_states:
            if fs == start_set:
                labels[fs] = "d0"
            else:
                counter += 1
                labels[fs] = f"d{counter}"
        return labels

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        lines = [
            f"States       : {sorted(self.states)}",
            f"Alphabet     : {sorted(self.alphabet)}",
            f"Start        : {self.start}",
            f"Final states : {sorted(self.final_states)}",
            "Transitions  :",
        ]
        for (state, sym), nexts in sorted(self.transitions.items()):
            lines.append(f"  δ({state}, {sym}) = {sorted(nexts)}")
        return "\n".join(lines)