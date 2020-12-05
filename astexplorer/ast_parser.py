from ast import parse
import codecs
import regex as re
from _ast import Module
from typing import List, Tuple, Optional, Any
from astexplorer.brief_node import BriefNode
from astexplorer.func_tree import FuncTree


class FileLines:
    REG_NEWLINE = re.compile(r'(\r\n?|\n)+')
    NEW_CHARS = {chr(0x0A), chr(0x0D)}

    def __init__(self, file_data: str):
        # start - end indices of each line
        self.lines: List[Tuple[int, int]] = []
        self.get_file_lines(file_data)

    def get_file_lines(self, data: str) -> None:
        start, i = 0, -1

        for c in data:
            i += 1
            if c not in self.NEW_CHARS:
                continue
            if c == chr(0x0A):
                self.lines.append((start, i,))
                start = i + 1
                continue
            if c == chr(0x0D):
                start += 1

        if start < len(data):
            self.lines.append((start, len(data),))

    def get_file_lines2(self, data: str) -> None:
        start = 0
        for mth in self.REG_NEWLINE.finditer(data):
            s = mth.start()
            e = mth.end()
            self.lines.append((start, s,))
            start = e + 1
        if start < len(data):
            self.lines.append((start, len(data),))

    def get_line_start_end(self, line_num: int, col_offset: int) -> Tuple[int, int]:
        line = self.lines[line_num - 1]
        return line[0] + col_offset, line[1]

    def get_node_line_start_end(self, node: Any) -> Tuple[int, int]:
        line = self.lines[node.lineno - 1]
        return line[0] + node.col_offset, line[1]


