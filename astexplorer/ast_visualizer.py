import sys, re
from datetime import date, time
import json
from pythonparser import source, lexer, diagnostic, parser, parse
from astexplorer.brief_tree import *


def serialize(obj):
    if isinstance(obj, date):
        serial = obj.isoformat()
        return serial

    if isinstance(obj, time):
        serial = obj.isoformat()
        return serial

    return obj.__dict__


def go_down_tree(ast):
    functions = []
    if ast.body is None:
        return functions
    return go_down_body(ast.body, functions)


def go_down_body(node, functions):
    for item in node:
        if item.__class__.__name__ == 'FunctionDef':
            func = go_down_func(item)
            functions.append(func)
    return functions


def go_down_func(node):
    func = FuncTree(node.name)
    args = node.args.args
    if args is not None:
        i = 0
        for arg in args:
            func.args[arg.arg] = i
            i = i + 1
    for item in node.body:
        child = BriefNode(item.__class__.__name__)
        func.children.append(child)
        go_down_expression(item, child)

    return func


def go_down_expression(node, child):
    if node.__class__.__name__ == 'If':
        go_down_if_expression(node, child)
        return
    if node.__class__.__name__ == 'Call':
        go_down_call_expression(node, child)
        return
    if node.__class__.__name__ == 'Assign':
        go_down_assign_expression(node, child)
        return
    if node.__class__.__name__ == 'BinOp':
        go_down_bin_op(node, child)
        return
    if node.__class__.__name__ == 'Compare':
        go_down_compare(node, child)
        return
    if node.__class__.__name__ == 'Num':
        process_num_arg(node, child)
        return
    if node.__class__.__name__ == 'NameConstant':
        process_name_const(node, child)
        return
    if node.__class__.__name__ == 'Attribute':
        process_attribute(node, child)
        return
    if node.__class__.__name__ == 'Return':
        process_return(node, child)
        return

    if hasattr(node, 'id'):
        child.id = node.id
    return


def process_return(node, child):
    val_node = BriefNode(node.value.__class__.__name__)
    child.body["_"] = val_node
    go_down_expression(node.value, val_node)
    return


def process_attribute(node, child):
    if hasattr(node.value, 'id'):
        child.instance = node.value.id
    child.id = node.attr
    return


def process_name_const(node, child):
    if hasattr(node, 'value'):
        child.id = str(node.value)
    return


def process_num_arg(node, child):
    if hasattr(node, 'n'):
        child.id = str(node.n)
    return


def go_down_compare(node, child):
    # left
    left_node = BriefNode(node.left.__class__.__name__)
    go_down_expression(node.left, left_node)
    child.body["left"] = left_node

    # ops
    if hasattr(node, 'ops'):
        child.id = ", ".join([i.__class__.__name__ for i in node.ops])

    # comparators
    if hasattr(node, 'comparators'):
        cp_index = 0
        for cmp in node.comparators:
            cmp_child = BriefNode(cmp.__class__.__name__)
            go_down_expression(cmp, cmp_child)
            child.body["cmp" + str(cp_index)] = cmp_child
    return


def go_down_bin_op(node, child):
    child.function = node.op.__class__.__name__
    # left
    left_node = BriefNode(node.left.__class__.__name__)
    go_down_expression(node.left, left_node)
    child.body["left"] = left_node

    # right
    right_node = BriefNode(node.right.__class__.__name__)
    go_down_expression(node.right, right_node)
    child.body["right"] = right_node
    return


def go_down_assign_expression(node, child):
    # right side: delve into targets
    for arg in node.targets:
        child.arguments.append(BriefNode(arg.__class__.__name__))
        go_down_expression(arg, child.arguments[-1])

    # left side
    val_node = BriefNode(node.value.__class__.__name__)
    child.body["_"] = val_node
    go_down_expression(node.value, val_node)
    return


def go_down_call_expression(node, child):
    # delve into args
    for arg in node.args:
        child.arguments.append(BriefNode(arg.__class__.__name__))
        go_down_expression(arg, child.arguments[-1])

    # function name
    if hasattr(node.func, 'id'):
        child.id = node.func.id
    elif hasattr(node.func, 'attr'):
        child.id = node.func.attr

    # node.func.value.id (obj.call_some(), ... = obj)
    if hasattr(node.func, 'value'):
        if hasattr(node.func.value, 'id'):
            child.instance = node.func.value.id
    return


def go_down_if_expression(node, child):
    # delve into (test)
    child.arguments.append(BriefNode(node.test.__class__.__name__))
    go_down_expression(node.test, child.arguments[0])

    # delve into body
    b_children = []
    for b_item in node.body:
        body_child = BriefNode(b_item.__class__.__name__)
        b_children.append(body_child)
        go_down_expression(b_item, body_child)
    child.body["_"] = b_children
    return


with open(sys.argv[1], 'r') as myfile:
    data = myfile.read()


ast = parse(data, sys.argv[1], "exec")
tree = go_down_tree(ast)
print(json.dumps(tree, default=serialize, sort_keys=False, indent=4))
#print(ast.__class__.__name__)
#print(str(ast))
