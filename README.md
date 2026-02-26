Converting a regular grammar to a finite automaton and testing string recognition.

The Grammar

VN = {S, A, B, C}

VT = {a, b}

Start: S

Production Rules:

S → aA

A → bS | aB

B → bC

C → aA | b

What does this language generate?

Strings that start with a
Strings that end with bb
Pattern: a(ba)*abb

Valid examples: aabb, abaabb, ababaabb
Invalid examples: ab, ba, aaab, abb

How the Conversion Works
Rule: Grammar → Finite Automaton

Each non-terminal = a state
Add one final state F
For rule X → aY: add transition δ(X, a) = Y
For rule X → a: add transition δ(X, a) = F

Result
States: {S, A, B, C, F}
Start state: S
Final state: {F}
Transitions:

δ(S, a) = A    (from S → aA)

δ(A, b) = S    (from A → bS)

δ(A, a) = B    (from A → aB)

δ(B, b) = C    (from B → bC)

δ(C, a) = A    (from C → aA)

δ(C, b) = F    (from C → b)

<img width="692" height="206" alt="image" src="https://github.com/user-attachments/assets/13ea8fb2-e76b-4ba9-82bd-97b08e4f1786" />

Code Structure
Grammar Class

generate_string() - generates random valid strings
to_finite_automaton() - converts grammar to FA

FiniteAutomaton Class

string_belong_to_language(input) - checks if string is valid
trace_string(input) - shows step-by-step processing
display_automaton() - prints FA structure


Running the Code
bashpython grammar_corrected.py
What it does:


Shows the grammar definition

Generates 5 valid strings

Converts grammar to FA

Tests the generated strings (all pass ✓)

Tests predefined cases

Shows detailed traces

Interactive mode - test your own strings



Testing Quick Reference
Should ACCEPT:


aabb - minimum valid string

abaabb - one loop

ababaabb - two loops

Any string matching a(ba)*abb


Should REJECT:

ab - too short, missing final 'b'
aaab - ends with single 'b'
ba - starts with 'b'
abb - doesn't follow pattern
Empty string


Example Trace

Input: abaabb

Start: S

Read 'a': S → A

Read 'b': A → S  (loop back)

Read 'a': S → A

Read 'a': A → B

Read 'b': B → C

Read 'b': C → F

End at F → ACCEPT ✓

Grammar derivation:

S ⇒ aA ⇒ abS ⇒ abaA ⇒ abaaB ⇒ abaabC ⇒ abaabb
