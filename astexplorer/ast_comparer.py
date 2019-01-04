from astexplorer.copypaste import *

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
        return self.copypastes

    def find_func_copypastes(self, fa, fb):
        self.find_node_copypastes(fa, fb, fa.children, fb.children)

    def find_node_copypastes(self, fa, fb, a_list, b_list):
        cp_list = []
        cp = None
        for a in a_list:
            for b in b_list:
                if a.hash == b.hash:
                    if cp is None:
                        cp = Copypaste(fa, fb, a, b)
                        cp_list.append(cp)
                    else: # cp is not None
                        cp.update(a)
                else: # if a.hash != b.hash:
                    cp = None
                # delve into B children
                for bkey in b.body:
                    if len(b.body[bkey]) == 0:
                        continue
                    self.find_node_copypastes(fa, fb, a_list, b.body[bkey])
            # delve into A children
            for akey in a.body:
                if len(a.body[akey]) == 0:
                    continue
                self.find_node_copypastes(fa, fb, a.body[akey], b_list)

        # leave copypastes of 2+ items with min_cp_weight
        for cp in cp_list:
            if cp.count < 2 or cp.weight < self.min_cp_weight:
                continue
            self.copypastes.append(cp)

        return
