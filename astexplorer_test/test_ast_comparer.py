import unittest
from unittest import TestCase
from astexplorer.ast_parser import *
from astexplorer.ast_comparer import *


def read_file_line_by_line(file_path):
    with open(file_path) as f:
        return f.readlines()


class TestAstComparer(TestCase):
    def test_find_dups_in_parser(self):
        fname = '../examples/lazy_copypaste.py'
        with open(fname, 'r') as myfile:
            data = myfile.read()
        functions = AstParser().parse_module(fname)

        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)
        cps, cmp = self.find_copypastes_in_file(fname)
        cmp.read_src_lines(read_file_line_by_line)
        print(f'{len(cps)} copypastes found, max lines per one: {max([c.count for c in cps])}')

        for i in range(len(cps)):
            c = cps[i]
            print('-' * 80)
            print(f'[{i}] copypaste: {c}')
            print('-' * 80)
            text_a = data[c.start_index_a:c.end_index_a]
            text_b = data[c.node_b.line_start:c.node_b.line_end]
            print('-------------------------')
            print(text_a)
            print('\n' + '-' * 80)
            print(text_b)

    def test_identical(self):
        fname = '../examples/identical_functions.py'
        cps, _ = self.find_copypastes_in_file(fname)
        self.assertEqual(1, len(cps))
        # all the 3 lines are identical despite of extra spaces and
        # different argument naming (x and z)
        self.assertEqual(3, cps[0].count)

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

    def test_different_local_vars(self):
        fname = '../examples/renamed_local_var_functions.py'
        cps, _ = self.find_copypastes_in_file(fname)
        # so far the test fails
        self.assertEqual(1, len(cps))
        self.assertEqual(3, cps[0].count, 'Should include all the 3 lexems')

    def test_diff_arg_count(self):
        fname = '../examples/diff_arg_count.py'
        cps, _ = self.find_copypastes_in_file(fname)
        # so far the test fails
        self.assertEqual(1, len(cps))
        self.assertEqual(3, cps[0].count, 'Should include all the 3 lexems')

    def find_copypastes_in_file(self, fname: str) -> Tuple[List[Copypaste], AstComparer]:
        functions = AstParser().parse_module(fname)
        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)
        cps = cmp.find_copypastes(functions)
        return cps, cmp


if __name__ == '__main__':
    unittest.main()
