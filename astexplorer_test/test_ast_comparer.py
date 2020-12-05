import unittest
from unittest import TestCase
from astexplorer.ast_parser import *
from astexplorer.ast_comparer import *


def read_file_line_by_line(file_path):
    with open(file_path) as f:
        return f.readlines()


class TestAstComparer(TestCase):
    def test_immutable_variables_equal(self):
        # 'ct' is immutable in "if ct > 0:" line
        # so loop bodies should match
        functions = AstParser().parse_string('''
def fn1(iters):
    s = ''
    a = 1
    while iters > 0:
        s += f'{a*a}'
        a += 1 
    return s

def fn2(ct):
    s = ''
    a = 1
    if ct > 0:
        while ct > 0:
            s += f'{a*a}'
            a += 1
        return s            
            ''', 'file.py')
        cmp = AstComparer()
        cmp.compare_pre_process_functions(functions)
        cps = cmp.find_copypastes(functions)
        self.assertEqual(1, len(cps))

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
            print('-'*40)
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

    def test_while_loop(self):
        fname = '../examples/while_loop.py'
        cps, _ = self.find_copypastes_in_file(fname)
        # TODO: check inside loop expression
        self.assertEqual(1, len(cps))

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
