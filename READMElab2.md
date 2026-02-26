# Lab 2 – Determinism in Finite Automata, NFA→DFA, Chomsky Hierarchy

**Course:** Formal Languages & Finite Automata  
**Variant:** 19  
**Author:** Cretu Dumitru

---

## Overview

This lab extends the work from Lab 1 by adding Chomsky hierarchy classification to the existing grammar, then working with a new finite automaton (Variant 19) to determine determinism, convert an NFA to a DFA, and derive a regular grammar from the automaton.

---

## Variant 19 – FA Definition

```
Q  = {q0, q1, q2}
Σ  = {a, b}
F  = {q2}

δ(q0, a) = q0
δ(q0, a) = q1     ← non-deterministic!
δ(q0, b) = q0
δ(q1, b) = q1
δ(q1, b) = q2     ← non-deterministic!
δ(q2, b) = q2
```

The language accepted is: all strings over `{a, b}` that contain at least one `a` followed by at least one `b` — i.e., strings containing the pattern `a…b`.

---

## Tasks

### 1. Chomsky Classification

The `classify_chomsky()` method inspects every production rule and checks conditions from Type 3 down to Type 0. The Lab-1 grammar:

```
S → aA | A → bS | aB | B → bC | C → aA | b
```

Every LHS is a single non-terminal, and every RHS is either a single terminal or a terminal followed by a non-terminal (right-linear). This makes it a **Type 3 – Regular Grammar**.

### 2. Determinism Check

`is_deterministic()` scans the transition table and checks whether any `(state, symbol)` pair maps to more than one state. For Variant 19:

- `δ(q0, a)` → `{q0, q1}` — two targets ✗
- `δ(q1, b)` → `{q1, q2}` — two targets ✗

**Result: NFA** (Non-Deterministic Finite Automaton).

### 3. NFA → DFA Conversion (Subset Construction)

`to_dfa()` applies the powerset algorithm, tracking sets of NFA states as single DFA states:

| DFA State    | On `a`       | On `b`         | Final? |
|--------------|--------------|----------------|--------|
| `{q0}`       | `{q0, q1}`   | `{q0}`         | No     |
| `{q0, q1}`   | `{q0, q1}`   | `{q0, q1, q2}` | No     |
| `{q0,q1,q2}` | `{q0, q1}`   | `{q0, q1, q2}` | **Yes** |

The resulting DFA has 3 states, the same as the original NFA, and is confirmed deterministic.

### 4. FA → Regular Grammar Conversion

`to_regular_grammar()` converts each FA transition into a right-linear production:

- `δ(q, a) = p` → `q → a p`
- If `p` is a final state → also add `q → a`

Derived grammar from the NFA:
```
q0 → a q0 | a q1 | b q0
q1 → b q1 | b
q2 → b
```

This grammar correctly classifies as **Type 3 – Regular**.

---

## Project Structure

```
lab2.py        - Main implementation
README.md      - This file
```

### Key Classes

- **`Grammar`** – Lab-1 grammar with added `classify_chomsky()` method
- **`Grammar_Generic`** – General grammar produced by FA→grammar conversion, also supports Chomsky classification
- **`FiniteAutomaton`** – Supports both NFA and DFA; transitions stored as sets internally. Key methods:
  - `is_deterministic()` – checks for multi-target transitions
  - `to_dfa()` – subset construction NFA→DFA
  - `to_regular_grammar()` – derives right-linear grammar from FA
  - `string_belong_to_language()` – BFS-based acceptance check (works for NFA and DFA)

---

## How to Run

```bash
python lab2.py
```

No external dependencies required — standard Python 3 only.

---

## Results Summary

| Task | Result |
|------|--------|
| Lab-1 grammar Chomsky class | Type 3 – Regular |
| Variant 19 FA type | NFA |
| DFA states after conversion | 3 (`{q0}`, `{q0,q1}`, `{q0,q1,q2}`) |
| Derived grammar Chomsky class | Type 3 – Regular |
| NFA/DFA agreement on test strings | 10/10 ✓ |
