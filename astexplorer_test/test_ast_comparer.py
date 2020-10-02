import unittest
from unittest import TestCase
from astexplorer.ast_parser import *
from astexplorer.ast_comparer import *
from pythonparser import parse


def read_file_line_by_line(file_path):
    with open(file_path) as f:
        return f.readlines()


class TestAstComparer(TestCase):
    def test_identical(self):
        fname = '../examples/identical_functions.py'
        with open(fname, 'r') as myfile:
            data = myfile.read()
        ast = parse(data, fname, "exec")
        functions = go_down_tree(ast)
        for f in functions:
            f.file = fname

        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)
        cps = cmp.find_copypastes(functions)
        self.assertEqual(1, len(cps))
        # all the 3 lines are identical despite of extra spaces and
        # different argument naming (x and z)
        self.assertEqual(3, cps[0].count)

    def test_different_local_vars(self):
        fname = '../examples/renamed_local_var_functions.py'
        with open(fname, 'r') as myfile:
            data = myfile.read()
        ast = parse(data, fname, "exec")
        functions = go_down_tree(ast)
        for f in functions:
            f.file = fname

        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)
        cps = cmp.find_copypastes(functions)
        # so far the test fails
        self.assertEqual(0, len(cps))

    def test_find_dups_in_parser(self):
        fname = '../examples/lazy_copypaste.py'
        with open(fname, 'r') as myfile:
            data = myfile.read()
        ast = parse(data, fname, "exec")
        functions = go_down_tree(ast)
        for f in functions:
            f.file = fname

        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)
        cps = cmp.find_copypastes(functions)
        cmp.read_src_lines(read_file_line_by_line)
        print(f'{len(cps)} copypastes found, max lines per one: {max([c.count for c in cps])}')

        for i in range(len(cps)):
            c = cps[i]
            print('-' * 80)
            print(f'[{i}] copypaste: {c}')
            print('-' * 80)
            text_a = data[c.node_a.line_start:c.node_a.line_end]
            text_b = data[c.node_b.line_start:c.node_b.line_end]
            print('-------------------------')
            print(text_a)
            print('\n' + '-' * 80)
            print(text_b)


if __name__ == '__main__':
    unittest.main()