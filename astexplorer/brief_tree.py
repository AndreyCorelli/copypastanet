class BriefNode:
    def __init__(self):
        self.operands = []
        self.function = ''

    def __init__(self, function):
        self.function = function
        self.arguments = []
        self.body = {}
        self.id = None
        self.instance = None


class FuncTree:
    def __init__(self, name):
        self.children = []
        self.name = name
        self.args = {}

    def __str__(self):
        args = ''
        for p in self.args:
            args += p
            args += ';'
        return self.name + ' ' + args

    # make parameter names, e.g. (self, folder, mode) "minimized"
    # e.q. (self, #p1, #p2)
    def rename_ptrs(self):
        for child in self.children:
            self.rename_ptrs_for_node(child)

    def rename_ptrs_for_node(self, node):
        if node.function == 'Name':
            node.id = self.find_suitable_ptr(node.id)
        elif node.function == 'Call':
            if node.instance is not None:
                node.instance = self.find_suitable_ptr(node.instance)
        elif node.function == 'Attribute':
            node.instance = self.find_suitable_ptr(node.instance)

        for arg in node.arguments:
            self.rename_ptrs_for_node(arg)
        for child_list in node.body.values():
            for child in child_list:
                self.rename_ptrs_for_node(child)

    def find_suitable_ptr(self, name):
        if name not in self.args:
            return name
        if name == 'self':
            return name
        return '#p' + str(self.args[name])