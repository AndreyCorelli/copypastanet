class Copypaste:
    def __init__(self, func_a, func_b, node_a, node_b):
        self.func_a = func_a
        self.func_b = func_b
        self.node_a = node_a
        self.node_b = node_b
        self.count = 1
        self.weight = node_a.weight

    def update(self, node_a):
        self.count += 1
        self.weight += node_a.weight

    def __str__(self):
        s = str(self.count) + ' lexems, ' + str(self.weight) + ' weight.\n'
        s += 'Files: [' + self.func_a.file + ', ' + self.func_b.file + ']\n'
        s += 'Functions: [' + str(self.func_a) + ', ' + str(self.func_b) + ']\n'
        s += str(self.node_a) + ' ...'
        return s

