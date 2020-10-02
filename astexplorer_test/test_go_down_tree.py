import unittest
from unittest import TestCase
from astexplorer.utils import *
from astexplorer.ast_parser import *
from pythonparser import parse
import json


class TestGoDownTree(TestCase):
    def test_go_down_tree01(self):
        fname = '../examples/ast_parser.py'
        #fname = 'sample01.txt'
        with open(fname, 'r') as myfile:
            data = myfile.read()

        ast = parse(data, fname, "exec")
        tree = go_down_tree(ast)
        #print(json.dumps(tree, default=serialize, sort_keys=False, indent=4))
        #self.assertEquals(2, len(tree))
        for fun in tree:
            fun.weight_tree()
            fun.calc_hashes()
            print(fun.stringify())
            print()

    def test_go_down_tree02(self):
        return
        fname = '../examples/sample02.txt'
        with open(fname, 'r') as myfile:
            data = myfile.read()

        ast = parse(data, fname, "exec")
        tree = go_down_tree(ast)
        print(tree[0].stringify())

    def test_rename_ptrs(self):
        return
        fname = '../examples/sample01.txt'
        with open(fname, 'r') as myfile:
            data = myfile.read()

        ast = parse(data, fname, "exec")
        tree = go_down_tree(ast)
        for fnode in tree:
            fnode.rename_ptrs()
        print(json.dumps(tree, default=serialize, sort_keys=False, indent=4))
        self.assertEqual(2, len(tree))

    def test_math(self):
        return
        fname = '../examples/sample_math01.txt'
        with open(fname, 'r') as myfile:
            data = myfile.read()

        ast = parse(data, fname, "exec")
        tree = go_down_tree(ast)
        print(tree[0].stringify())
        #print(json.dumps(tree[0], default=serialize, sort_keys=False, indent=4))

    def test_ifelse(self):
        return
        fname = '../examples/sample_ifelse_01.txt'
        with open(fname, 'r') as myfile:
            data = myfile.read()

        ast = parse(data, fname, "exec")
        tree = go_down_tree(ast)
        print(tree[0].stringify())
        #print(json.dumps(tree[0], default=serialize, sort_keys=False, indent=4))


if __name__ == '__main__':
    unittest.main()