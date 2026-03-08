import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from Finite_automaton import FiniteAutomaton
from grammar import Grammar
from visualiser import render


SEPARATOR = "=" * 60


def section(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)



def build_variant19_fa() -> FiniteAutomaton:

    states = {"q0", "q1", "q2"}
    alphabet = {"a", "b"}
    transitions = {
        ("q0", "a"): {"q0", "q1"},   # δ(q0,a)=q1 AND δ(q0,a)=q0
        ("q0", "b"): {"q0"},
        ("q1", "b"): {"q1", "q2"},   # δ(q1,b)=q2 AND δ(q1,b)=q1
        ("q2", "b"): {"q2"},
    }
    start = "q0"
    final_states = {"q2"}
    return FiniteAutomaton(states, alphabet, transitions, start, final_states)

def task_show_fa(fa: FiniteAutomaton) -> None:
    section("Original FA (Variant 19)")
    print(fa)


def task_grammar_from_fa(fa: FiniteAutomaton) -> Grammar:
    section("Task 3a – FA → Regular Grammar")
    grammar = fa.to_regular_grammar()
    print(grammar)
    print(f"\nChomsky classification: {grammar.classify()}")
    return grammar


def task_determinism_check(fa: FiniteAutomaton) -> None:
    section("Task 3b – Determinism Check")
    det = fa.is_deterministic()
    verdict = "DETERMINISTIC (DFA)" if det else "NON-DETERMINISTIC (NDFA)"
    print(f"The FA is: {verdict}")
    if not det:
        print("\nReason – multiple target states for the same (state, symbol):")
        for (state, sym), nexts in sorted(fa.transitions.items()):
            if len(nexts) > 1:
                print(f"  δ({state}, {sym}) = {sorted(nexts)}")


def task_ndfa_to_dfa(fa: FiniteAutomaton) -> FiniteAutomaton:
    section("Task 3c – NDFA → DFA (Subset Construction)")
    dfa = fa.to_dfa()
    print("Resulting DFA:")
    print(dfa)
    print(f"\nDFA is deterministic: {dfa.is_deterministic()}")
    return dfa


def task_grammar_classify_demo() -> None:
    section("Task 2a – Chomsky Hierarchy Classification (examples)")

    examples = [
        # Type 3 – right-linear
        Grammar(
            non_terminals={"S", "A"},
            terminals={"a", "b"},
            productions={"S": ["aA", "a"], "A": ["bS", "b"]},
            start="S",
        ),
        # Type 2 – context-free (not regular)
        Grammar(
            non_terminals={"S"},
            terminals={"a", "b"},
            productions={"S": ["aSb", "ab"]},
            start="S",
        ),
        # Type 1 – context-sensitive
        Grammar(
            non_terminals={"S", "A", "B"},
            terminals={"a", "b", "c"},
            productions={
                "S":  ["abc", "aAbc"],
                "Ab": ["bA"],
                "Ac": ["Bbcc"],
                "bB": ["Bb"],
                "aB": ["aa"],
            },
            start="S",
        ),
        # Type 0 – unrestricted (LHS shrinks)
        Grammar(
            non_terminals={"S", "A"},
            terminals={"a"},
            productions={"SA": ["a"], "S": ["SA"]},
            start="S",
        ),
    ]

    for i, g in enumerate(examples):
        print(f"\n--- Example {i + 1} ---")
        print(g)
        print(f"→ Classification: {g.classify()}")


def task_visualise(fa: FiniteAutomaton, dfa: FiniteAutomaton) -> None:
    section("Task 3d (Bonus) – Graphical Representation")
    render(fa,  title="NDFA – Variant 19",   filename="ndfa_variant19")
    render(dfa, title="DFA  – Variant 19",   filename="dfa_variant19")

def main() -> None:
    print("\n" + SEPARATOR)
    print("  Lab 2 – NDFA/DFA – Formal Languages & Finite Automata")
    print(SEPARATOR)

    fa = build_variant19_fa()

    task_show_fa(fa)
    grammar = task_grammar_from_fa(fa)
    task_determinism_check(fa)
    dfa = task_ndfa_to_dfa(fa)
    task_grammar_classify_demo()
    task_visualise(fa, dfa)

    print(f"\n{SEPARATOR}")
    print("  All tasks completed.")
    print(SEPARATOR + "\n")


if __name__ == "__main__":
    main()