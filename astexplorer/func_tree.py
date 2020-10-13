from typing import List, Dict

from astexplorer.brief_node import BriefVariableSet, BriefNode, \
    VAR_NAMES_INDEX, VAR_NAMES_HASH, get_hash


class FuncTree:
    default_node_weight = 10

    weight_by_function = {'Attribute': 1, 'Name': 1, 'Num': 1, 'NameConstant': 1, 'Str': 1, 'Tuple': 5}

    def __init__(self, name: str):
        self.file = ''
        self.children = []  # type: List[BriefNode]
        self.name = name
        self.args = {}

    def __str__(self):
        args = ', '.join(self.args)
        return 'def ' + self.name + '(' + args + '):'

    def stringify(self) -> str:
        title = str(self) + '\n'
        for child in self.children:
            title = child.stringify_subtree(title, 0)
        return title

    def calc_hashes(self) -> None:
        # first, calculate hashes substituting variables by their indices
        for child in self.children:
            self.calc_hash(child, VAR_NAMES_INDEX)
        self.hashify_variables()
        for child in self.children:
            self.calc_hash(child, VAR_NAMES_HASH)

    def calc_hash(self,
                  child: BriefNode,
                  var_names: str) -> str:
        hash_src = child.stringify(child, var_names)
        # plus body items
        for key in child.body:
            for sub in child.body[key]:
                hash_src += self.calc_hash(sub, var_names)
        # plus arguments
        for arg in child.arguments:
            hash_src += self.calc_hash(arg, var_names)

        child.hash_by_type[var_names] = get_hash(hash_src)
        return child.hash_by_type[var_names]

    def hashify_variables(self):
        # calculate hashes for all variables
        var_hashes = {}  # Dict[str, str]
        for child in self.children:
            self.calc_and_sum_hashes(child, var_hashes)
        # propagate variable hashes from top to bottom
        for child in self.children:
            self.propagate_var_hashes_down(child, var_hashes)

    def propagate_var_hashes_down(self, node: BriefNode, var_hashes: Dict[str, str]):
        for var in node.variables.variables:
            var.usage_hash = var_hashes.get(var.name)
        for key in node.body:
            for child in node.body[key]:
                self.propagate_var_hashes_down(child, var_hashes)
        for child in node.arguments:
            self.propagate_var_hashes_down(child, var_hashes)

    def calculate_variable_hashes(self, node: BriefNode) -> Dict[str, str]:
        var_hashes = {}  # Dict[str, str]
        for key in node.body:
            for child in node.body[key]:
                self.calc_and_sum_hashes(child, var_hashes)
        for child in node.arguments:
            self.calc_and_sum_hashes(child, var_hashes)
        # add own variable hashes
        for i in range(len(node.variables.variables)):
            var = node.variables.variables[i]
            var_hash = node.hash_by_type[VAR_NAMES_INDEX] + str(i)
            if var.name not in var_hashes:
                var_hashes[var.name] = var_hash
            else:
                var_hashes[var.name] = get_hash(var_hash + var_hashes[var.name])
            var.usage_hash = var_hashes[var.name]
        return var_hashes

    def calc_and_sum_hashes(self, node: BriefNode, var_hashes: Dict[str, str]):
        sub_hashes = self.calculate_variable_hashes(node)
        for var_name in sub_hashes:
            if var_name not in var_hashes:
                var_hashes[var_name] = sub_hashes[var_name]
            else:
                var_hashes[var_name] = get_hash(var_hashes[var_name] + sub_hashes[var_name])

    def weight_tree(self) -> None:
        # give weight to each node, recursively
        # the weight reflects node's depth and complexity
        for child in self.children:
            self.weight_sub_tree(child, 1)

    def weight_sub_tree(self, child: BriefNode, depth: int) -> List[int]:
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

    def rename_ptrs_for_node(self, node: BriefNode) -> None:
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

    def find_suitable_ptr(self, name: str) -> str:
        if name not in self.args:
            return name
        if name == 'self':
            return name
        return '#p' + str(self.args[name])