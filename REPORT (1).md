# Lab 5: Chomsky Normal Form

**Course:** Formal Languages & Finite Automata  
**Variant:** 19  
**Author:** *Iulian Pavlov*  
**Date:** March 29, 2026

---

## Overview

CNF (Chomsky Normal Form) is a standardized way of writing context-free grammars where every rule is either `A → BC` or `A → a`. This matters practically because algorithms like CYK rely on it, and it makes it much easier to reason about what a grammar can and can't generate.

A CFG is defined as G = (V_N, V_T, P, S) — non-terminals, terminals, production rules, and a start symbol. Getting to CNF requires cleaning up the grammar first: removing empty productions, collapsing shortcut rules, cutting dead-end and unreachable symbols, then finally reshaping whatever's left into the two allowed forms.

---

## Objectives

1. Understand what CNF is and why it's useful.
2. Work through the normalisation steps manually (and in code).
3. Build a `Grammar` class in Python that can convert any CFG — not just Variant 19.

---

## Implementation

The core class is `Grammar` in `grammar.py`. It takes V_N, V_T, P, and S as arguments and stores productions internally as `list[list[str]]` — each production is a list of symbol strings rather than a single concatenated string. That detail matters: once you start introducing non-terminals with names like `TA` or `X1`, treating productions as plain strings breaks everything.

The `normalize()` method runs all five steps in order and optionally prints the grammar after each one.

### Step 1 — Eliminate ε-productions

First, find every nullable non-terminal — anything that can eventually derive the empty string. Then for each production, generate all possible variants where some or all nullable symbols are dropped. The original ε rules are removed. If the start symbol was nullable, `S → ε` is kept.

In this variant, `C → ε` makes `C` nullable, which cascades into `B` and then `S` getting new rules.

### Step 2 — Eliminate unit productions

A unit production is something like `A → B` where B is a single non-terminal. These are replaced by directly inlining B's own productions into A. This repeats until none are left.

After step 1, `B → A` and `S → B` appear. Both get inlined.

### Step 3 — Eliminate inaccessible symbols

Starting from S, mark every non-terminal that can actually be reached. Anything not reachable gets removed along with all its rules.

`E → AS` exists in the grammar, but nothing ever produces `E` — it's defined but never used. It gets dropped here.

### Step 4 — Eliminate non-productive symbols

A non-terminal is productive if it can eventually derive a string of terminals. This is computed iteratively. Symbols that can never terminate get removed, along with any rules that reference them.

After step 3, `C` has no productions left (they were all removed in step 1). It's non-productive and gets cut, along with rules like `A → aAdCB` that referenced it.

### Step 5 — Convert to CNF

Two things happen here:

**Terminal lifting:** Any terminal appearing inside a longer rule (e.g., `a` in `a A d B`) gets replaced by a proxy non-terminal. So `a` becomes `TA` where `TA → a`, and `d` becomes `TD` where `TD → d`.

**Binarisation:** Rules with more than two symbols get split right-recursively. `A → TA A TD B` becomes `A → TA X1`, `X1 → A X2`, `X2 → TD B`.

---

## Variant 19 — Step by Step

**Original grammar:**

```
G = ({S, A, B, C, E}, {a, d}, P, S)

S → dB | B
A → d | dS | aAdCB
B → aC | bA | AC
C → ε
E → AS
```

**After step 1** — C is nullable, so variants without C are added everywhere it appears:

```
A → aAdB | aAdCB | d | dS
B → A | AC | a | aC | bA
S → B | dB
E → AS
```

**After step 2** — B → A and S → B are unit productions, both get inlined:

```
A → aAdB | aAdCB | d | dS
B → AC | a | aAdB | aAdCB | aC | bA | d | dS
S → AC | a | aAdB | aAdCB | aC | bA | d | dB | dS
E → AS
```

**After step 3** — E is unreachable, removed. C is still referenced in some rules.

**After step 4** — C has no productions, so it's non-productive. Everything containing C gets pruned:

```
A → aAdB | d | dS
B → a | aAdB | d | dS
S → a | aAdB | d | dB | dS
```

**After step 5** — terminals lifted, productions binarised:

```
A  → TA X1 | TD S | d
B  → TA X3 | TD S | a | d
S  → TA X5 | TD B | TD S | a | d
TA → a
TD → d
X1 → A X2
X2 → TD B
X3 → A X4
X4 → TD B
X5 → A X6
X6 → TD B
```

---

## Challenges

**Representation choice.** Initially productions were stored as plain strings, which worked fine for single-character symbols but immediately broke during CNF conversion when helper non-terminals like `TA` or `X1` got introduced. Iterating over a string character by character treats `TA` as `T` and `A`. Switching to `list[list[str]]` fixed this but required rewriting most of the step logic.

**Binarisation ordering.** The first binarisation attempt mutated `self.P` during iteration, causing a `RuntimeError: dictionary changed size during iteration`. The fix was to collect all new rules in a separate `extra_rules` dict and merge it in at the end.

**C and the non-productive cascade.** C becomes non-productive not because it's inherently useless but because step 1 strips its only rule. The tricky part was making sure rules containing C (like `aAdCB`) were properly removed in step 4 rather than silently kept with a dangling symbol.

**Epsilon subset enumeration.** Generating all combinations of a production with nullable symbols removed requires iterating over all 2^k subsets of nullable positions. The implementation uses a bitmask for this, which works cleanly but took some care to get right — particularly making sure the empty result (all symbols removed) is excluded unless it's the start symbol.

---

## Tests

```
test_all_productions_cnf        ... ok
test_bonus_grammar              ... ok
test_c_no_longer_has_epsilon    ... ok
test_no_epsilon_in_non_start    ... ok
test_e_removed                  ... ok
test_no_single_nonterminal_rhs  ... ok

Ran 6 tests in 0.001s  —  OK
```

Tests cover each step individually (epsilon removal, unit removal, inaccessible removal) and the full CNF output for both the Variant 19 grammar and a second grammar to confirm generality.

---

## Conclusions

The `Grammar` class works correctly on Variant 19 and on arbitrary input grammars. The main lesson from implementing this was that the order of steps matters — removing ε-productions before unit productions avoids creating new unit productions from nullable collapsing, and removing inaccessible symbols before non-productive ones avoids redundant work.

The representation issue (strings vs lists) was also a good reminder that the data model needs to match the actual complexity of what you're representing. Single-character symbols feel natural but don't stay that way once CNF introduces helper non-terminals.

---

## References

1. Hopcroft, J. E., Motwani, R., Ullman, J. D. *Introduction to Automata Theory, Languages, and Computation*, 3rd ed.
2. Sipser, M. *Introduction to the Theory of Computation*, 3rd ed.
