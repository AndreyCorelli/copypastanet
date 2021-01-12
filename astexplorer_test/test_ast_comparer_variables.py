from unittest import TestCase
from astexplorer.ast_parser import *
from astexplorer.ast_comparer import *


def read_file_line_by_line(file_path):
    with open(file_path) as f:
        return f.readlines()


class TestAstComparerVariables(TestCase):
    def test_mutable_vars(self):
        functions = AstParser().parse_string('''
import math
def compute_none(p):    
    a = {1, 10, 100}
    print(a)
    print('10')
    x = 3.14
    y = math.pow(math.sin(x / 2), p)
    return p / 4''', 'file.py')
        self.assertEqual(1, len(functions))
        children = functions[0].children
        self.assertEqual({'a'}, children[0].mutating_variables)
        # 'a' is a function argument and probably the function modifies the variable
        self.assertEqual({'a'}, children[1].mutating_variables)
        # '10' is string, neither variable nor attribute
        self.assertEqual(0, len(children[2].mutating_variables))
        self.assertEqual(0, len(children[5].mutating_variables))

    def test_mutable_vars_if(self):
        functions = AstParser().parse_string('''
import math
def compute_none(p):    
    if p < 0:
        print('negative')
    print(p)

def compute_one(p):    
    print('?')
    print(p)    
    ''', 'file.py')
        self.assertEqual(2, len(functions))
        children = functions[0].children
        self.assertEqual(0, len(children[0].mutating_variables))
        self.assertEqual({'p'}, children[1].mutating_variables)

        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)

        a_vars = {}
        b_vars = {}
        all_vars = [a_vars, b_vars]
        for i in range(2):
            for c in functions[i].children:
                for v in c.variables.variables:
                    if v.name in all_vars[i]:
                        all_vars[i][v.name].add(v.usage_hash)
                    else:
                        all_vars[i][v.name] = {v.usage_hash}

        self.assertEqual(len(a_vars), len(b_vars))

    def test_local_position_hashes(self):
        fname = '../examples/renamed_local_var_functions.py'
        functions = AstParser().parse_module(fname)

        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)
        nodes = []
        hashes_a = []
        for node in functions[0].children:
            self.extract_hashes(node, hashes_a, VAR_NAMES_INDEX, nodes)
        hashes_b = []
        for node in functions[1].children:
            self.extract_hashes(node, hashes_b, VAR_NAMES_INDEX, [])

        self.assertEqual(len(hashes_b), len(hashes_a))
        for i in range(len(hashes_a)):
            self.assertEqual(hashes_b[i], hashes_a[i],
                             f'test_local_position_hashes: hashes differ at [{i}].\n'
                             f'Node: {nodes[i]}')

    def test_local_var_hashes(self):
        fname = '../examples/renamed_local_var_functions.py'
        functions = AstParser().parse_module(fname)

        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)
        hashes_a = {}
        for node in functions[0].children:
            hashes_a.update({nm.name: nm.usage_hash for nm in node.variables.variables})
        hashes_b = {}
        for node in functions[1].children:
            hashes_b.update({nm.name: nm.usage_hash for nm in node.variables.variables})

        self.assertEqual(len(hashes_b), len(hashes_a))
        self.assertEqual(hashes_b['z'], hashes_a['x'], 'x / y')
        self.assertEqual(hashes_b['d'], hashes_a['y'], 'x / y')

    def extract_hashes(self,
                       node: BriefNode,
                       hashes: List[str],
                       hash_key: str,
                       nodes: List[BriefNode]):
        hashes.append(node.hash_by_type[hash_key])
        nodes.append(node)
        for child in node.arguments:
            self.extract_hashes(child, hashes, hash_key, nodes)
        for lst_key in node.body:
            for child in node.body[lst_key]:
                self.extract_hashes(child, hashes, hash_key, nodes)