import hashlib
from typing import List, Dict, Set, Optional

# use original variable names like get_cartesian(bearing, distance)
VAR_NAMES_ORIGINAL = 'orig'
# user variables' indices inside the block like
# get_cartesian(bearing, distance) -> get_cartesian(v1, v2)
VAR_NAMES_INDEX = 'index'
# use hash for each variable built up on all variable's usages
VAR_NAMES_HASH = 'hash'


def get_hash(s: str) -> str:
    return hashlib.md5(s.encode('utf-8')).hexdigest()


class BriefVariable:
    def __init__(self, name: str):
        self.name = name
        self.block_index = ''
        self.usage_hash = ''

    def copy(self) -> 'BriefVariable':
        cpy = BriefVariable(self.name)
        cpy.block_index = self.block_index
        cpy.usage_hash = self.usage_hash
        return cpy

    def __str__(self):
        return f'{self.name} [{self.block_index}], #{self.usage_hash}'


class BriefVariableSet:
    def __init__(self):
        self.variables = []  # type: List[BriefVariable]
        # { name: index in self.variables }
        self.index_by_name = {}  # type: Dict[str, int]

    def find_var(self, var_name: str) -> Optional[BriefVariable]:
        return self.variables[self.index_by_name[var_name]] if var_name in self.index_by_name else None

    def add_variable(self, name: str) -> None:
        self.variables.append(BriefVariable(name))
        self.index_by_name[name] = len(self.variables) - 1

    def update(self, subset: 'BriefVariableSet') -> None:
        for var in subset.variables:
            if var.name in self.index_by_name:
                continue
            self.variables.append(var.copy())
            self.index_by_name[var.name] = len(self.variables) - 1


class BriefNode:
    compare_op_symbols = {'Lt': '<', 'Gt': '>', 'Eq': '==', 'NotEq': '!==',
                          'In': 'in', 'NotIn': 'not in', 'Is': 'is', 'IsNot': 'is not'}

    math_bin_op_symbols = {'Add': '+', 'Div': '/', 'Mult': '*', 'Sub': '-', 'Pow': '^', 'Mod': '%'}

    math_unr_op_symbols = {'USub': '-', 'Not': 'not '}

    def __init__(self, function='', loc=None):
        self.operands = []
        self.function = function  # type: str
        self.arguments = []  # type: List[BriefNode]
        self.body = {}  # type: Dict[str, List[BriefNode]]
        self.id = function
        self.instance = None
        self.weight = 0
        self.depth = 0
        # FuncTree recursively calculates hash for each node
        self.hash_by_type = {VAR_NAMES_ORIGINAL: '',
                             VAR_NAMES_INDEX: '',
                             VAR_NAMES_HASH: '' }
        if loc is not None:
            self.line_start = loc.begin_pos
            self.line_end = loc.end_pos
        else:
            self.line_start = 0
            self.line_end = 0
        # variable local name - variable uniform name
        self.variables = BriefVariableSet()

    def __str__(self):
        return self.stringify(self)

    def stringify_subtree(self, sstr: str, indent: int):
        pads = ' ' * (indent * 4)
        sstr += pads
        sstr += self.__str__()
        sstr += '\n'
        for arg in self.arguments:
            sstr = arg.stringify_subtree(sstr, indent + 1)
        for b_list in self.body.values():
            for b_child in b_list:
                sstr = b_child.stringify_subtree(sstr, indent + 1)
        return sstr

    def stringify(self,
                  node: 'BriefNode',
                  var_names_source: str = VAR_NAMES_ORIGINAL) -> str:
        s = self.stringify_expression(node, var_names_source)
        if node.depth > 0:
            s = f'{s} [{node.depth}]'
        return s

    def get_variable_name(self,
                          node: 'BriefNode',
                          uniform_var_names: str = VAR_NAMES_ORIGINAL) -> str:
        orig_name = node.id
        if node.instance is not None:
            orig_name = node.instance + '.' + node.id
        if uniform_var_names == VAR_NAMES_ORIGINAL:
            return orig_name
        var = self.variables.find_var(orig_name)
        if not var:
            return orig_name
        if uniform_var_names == VAR_NAMES_INDEX:
            return var.block_index
        return var.usage_hash

    def stringify_expression(self,
                             node: 'BriefNode',
                             uniform_var_names: str = VAR_NAMES_ORIGINAL) -> str:
        if node.function == 'Name':
            return self.get_variable_name(node, uniform_var_names)

        if node.function == 'NameConstant':
            return self.get_variable_name(node, uniform_var_names)

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
            test_node = self.stringify(node.body[""][0])
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

    def explore_variables(self):
        if self.function == 'Name' or self.function == 'NameConstant':
            self.variables.add_variable(self.id)
        for k in self.body:
            for node in self.body[k]:
                node.explore_variables()
                self.variables.update(node.variables)
        for node in self.arguments:
            node.explore_variables()
            self.variables.update(node.variables)
        for i in range(len(self.variables.variables)):
            self.variables.variables[i].block_index = str(i)
