from astexplorer.brief_node import BriefNode
from astexplorer.func_tree import FuncTree


class Copypaste:
    def __init__(self, func_a: FuncTree, func_b: FuncTree,
                 node_a: BriefNode, node_b: BriefNode):
        self.func_a = func_a
        self.func_b = func_b
        self.node_a = node_a
        self.node_b = node_b
        self.count = 1  # type: int
        self.weight = node_a.weight   # type: int
        self.src_line = ''
        self.start_index_a = node_a.line_start
        self.end_index_a = node_a.line_end

    def update(self, node_a: BriefNode):
        # self.count += 1
        self.weight += node_a.weight
        self.start_index_a = min(self.start_index_a, node_a.line_start)
        self.end_index_a = max(self.end_index_a, node_a.line_end)

    def __str__(self):
        s = str(self.count) + ' lexems, ' + str(self.weight) + ' weight.\n'
        s += 'Files: [' + self.func_a.file + ', ' + self.func_b.file + ']\n'
        s += 'Functions: [' + str(self.func_a) + ', ' + str(self.func_b) + ']\n'
        s += str(self.node_a) + ' ...'
        return s

    def __repr__(self):
        return self.__str__()
