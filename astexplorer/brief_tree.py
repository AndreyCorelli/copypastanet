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

