import unittest
import names
import codecs
from unittest import TestCase
from astexplorer.ast_parser import *
from astexplorer.ast_comparer import *
from pythonparser import parse


def read_file_line_by_line(file_path):
    with open(file_path) as f:
        return f.readlines()


class TestAstComparer(TestCase):
    def test_names(self):
        f_names = set()
        l_names = set()
        for i in range(3000):
            name = names.get_first_name()
            f_names.add(name)
        for i in range(3000):
            name = names.get_last_name()
            l_names.add(name)
        f_names = list(f_names)
        l_names = list(l_names)
        ln = min(len(f_names), len(l_names))
        with codecs.open('/home/andrey/Downloads/names.txt', 'w', encoding='utf-8') as fw:
            for i in range(ln):
                fw.write(f'{f_names[i]};{l_names[i]}')

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