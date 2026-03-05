# Lab 1 – Regular Grammars & Finite Automata

**Course:** Formal Languages & Finite Automata
**Author:** Cretu Dumitru

---

## Table of Contents

1. [Overview](#overview)
2. [The Grammar](#the-grammar)
3. [Grammar → Finite Automaton Conversion](#grammar--finite-automaton-conversion)
4. [Implementation](#implementation)
5. [Testing](#testing)
6. [Challenges Encountered](#challenges-encountered)
7. [Conclusions](#conclusions)

---

## Overview

This lab covers converting a regular grammar into a finite automaton and using it to validate strings. The grammar defines a formal language, and the FA acts as a recognizer — accepting strings that belong to the language and rejecting those that do not.

---

## The Grammar

```
VN = {S, A, B, C}       — non-terminals (states)
VT = {a, b}             — terminals (alphabet)
Start symbol: S

Production rules:
  S → aA
  A → bS | aB
  B → bC
  C → aA | b
```

### What does this language generate?

All strings produced by this grammar follow the pattern **`a(ba)*abb`**:

- Every string starts with `a`
- Every string ends with `bb`
- The middle section is zero or more repetitions of `ba`

| String     | Valid? | Reason                         |
|------------|--------|--------------------------------|
| `aabb`     | ✓      | Minimum valid string (0 loops) |
| `abaabb`   | ✓      | One `ba` loop                  |
| `ababaabb` | ✓      | Two `ba` loops                 |
| `ab`       | ✗      | Missing final `b`              |
| `aaab`     | ✗      | Ends with single `b`           |
| `ba`       | ✗      | Starts with `b`                |
| `abb`      | ✗      | Doesn't follow pattern         |

---

## Grammar → Finite Automaton Conversion

The conversion follows a straightforward rule set:

- Each non-terminal becomes a state
- One extra final state `F` is added
- For a rule `X → aY` → add transition `δ(X, a) = Y`
- For a rule `X → a` → add transition `δ(X, a) = F`

### Resulting FA

```
States:      {S, A, B, C, F}
Alphabet:    {a, b}
Start state: S
Final state: {F}

Transitions:
  δ(S, a) = A     (from S → aA)
  δ(A, b) = S     (from A → bS)
  δ(A, a) = B     (from A → aB)
  δ(B, b) = C     (from B → bC)
  δ(C, a) = A     (from C → aA)
  δ(C, b) = F     (from C → b)
```

### Example Trace — `abaabb`

```
Start: S
  Read 'a' → S → A
  Read 'b' → A → S   (loop back)
  Read 'a' → S → A
  Read 'a' → A → B
  Read 'b' → B → C
  Read 'b' → C → F
End at F → ACCEPT ✓
```

Grammar derivation for the same string:
```
S ⇒ aA ⇒ abS ⇒ abaA ⇒ abaaB ⇒ abaabC ⇒ abaabb
```

---

## Implementation

### Project Structure

```
grammar_corrected.py    — Main implementation
README.md               — This file
```

### Grammar Class

The `Grammar` class stores the production rules and provides two core methods.

**String Generation** — `generate_string()` starts from the start symbol and repeatedly replaces the leftmost non-terminal with a randomly chosen production until only terminals remain. A `max_steps` guard prevents infinite loops on recursive paths like `A → bS`.

```python
def generate_string(self, max_steps=50):
    current = self.start

    for _ in range(max_steps):
        replaced = False
        for i, ch in enumerate(current):
            if ch in self.VN:
                production = random.choice(self.P[ch])
                current = current[:i] + production + current[i + 1:]
                replaced = True
                break
        if not replaced:
            break

    return current
```

**Grammar to FA Conversion** — `to_finite_automaton()` iterates over every production rule and builds the transition dictionary. It handles two cases: rules of the form `X → aY` (transition to another non-terminal state) and rules of the form `X → a` (transition to the dedicated final state `F`).

```python
def to_finite_automaton(self):
    states = set(self.VN)
    states.add('F')
    transitions = {}

    for non_terminal, productions in self.P.items():
        for production in productions:
            if len(production) == 1 and production in self.VT:
                # X → a  →  go to final state
                transitions.setdefault(non_terminal, {})[production] = 'F'
            elif len(production) == 2:
                # X → aY  →  go to state Y
                terminal, next_state = production[0], production[1]
                transitions.setdefault(non_terminal, {})[terminal] = next_state

    return FiniteAutomaton(states, set(self.VT), transitions, self.start, {'F'})
```

### FiniteAutomaton Class

**String Acceptance** — `string_belong_to_language()` walks through each character of the input, follows transitions, and returns `True` only if the automaton ends in a final state.

```python
def string_belong_to_language(self, input_string):
    if not input_string:
        return self.q0 in self.F

    current_state = self.q0

    for char in input_string:
        if char not in self.Sigma:
            return False
        if current_state not in self.delta:
            return False
        if char not in self.delta[current_state]:
            return False
        current_state = self.delta[current_state][char]

    return current_state in self.F
```

**Step-by-step Trace** — `trace_string()` prints each transition as it happens, making it easy to follow exactly why a string is accepted or rejected.

```python
def trace_string(self, input_string):
    current_state = self.q0
    print(f"Start: {current_state}")

    for char in input_string:
        if current_state not in self.delta or char not in self.delta[current_state]:
            print(f"  No transition from {current_state} on '{char}' - REJECT")
            return
        next_state = self.delta[current_state][char]
        print(f"  Read '{char}': {current_state} → {next_state}")
        current_state = next_state

    if current_state in self.F:
        print(f"End state {current_state} is in F - ACCEPT")
    else:
        print(f"End state {current_state} is not in F - REJECT")
```


## Testing

### Quick Reference

**Should ACCEPT** (match pattern `a(ba)*abb`):
- `aabb` — minimum valid string
- `abaabb` — one loop
- `ababaabb` — two loops

**Should REJECT:**
- `ab` — too short, missing final `b`
- `aaab` — ends with single `b`
- `ba` — starts with `b`
- `abb` — doesn't follow the pattern
- empty string

### Sample Output

```
=== Generated Strings ===
1. aabb
2. abaabb
3. aabb
4. ababaabb
5. abaabb

Testing generated strings:
  'aabb':     ✓ ACCEPTED
  'abaabb':   ✓ ACCEPTED
  'aabb':     ✓ ACCEPTED
  'ababaabb': ✓ ACCEPTED
  'abaabb':   ✓ ACCEPTED

Testing additional strings:
  'aabb':     ✓ ACCEPTED  (expected: ACCEPT)  ✓
  'abaabb':   ✓ ACCEPTED  (expected: ACCEPT)  ✓
  'ab':       ✗ REJECTED  (expected: REJECT)  ✓
  'aaab':     ✗ REJECTED  (expected: REJECT)  ✓
  'ba':       ✗ REJECTED  (expected: REJECT)  ✓
  '':         ✗ REJECTED  (expected: REJECT)  ✓
```

---

## Challenges Encountered

### Challenge 1 — Handling terminal-only productions

Rules like `C → b` don't point to another non-terminal, so the standard `X → aY` conversion doesn't apply. Initially this rule was skipped, which meant strings ending correctly (reaching state `C` and reading `b`) were rejected because no transition to `F` existed.

The fix was a separate check: if a production has only a terminal with no following non-terminal, create a transition directly to the final state `F`.

```python
if len(production) == 1 and production in self.VT:
    transitions.setdefault(non_terminal, {})[production] = 'F'
```

### Challenge 2 — Infinite loops in string generation

Some productions loop back to earlier states (e.g. `A → bS`), so the generator could theoretically run forever on an unlucky sequence of random choices. The fix was a `max_steps=50` counter — if the limit is hit, the current string is discarded and the caller retries.

```python
def generate_string(self, max_steps=50):
    current = self.start
    for _ in range(max_steps):
        ...
    return current  # returned as-is if limit hit; caller checks for non-terminals
```

---

## Conclusions

This lab demonstrated the direct equivalence between regular grammars and finite automata. Every production rule maps cleanly to a state transition, and the resulting FA accepts exactly the strings the grammar generates. Implementing both the generator and the validator together made it easy to verify correctness — every string the grammar produced was accepted by the FA, and manually crafted invalid strings were correctly rejected.

---

## References

- Course materials: Formal Languages & Finite Automata
- Hopcroft, Motwani, Ullman — *Introduction to Automata Theory, Languages, and Computation*
