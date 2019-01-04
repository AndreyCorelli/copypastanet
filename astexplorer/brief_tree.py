import hashlib

class BriefNode:
    compare_op_symbols = {'Lt': '<', 'Gt': '>', 'Eq': '==', 'NotEq': '!==',
                          'In': 'in', 'NotIn': 'not in', 'Is': 'is', 'IsNot': 'is not'}

    math_bin_op_symbols = {'Add': '+', 'Div': '/', 'Mult': '*', 'Sub': '-', 'Pow': '^', 'Mod': '%'}

    math_unr_op_symbols = {'USub': '-', 'Not': 'not '}

    def __init__(self):
        self.operands = []
        self.function = ''
        self.weight = 0
        self.depth = 0
        self.line_start = 0
        self.line_end = 0
        self.hash = ''

    def __init__(self, function, loc=None):
        self.function = function
        self.arguments = []
        self.body = {}
        self.id = function
        self.instance = None
        self.weight = 0
        self.depth = 0
        self.hash = ''
        if loc is not None:
            self.line_start = loc.begin
            self.line_end = loc.end
        else:
            self.line_start = 0
            self.line_end = 0

    def __str__(self):
        return self.stringify(self)

    def stringify(self, node):
        s = self.stringify_expression(node)
        if node.depth > 0:
            s += (' [' + str(node.depth) + ']')
        return s

    def stringify_expression(self, node):
        if node.function == 'Name':
            if node.instance is not None:
                return node.instance + '.' + node.id
            return node.id

        if node.function == 'NameConstant':
            return node.id

        if node.function == 'Str':
            return "#str'" + node.id + "'"

        if node.function == 'Attribute':
            return node.instance + '.' + node.id

        if node.function == 'Assign':
            return self.stringify(node.arguments[0]) + '=' + self.stringify(node.body['_'][0])

        # + - * / Pow
        if node.function in BriefNode.math_bin_op_symbols:
            smb = BriefNode.math_bin_op_symbols[node.function]
            return self.stringify(node.body['left'][0]) + smb + self.stringify(node.body['right'][0])

        if node.function == 'AugAssign':
            smb = BriefNode.math_bin_op_symbols[node.id]
            return self.stringify(node.arguments[0]) + smb + '=' + self.stringify(node.body['_'][0])

        # unary op
        if node.function == 'UnaryOp':
            smb = BriefNode.math_unr_op_symbols[node.id]
            return smb + self.stringify(node.body['_'][0])

        # comparison
        if node.function == 'Compare':
            smb = BriefNode.compare_op_symbols[node.id]
            cmp_str = ', '.join([self.stringify(c) for c in node.body['comparators']])
            return self.stringify(node.body['left'][0]) + ' ' + smb + ' ' + cmp_str

        if node.function == 'If' or node.function == 'Elif':
            if_case = self.stringify(node.arguments[0])
            return node.function + ' ' + if_case + ':'

        if node.function == 'For':
            iter_tg = self.stringify(node.arguments[0])
            iter_vl = self.stringify(node.arguments[1])
            return node.function + ' ' + iter_tg + ' in ' + iter_vl + ':'

        if node.function == 'While':
            test_node = self.stringify(node.body["_"][0])
            return node.function + ' ' + test_node + ':'

        if node.function == 'With':
            expr = self.stringify(node.body["opt_expr"][0])
            opt_vars = ', '.join([self.stringify(c) for c in node.body['opt_vars']])
            if len(opt_vars) > 0:
                opt_vars = " as " + opt_vars
            return node.function + ' ' + expr + opt_vars + ':'

        if node.function == 'Num':
            return node.id

        if node.function == 'Tuple':
            arg_list = ', '.join([self.stringify(a) for a in node.arguments])
            return 'Tuple{' + arg_list + '}'

        if node.function == 'List':
            arg_list = ', '.join([self.stringify(a) for a in node.body["items"]])
            return '#List[' + arg_list + ']'

        if node.function == 'Return':
            return 'return ' + self.stringify(node.body['_'][0])

        if node.function == 'Lambda':
            arg_list = ', '.join([self.stringify(a) for a in node.arguments])
            return arg_list + ' => {}'

        if node.function == 'Call':
            inst_preffix = node.instance + '.' if node.instance is not None else ''
            args_lst = []
            for arg in node.arguments:
                args_lst.append(self.stringify(arg))
            return inst_preffix + node.id + '(' + ",".join(args_lst) + ')'

        if node.function == 'Raise':
            s_body = self.stringify(node.body['_'][0]) if '_' in node.body else ''
            return 'raise ' + s_body

        if node.id == node.function:
            return node.id
        inst_preffix = node.instance + '.' if node.instance is not None else ''
        return node.function + ' ' + inst_preffix + node.id


class FuncTree:
    default_node_weight = 10

    weight_by_function = {'Attribute': 1, 'Name': 1, 'Num': 1, 'NameConstant': 1, 'Str': 1, 'Tuple': 5}

    def __init__(self, name):
        self.file = ''
        self.children = []
        self.name = name
        self.args = {}

    def __str__(self):
        args = ', '.join(self.args)
        return 'def ' + self.name + '(' + args + '):'

    def stringify(self):
        title = str(self) + '\n'
        for child in self.children:
            title = self.stringify_node(child, title, 0)
        return title

    def stringify_node(self, node, str, indent):
        pads = ' ' * (indent * 4)
        str += pads
        str += node.__str__()
        str += '\n'
        for arg in node.arguments:
            str = self.stringify_node(arg, str, indent + 1)
        for b_list in node.body.values():
            for b_child in b_list:
                str = self.stringify_node(b_child, str, indent + 1)
        return str

    def calc_hashes(self):
        hash_calc = hashlib.md5()
        for child in self.children:
            self.calc_hash(child, hash_calc)

    def calc_hash(self, child, hash_calc):
        hash_src = str(child)
        # plus body items
        for key in child.body:
            for sub in child.body[key]:
                hash_src += self.calc_hash(sub, hash_calc)
        # plus arguments
        for arg in child.arguments:
            hash_src += self.calc_hash(arg, hash_calc)

        child.hash = hashlib.md5(hash_src.encode('utf-8')).hexdigest()
        return child.hash

    # give weight to each node, recursively
    def weight_tree(self):
        for child in self.children:
            self.weight_sub_tree(child, 1)

    def weight_sub_tree(self, child, depth):
        max_depth = depth
        child.weight = FuncTree.default_node_weight
        if child.function in FuncTree.weight_by_function:
            child.weight = FuncTree.weight_by_function[child.function]

        # sum body weights
        for key in child.body:
            for sub in child.body[key]:
                wd = self.weight_sub_tree(sub, 0)
                max_depth = max(max_depth, wd[1])
                child.weight += wd[0]
        # sum arguments
        for arg in child.arguments:
            arg_weight = self.weight_sub_tree(arg, 0)
            max_depth = max(max_depth, arg_weight[1])
            if arg_weight[0] > FuncTree.default_node_weight:
                arg_weight[0] -= FuncTree.default_node_weight
            child.weight += arg_weight[0]

        child.depth = max_depth
        return [child.weight, max_depth + 1]

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