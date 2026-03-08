class Grammar:

    def __init__(self, non_terminals: set, terminals: set, productions: dict, start: str):
        self.non_terminals = set(non_terminals)
        self.terminals = set(terminals)
        self.productions = productions  # {lhs_str: [rhs_str, ...]}
        self.start = start

    def classify(self) -> str:

        if self._is_type3():
            return "Type 3 (Regular)"
        if self._is_type2():
            return "Type 2 (Context-Free)"
        if self._is_type1():
            return "Type 1 (Context-Sensitive)"
        return "Type 0 (Unrestricted)"

    def _is_type3(self) -> bool:

        right_ok = True
        left_ok = True

        for lhs, rhs_list in self.productions.items():
            # LHS must be a single non-terminal (name may be multi-char, e.g. "Q0")
            if lhs not in self.non_terminals:
                return False
            for rhs in rhs_list:
                if not self._is_right_linear(rhs):
                    right_ok = False
                if not self._is_left_linear(rhs):
                    left_ok = False

        return right_ok or left_ok

    def _is_right_linear(self, rhs: str) -> bool:

        if rhs == "ε":
            return True
        # Try to split as single terminal + optional non-terminal suffix
        for t in self.terminals:
            if rhs == t:
                return True
            if rhs.startswith(t):
                suffix = rhs[len(t):]
                if suffix in self.non_terminals:
                    return True
        return False

    def _is_left_linear(self, rhs: str) -> bool:

        if rhs == "ε":
            return True
        for t in self.terminals:
            if rhs == t:
                return True
            if rhs.endswith(t):
                prefix = rhs[: len(rhs) - len(t)]
                if prefix in self.non_terminals:
                    return True
        return False

    def _is_type2(self) -> bool:

        for lhs in self.productions:
            if len(lhs) != 1 or lhs not in self.non_terminals:
                return False
        return True

    def _is_type1(self) -> bool:

        for lhs, rhs_list in self.productions.items():
            for rhs in rhs_list:
                if rhs == "ε":
                    # Allowed only if start symbol never appears on RHS
                    if lhs != self.start:
                        return False
                    for other_lhs, other_rhs_list in self.productions.items():
                        for other_rhs in other_rhs_list:
                            if self.start in other_rhs:
                                return False
                else:
                    if len(lhs) > len(rhs):
                        return False
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        lines = [
            f"Non-terminals : {sorted(self.non_terminals)}",
            f"Terminals     : {sorted(self.terminals)}",
            f"Start symbol  : {self.start}",
            "Productions   :",
        ]
        for lhs, rhs_list in self.productions.items():
            for rhs in rhs_list:
                lines.append(f"  {lhs} -> {rhs}")
        return "\n".join(lines)