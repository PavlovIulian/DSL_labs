import random


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

    def generate_string(self, max_steps=50):
        """Generate a valid string from the grammar"""
        current = self.start

        for _ in range(max_steps):
            replaced = False

            # Find leftmost non-terminal
            for i, ch in enumerate(current):
                if ch in self.VN:
                    # Get productions for this non-terminal
                    if ch in self.P:
                        # Randomly choose a production
                        production = random.choice(self.P[ch])
                        # Replace non-terminal with production
                        current = current[:i] + production + current[i + 1:]
                        replaced = True
                        break

            # If no replacement was made, we're done
            if not replaced:
                break

        return current

    def to_finite_automaton(self):
        """Convert grammar to finite automaton"""
        # States: all non-terminals + final state
        states = set(self.VN)
        states.add('F')

        # Alphabet: all terminals
        alphabet = set(self.VT)

        # Build transitions from production rules
        transitions = {}

        for non_terminal, productions in self.P.items():
            for production in productions:
                if len(production) == 1 and production in self.VT:
                    # Production: X -> a (terminal only, goes to final state)
                    if non_terminal not in transitions:
                        transitions[non_terminal] = {}
                    transitions[non_terminal][production] = 'F'

                elif len(production) == 2:
                    # Production: X -> aY (terminal + non-terminal)
                    terminal = production[0]
                    next_state = production[1]

                    if non_terminal not in transitions:
                        transitions[non_terminal] = {}
                    transitions[non_terminal][terminal] = next_state

        # Initial state is the start symbol
        start_state = self.start

        # Final states
        final_states = {'F'}

        return FiniteAutomaton(states, alphabet, transitions, start_state, final_states)


class FiniteAutomaton:
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        self.Q = states  # Set of states
        self.Sigma = alphabet  # Input alphabet
        self.delta = transitions  # Transition function (dict of dicts)
        self.q0 = start_state  # Initial state
        self.F = final_states  # Set of final states

    def string_belong_to_language(self, input_string):
        """Check if input string is accepted by the automaton"""
        # Empty string check
        if not input_string:
            return self.q0 in self.F

        current_state = self.q0

        # Process each character
        for char in input_string:
            # Check if character is in alphabet
            if char not in self.Sigma:
                return False

            # Check if transition exists from current state
            if current_state not in self.delta:
                return False

            if char not in self.delta[current_state]:
                return False

            # Move to next state
            current_state = self.delta[current_state][char]

        # Check if we ended in a final state
        return current_state in self.F

    def display_automaton(self):
        """Display the automaton structure"""
        print("\n=== Finite Automaton ===")
        print(f"States (Q): {self.Q}")
        print(f"Alphabet (Σ): {self.Sigma}")
        print(f"Initial state (q0): {self.q0}")
        print(f"Final states (F): {self.F}")
        print("\nTransition function (δ):")
        for state, transitions in sorted(self.delta.items()):
            for symbol, next_state in sorted(transitions.items()):
                print(f"  δ({state}, {symbol}) = {next_state}")


def main():
    # Create grammar instance
    grammar = Grammar()

    print("=== Grammar Definition ===")
    print(f"Non-terminals (VN): {grammar.VN}")
    print(f"Terminals (VT): {grammar.VT}")
    print("\nProduction rules (P):")
    for nt, prods in grammar.P.items():
        for prod in prods:
            print(f"  {nt} -> {prod}")
    print(f"Start symbol: {grammar.start}")

    # Task 1: Generate 5 valid strings
    print("\n=== Generated Strings ===")
    generated_strings = []
    for i in range(5):
        string = grammar.generate_string()
        generated_strings.append(string)
        print(f"{i + 1}. {string}")

    # Task 2: Convert grammar to finite automaton
    print("\n=== Grammar to Finite Automaton Conversion ===")
    fa = grammar.to_finite_automaton()
    fa.display_automaton()

    # Task 3: Test the finite automaton
    print("\n=== Testing Finite Automaton ===")

    # Test with generated strings (should all be accepted)
    print("\nTesting generated strings:")
    for string in generated_strings:
        result = fa.string_belong_to_language(string)
        status = "✓ ACCEPTED" if result else "✗ REJECTED"
        print(f"  '{string}': {status}")

    # Test with additional strings
    print("\nTesting additional strings:")
    test_strings = [
        'ab',  # Should be accepted: S->aA, A->b (via C->b path)
        'aab',  # Should be accepted
        'aaab',  # Should be accepted
        'abab',  # Should be accepted
        'ba',  # Should be rejected (can't start with 'b')
        'aa',  # Should be rejected (can't end with 'a')
        'abb',  # Should be rejected
        '',  # Empty string - rejected
    ]

    for string in test_strings:
        result = fa.string_belong_to_language(string)
        status = "✓ ACCEPTED" if result else "✗ REJECTED"
        print(f"  '{string}': {status}")

    # Interactive testing
    print("\n=== Interactive Testing ===")
    while True:
        user_input = input("\nEnter a string to check (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break

        result = fa.string_belong_to_language(user_input)
        if result:
            print(f"✓ String '{user_input}' BELONGS to the language")
        else:
            print(f"✗ String '{user_input}' does NOT belong to the language")


if __name__ == "__main__":
    main()