import unittest
from unittest import TestCase
from astexplorer.ast_parser import *
from astexplorer.ast_comparer import *
from pythonparser import parse

def read_file_line_by_line(file_path):
    with open(file_path) as f:
        return f.readlines()


class TestAstComparer(TestCase):

    def test_find_dups_in_parser(self):
        fname = '../astexplorer/ast_parser.py'
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

        for c in cps:
            print(c)
            print()


if __name__ == '__main__':
    unittest.main()