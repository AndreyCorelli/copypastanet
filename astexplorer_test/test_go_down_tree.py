import unittest
from unittest import TestCase
from astexplorer.utils import *
from astexplorer.ast_parser import *
from pythonparser import parse
import json


class TestGoDownTree(TestCase):

    def test_go_down_tree(self):
        fname = 'sample01.txt'
        with open(fname, 'r') as myfile:
            data = myfile.read()

        ast = parse(data, fname, "exec")
        tree = go_down_tree(ast)
        print(json.dumps(tree, default=serialize, sort_keys=False, indent=4))


if __name__ == '__main__':
    unittest.main()