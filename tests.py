"""Unit tests for the CNF converter."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from grammar import Grammar


def variant19_grammar():
    VN = {'S', 'A', 'B', 'C', 'E'}
    VT = {'a', 'd'}
    P = {
        'S': ['dB', 'B'],
        'A': ['d', 'dS', 'aAdCB'],
        'B': ['aC', 'bA', 'AC'],
        'C': ['ε'],
        'E': ['AS'],
    }
    return Grammar(VN, VT, P, 'S')


class TestEliminateEpsilon(unittest.TestCase):
    def test_no_epsilon_in_non_start(self):
        g = variant19_grammar()
        g.eliminate_epsilon()
        for A, prods in g.P.items():
            if A != g.S:
                self.assertNotIn([], prods, f"ε found in {A}")

    def test_c_no_longer_has_epsilon(self):
        g = variant19_grammar()
        g.eliminate_epsilon()
        self.assertNotIn([], g.P.get('C', []))


class TestEliminateUnitProductions(unittest.TestCase):
    def test_no_single_nonterminal_rhs(self):
        g = variant19_grammar()
        g.eliminate_epsilon()
        g.eliminate_unit_productions()
        for A, prods in g.P.items():
            for prod in prods:
                if prod != []:
                    self.assertFalse(
                        len(prod) == 1 and prod[0] in g.VN,
                        f"Unit production {A} → {prod[0]} still present"
                    )


class TestEliminateInaccessible(unittest.TestCase):
    def test_e_removed(self):
        g = variant19_grammar()
        g.eliminate_epsilon()
        g.eliminate_unit_productions()
        g.eliminate_inaccessible()
        self.assertNotIn('E', g.VN)
        self.assertNotIn('E', g.P)


class TestCNF(unittest.TestCase):
    def _check_cnf(self, g):
        for A, prods in g.P.items():
            for prod in prods:
                if prod == []:
                    self.assertEqual(A, g.S, f"Only S can have ε, got {A}")
                    continue
                self.assertIn(len(prod), [1, 2], f"{A} → {prod} has bad length")
                if len(prod) == 1:
                    self.assertIn(prod[0], g.VT, f"{A} → {prod[0]}: must be terminal")
                else:
                    self.assertIn(prod[0], g.VN, f"{A} → {prod}: first must be NT")
                    self.assertIn(prod[1], g.VN, f"{A} → {prod}: second must be NT")

    def test_all_productions_cnf(self):
        g = variant19_grammar()
        g.normalize(verbose=False)
        self._check_cnf(g)

    def test_bonus_grammar(self):
        VN = {'S', 'A', 'B'}
        VT = {'a', 'b'}
        P = {'S': ['AB', 'ε'], 'A': ['aA', 'ε'], 'B': ['bB', 'b']}
        g = Grammar(VN, VT, P, 'S')
        g.normalize(verbose=False)
        self._check_cnf(g)


if __name__ == '__main__':
    unittest.main(verbosity=2)
