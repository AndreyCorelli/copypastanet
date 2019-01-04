from astexplorer.copypaste import *
from astexplorer.utils import *

class AstComparer:

    def __init__(self):
        self.copypastes = []
        self.min_cp_weight = 20

    def compare_pre_process_functions(self, functions):
        for fun in functions:
            fun.rename_ptrs()
            fun.weight_tree()
            fun.calc_hashes()

    def find_copypastes(self, functions):
        for i, fa in enumerate(functions):
            j = i + 1
            while j < len(functions):
                fb = functions[j]
                self.find_func_copypastes(fa, fb)
                j = j + 1
        self.sort_copypastes()
        return self.copypastes

    def find_func_copypastes(self, fa, fb):
        self.find_node_copypastes(fa, fb, fa.children, fb.children)

    def find_node_copypastes(self, fa, fb, a_list, b_list):

        # find copypastes on the current level
        cp_list = find_sub_sequences(a_list, b_list, lambda x, y: x.hash == y.hash)
        for cp in cp_list:
            if cp.count < 2:
                continue
            cpy = Copypaste(fa, fb, a_list[cp.start_a], b_list[cp.start_b])
            cpy.count = cp.count
            self.copypastes.append(cpy)

        # go down
        for a in a_list:
            for b in b_list:
                # delve into B children
                if b.depth >= a.depth:
                    if "" in b.body:
                        if len(b.body[""]) == 0:
                            continue
                        self.find_node_copypastes(fa, fb, a_list, b.body[""])
            # delve into A children
            if "" in a.body:
                if len(a.body[""]) == 0:
                    continue
                self.find_node_copypastes(fa, fb, a.body[""], b_list)
        return

    def sort_copypastes(self):
        self.copypastes.sort(key=lambda x: x.count, reverse=True)