class AstParser:
    def __init__(self):
        self.file_path = ''
        self.line_data: Optional[FileLines] = None
        pass

    def parse_module(self, file_path: str) -> List[FuncTree]:
        with codecs.open(file_path, 'r', encoding='utf-8') as fr:
            data = fr.read()
        return self.parse_string(data, file_path)

    def parse_string(self, data: str, file_path: str) -> List[FuncTree]:
        self.line_data = FileLines(data)
        ast = parse(data, file_path, "exec")
        functions = self.go_down_tree(ast)
        for f in functions:
            f.file = file_path
        return functions

    def go_down_tree(self, ast: Module) -> List[FuncTree]:
        functions = []  # type: List[FuncTree]
        if ast.body is None:
            return functions
        return self.go_down_body(ast.body, functions)

    def go_down_body(self, node, functions: List[FuncTree]) -> List[FuncTree]:
        for item in node:
            if item.__class__.__name__ == 'ClassDef':
                if hasattr(item, 'body'):
                    self.go_down_body(item.body, functions)
                continue
            if item.__class__.__name__ == 'FunctionDef':
                func = self.go_down_func(item)
                functions.append(func)
        return functions

    def go_down_func(self, node) -> FuncTree:
        func = FuncTree(node.name)
        args = node.args.args
        if args is not None:
            i = 0
            for arg in args:
                func.args[arg.arg] = i
                i = i + 1
        for item in node.body:
            start, end = self.line_data.get_line_start_end(item.lineno, item.col_offset)
            child = BriefNode(item.__class__.__name__, (start, end,))
            func.children.append(child)
            self.go_down_expression(item, child)

        for node in func.children:
            node.explore_variables()
        return func

    def go_down_expression(self, node, child):
        if node.__class__.__name__ == "Expr":
            node = node.value
            child.function = node.__class__.__name__
            child.id = child.function

        if node.__class__.__name__ == 'If':
            self.go_down_if_expression(node, child)
            return
        if node.__class__.__name__ == 'For':
            self.go_down_for_expression(node, child)
            return
        if node.__class__.__name__ == 'While':
            self.go_down_while_expression(node, child)
            return
        if node.__class__.__name__ == 'Call':
            self.go_down_call_expression(node, child)
            return
        if node.__class__.__name__ == 'Lambda':
            self.go_down_lambda_expression(node, child)
            return
        if node.__class__.__name__ == 'Assign':
            self.go_down_assign_expression(node, child)
            return
        if node.__class__.__name__ == 'With':
            self.process_with_op(node, child)
            return
        if node.__class__.__name__ == 'AugAssign':
            self.go_down_aug_assign_expression(node, child)
        if node.__class__.__name__ == 'BinOp':
            self.go_down_bin_op(node, child)
            return
        if node.__class__.__name__ == 'UnaryOp':
            self.go_down_unary_op(node, child)
            return
        if node.__class__.__name__ == 'Compare':
            self.go_down_compare(node, child)
            return
        if node.__class__.__name__ == 'Num':
            self.process_num_arg(node, child)
            return
        if node.__class__.__name__ == 'Str':
            self.process_str_arg(node, child)
            return
        if node.__class__.__name__ == 'NameConstant':
            self.process_name_const(node, child)
            return
        if node.__class__.__name__ == 'Attribute':
            self.process_attribute(node, child)
            return
        if node.__class__.__name__ == 'Tuple':
            self.process_tuple(node, child)
            return
        if node.__class__.__name__ == 'List':
            self.process_list(node, child)
            return
        if node.__class__.__name__ == 'Raise':
            self.process_raise(node, child)
            return
        if node.__class__.__name__ == 'Return':
            self.process_return(node, child)
            return

        if hasattr(node, 'id'):
            child.id = node.id
        return

    def process_return(self, node, child):
        loc = None if node.value is None else \
            self.line_data.get_node_line_start_end(node.value)
        val_node = BriefNode(node.value.__class__.__name__, loc)
        child.body["_"] = [val_node]

        if node.value is None:
            val_node.function = 'NameConstant'
            val_node.id = 'None'
            return

        self.go_down_expression(node.value, val_node)
        return

    def process_list(self, node, child):
        elts = []
        for elt in node.elts:
            loc = self.line_data.get_line_start_end(elt.lineno, elt.col_offset)
            e_node = BriefNode(elt.__class__.__name__, loc)
            self.go_down_expression(elt, e_node)
            elts.append(e_node)
        child.body["items"] = elts
        return

    def process_raise(self, node, child):
        loc = self.line_data.get_line_start_end(node.exc.lineno, node.exc.col_offset)
        exc_child = BriefNode(node.exc.__class__.__name__, loc)
        self.go_down_expression(node.exc, exc_child)
        child.body["_"] = [exc_child]
        return

    def process_attribute(self, node, child):
        # name in buffer.name
        child.id = node.attr

        # buffer in buffer.name
        if hasattr(node.value, 'id'):
            child.instance = node.value.id
        else:
            loc = self.line_data.get_line_start_end(node.value.lineno, node.value.col_offset)
            attr = BriefNode(node.value.__class__.__name__, node.value.loc)
            self.go_down_expression(node.value, attr)
            child.arguments.append(attr)
            s = []
            child.instance = '.'.join(self.unwind_attribute_chain(child, s))
        return

    @classmethod
    def unwind_attribute_chain(cls, c, s):
        if len(c.arguments) == 0:
            s.append(str(c))
            return s
        s.append(str(c.arguments[0]))
        return s

    def process_tuple(self, node, child):
        for elt in node.elts:
            e_node = BriefNode(elt.__class__.__name__, elt.loc)
            self.go_down_expression(elt, e_node)
            child.arguments.append(e_node)
        return

    def process_with_op(self, node, child):
        # with itself
        child.body["opt_expr"] = []
        child.body["opt_vars"] = []
        for item in node.items:
            if hasattr(item, 'optional_vars'):
                var_name = BriefNode('Name', item.loc)
                var_name.id = item.optional_vars.id
                child.body["opt_vars"].append(var_name)
            expr_node = item.context_expr
            expr_child = BriefNode(expr_node.__class__.__name__, expr_node.loc)
            self.go_down_expression(expr_node, expr_child)
            child.body["opt_expr"].append(expr_child)

        # with body
        b_children = []
        for b_item in node.body:
            body_child = BriefNode(b_item.__class__.__name__, b_item.loc)
            b_children.append(body_child)
            self.go_down_expression(b_item, body_child)
        child.body[""] = b_children

    def process_name_const(self, node, child):
        if hasattr(node, 'value'):
            child.id = str(node.value)
        return

    def process_num_arg(self, node, child):
        if hasattr(node, 'n'):
            child.id = str(node.n)
        return

    def process_str_arg(self, node, child):
        child.id = node.s
        return

    def go_down_compare(self, node, child):
        # left
        loc = self.line_data.get_line_start_end(node.left.lineno, node.left.col_offset)
        left_node = BriefNode(node.left.__class__.__name__, loc)
        self.go_down_expression(node.left, left_node)
        child.body["left"] = [left_node]

        # ops
        if hasattr(node, 'ops'):
            child.id = ", ".join([i.__class__.__name__ for i in node.ops])

        # comparators
        if hasattr(node, 'comparators'):
            compars = []
            for cmp in node.comparators:
                loc = self.line_data.get_line_start_end(cmp.lineno, cmp.col_offset)
                cmp_child = BriefNode(cmp.__class__.__name__, loc)
                self.go_down_expression(cmp, cmp_child)
                compars.append(cmp_child)
            child.body["comparators"] = compars

    def go_down_unary_op(self, node, child):
        loc = self.line_data.get_line_start_end(node.operand.lineno, node.operand.col_offset)
        operand = BriefNode(node.operand.__class__.__name__, loc)
        self.go_down_expression(node.operand, operand)
        child.body["_"] = [operand]
        child.id = node.op.__class__.__name__

    def go_down_bin_op(self, node, child):
        child.function = node.op.__class__.__name__
        child.id = child.function
        # left
        loc = self.line_data.get_line_start_end(node.left.lineno, node.left.col_offset)
        left_node = BriefNode(node.left.__class__.__name__, loc)
        self.go_down_expression(node.left, left_node)
        child.body["left"] = [left_node]

        # right
        loc = self.line_data.get_line_start_end(node.right.lineno, node.right.col_offset)
        right_node = BriefNode(node.right.__class__.__name__, loc)
        self.go_down_expression(node.right, right_node)
        child.body["right"] = [right_node]

    def go_down_assign_expression(self, node, child):
        # right side: delve into targets
        for arg in node.targets:
            loc = self.line_data.get_line_start_end(arg.lineno, arg.col_offset)
            child.arguments.append(BriefNode(arg.__class__.__name__, loc))
            self.go_down_expression(arg, child.arguments[-1])

        # left side
        loc = self.line_data.get_line_start_end(node.value.lineno, node.value.col_offset)
        val_node = BriefNode(node.value.__class__.__name__, loc)
        child.body["_"] = [val_node]
        self.go_down_expression(node.value, val_node)
        for left_arg in child.arguments:
            child.mutating_variables.add(left_arg.id)
        return

    def go_down_aug_assign_expression(self, node, child):
        # target
        loc = self.line_data.get_line_start_end(node.target.lineno, node.target.col_offset)
        child.arguments.append(BriefNode(node.target.__class__.__name__, loc))
        self.go_down_expression(node.target, child.arguments[-1])

        # value
        loc = self.line_data.get_line_start_end(node.value.lineno, node.value.col_offset)
        val_node = BriefNode(node.value.__class__.__name__, loc)
        child.body["_"] = [val_node]
        self.go_down_expression(node.value, val_node)

        # op
        child.id = node.op.__class__.__name__
        for left_arg in child.arguments:
            child.mutating_variables.add(left_arg.id)

    def go_down_call_expression(self, node, child):
        # delve into args
        args = node.args
        if hasattr(node, 'kwargs'):
            if node.kwargs is not None:
                args.append(node.kwargs)
        for arg in args:
            loc = self.line_data.get_line_start_end(arg.lineno, arg.col_offset)
            child.arguments.append(BriefNode(arg.__class__.__name__, loc))
            self.go_down_expression(arg, child.arguments[-1])

        # function name
        if hasattr(node.func, 'id'):
            child.id = node.func.id
        elif hasattr(node.func, 'attr'):
            child.id = node.func.attr

        # node.func.value.id (obj.call_some(), ... = obj)
        if hasattr(node.func, 'value'):
            if hasattr(node.func.value, 'id'):
                child.instance = node.func.value.id

        # TODO: add only mutable type variables
        for left_arg in child.arguments:
            if left_arg.function in {'Name', 'Attribute'}:
                child.mutating_variables.add(left_arg.id)

    def go_down_lambda_expression(self, node, child):
        # args
        for arg in node.args.args:
            loc = self.line_data.get_line_start_end(arg.lineno, arg.col_offset)
            a_child = BriefNode(arg.__class__.__name__, loc)
            a_child.id = 'arg'
            child.arguments.append(a_child)

        # body
        b_child = BriefNode(node.body.__class__.__name__, node.body.loc)
        self.go_down_expression(node.body, b_child)
        child.body[""] = [b_child]

    def go_down_if_expression(self, node, child):
        # delve into (test)
        loc = self.line_data.get_line_start_end(node.test.lineno, node.test.col_offset)
        child.arguments.append(BriefNode(node.test.__class__.__name__, loc))
        self.go_down_expression(node.test, child.arguments[0])

        if hasattr(node, 'orelse'):
            child.body['orelse'] = []
            for ore in node.orelse:
                loc = self.line_data.get_line_start_end(ore.lineno, ore.col_offset)
                if ore.__class__.__name__ == 'If':
                    or_child = BriefNode('Elif', loc)
                    self.go_down_expression(ore, or_child)
                    child.body['orelse'].append(or_child)
                else:
                    else_child = BriefNode('Else')
                    else_body = BriefNode(ore.__class__.__name__, loc)
                    self.go_down_expression(ore, else_body)
                    else_child.body[""] = [else_body]
                    child.body['orelse'].append(else_child)

        # delve into body
        b_children = []
        for b_item in node.body:
            loc = self.line_data.get_line_start_end(b_item.lineno, b_item.col_offset)
            body_child = BriefNode(b_item.__class__.__name__, loc)
            b_children.append(body_child)
            self.go_down_expression(b_item, body_child)
        child.body[""] = b_children

    def go_down_for_expression(self, node, child):
        # iterator
        loc = self.line_data.get_line_start_end(node.target.lineno, node.target.col_offset)
        arg_child = BriefNode(node.target.__class__.__name__, loc)
        self.go_down_expression(node.target, arg_child)
        child.arguments.append(arg_child)

        # iterating object
        loc = self.line_data.get_line_start_end(node.iter.lineno, node.iter.col_offset)
        for_val = BriefNode(node.iter.__class__.__name__, loc)
        self.go_down_expression(node.iter, for_val)
        child.arguments.append(for_val)

        # body
        child.body[""] = self.get_node_body_list(node.body)

    def go_down_while_expression(self, node, child):
        # test expr
        loc = self.line_data.get_line_start_end(node.test.lineno, node.test.col_offset)
        test_node = BriefNode(node.test.__class__.__name__, loc)
        self.go_down_expression(node.test, test_node)
        child.body["test"] = [test_node]

        # body
        child.body["_"] = self.get_node_body_list(node.body)

    def get_node_body_list(self, node_body):
        b_children = []
        for b_item in node_body:
            loc = self.line_data.get_line_start_end(b_item.lineno, b_item.col_offset)
            body_child = BriefNode(b_item.__class__.__name__, loc)
            b_children.append(body_child)
            self.go_down_expression(b_item, body_child)
        return b_children
