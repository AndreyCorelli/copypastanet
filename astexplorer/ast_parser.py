from astexplorer.brief_tree import *

def go_down_tree(ast):
    functions = []
    if ast.body is None:
        return functions
    return go_down_body(ast.body, functions)


def go_down_tree2(ast):
    functions = []
    if ast.body is None:
        return functions
    return go_down_body(ast.body, functions)


def go_down_body(node, functions):
    for item in node:
        if item.__class__.__name__ == 'ClassDef':
            if hasattr(item, 'body'):
                go_down_body(item.body, functions)
            continue
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
        child = BriefNode(item.__class__.__name__, item.loc)
        func.children.append(child)
        go_down_expression(item, child)

    return func


def go_down_expression(node, child):
    if node.__class__.__name__ == "Expr":
        node = node.value
        child.function = node.__class__.__name__
        child.id = child.function

    if node.__class__.__name__ == 'If':
        go_down_if_expression(node, child)
        return
    if node.__class__.__name__ == 'For':
        go_down_for_expression(node, child)
        return
    if node.__class__.__name__ == 'While':
        go_down_while_expression(node, child)
        return
    if node.__class__.__name__ == 'Call':
        go_down_call_expression(node, child)
        return
    if node.__class__.__name__ == 'Lambda':
        go_down_lambda_expression(node, child)
        return
    if node.__class__.__name__ == 'Assign':
        go_down_assign_expression(node, child)
        return
    if node.__class__.__name__ == 'With':
        process_with_op(node, child)
        return
    if node.__class__.__name__ == 'AugAssign':
        go_down_aug_assign_expression(node, child)
    if node.__class__.__name__ == 'BinOp':
        go_down_bin_op(node, child)
        return
    if node.__class__.__name__ == 'UnaryOp':
        go_down_unary_op(node, child)
        return
    if node.__class__.__name__ == 'Compare':
        go_down_compare(node, child)
        return
    if node.__class__.__name__ == 'Num':
        process_num_arg(node, child)
        return
    if node.__class__.__name__ == 'Str':
        process_str_arg(node, child)
        return
    if node.__class__.__name__ == 'NameConstant':
        process_name_const(node, child)
        return
    if node.__class__.__name__ == 'Attribute':
        process_attribute(node, child)
        return
    if node.__class__.__name__ == 'Tuple':
        process_tuple(node, child)
        return
    if node.__class__.__name__ == 'List':
        process_list(node, child)
        return
    if node.__class__.__name__ == 'Raise':
        process_raise(node, child)
        return
    if node.__class__.__name__ == 'Return':
        process_return(node, child)
        return

    if hasattr(node, 'id'):
        child.id = node.id
    return


def process_return(node, child):
    loc = None if node.value is None else node.value.loc
    val_node = BriefNode(node.value.__class__.__name__, loc)
    child.body["_"] = [val_node]

    if node.value is None:
        val_node.function = 'NameConstant'
        val_node.id = 'None'
        return

    go_down_expression(node.value, val_node)
    return


def process_list(node, child):
    elts = []
    for elt in node.elts:
        e_node = BriefNode(elt.__class__.__name__, elt.loc)
        go_down_expression(elt, e_node)
        elts.append(e_node)
    child.body["items"] = elts
    return


def process_raise(node, child):
    exc_child = BriefNode(node.exc.__class__.__name__, node.exc.loc)
    go_down_expression(node.exc, exc_child)
    child.body["_"] = [exc_child]
    return

def process_attribute(node, child):
    # name in buffer.name
    child.id = node.attr

    # buffer in buffer.name
    if hasattr(node.value, 'id'):
        child.instance = node.value.id
    else:
        attr = BriefNode(node.value.__class__.__name__, node.value.loc)
        go_down_expression(node.value, attr)
        child.arguments.append(attr)
        s = []
        child.instance = '.'.join(unwind_attribute_chain(child, s))
    return


def unwind_attribute_chain(c, s):
    if len(c.arguments) == 0:
        s.append(str(c))
        return s
    s.append(str(c.arguments[0]))
    return s


def process_tuple(node, child):
    for elt in node.elts:
        e_node = BriefNode(elt.__class__.__name__, elt.loc)
        go_down_expression(elt, e_node)
        child.arguments.append(e_node)
    return


def process_with_op(node, child):
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
        go_down_expression(expr_node, expr_child)
        child.body["opt_expr"].append(expr_child)

    # with body
    b_children = []
    for b_item in node.body:
        body_child = BriefNode(b_item.__class__.__name__, b_item.loc)
        b_children.append(body_child)
        go_down_expression(b_item, body_child)
    child.body[""] = b_children
    return


def process_name_const(node, child):
    if hasattr(node, 'value'):
        child.id = str(node.value)
    return


def process_num_arg(node, child):
    if hasattr(node, 'n'):
        child.id = str(node.n)
    return


def process_str_arg(node, child):
    child.id = node.s
    return


def go_down_compare(node, child):
    # left
    left_node = BriefNode(node.left.__class__.__name__, node.left.loc)
    go_down_expression(node.left, left_node)
    child.body["left"] = [left_node]

    # ops
    if hasattr(node, 'ops'):
        child.id = ", ".join([i.__class__.__name__ for i in node.ops])

    # comparators
    if hasattr(node, 'comparators'):
        compars = []
        for cmp in node.comparators:
            cmp_child = BriefNode(cmp.__class__.__name__, cmp.loc)
            go_down_expression(cmp, cmp_child)
            compars.append(cmp_child)
        child.body["comparators"] = compars
    return


def go_down_unary_op(node, child):
    operand = BriefNode(node.operand.__class__.__name__, node.operand.loc)
    go_down_expression(node.operand, operand)
    child.body["_"] = [operand]

    child.id = node.op.__class__.__name__
    return


def go_down_bin_op(node, child):
    child.function = node.op.__class__.__name__
    child.id = child.function
    # left
    left_node = BriefNode(node.left.__class__.__name__, node.left.loc)
    go_down_expression(node.left, left_node)
    child.body["left"] = [left_node]

    # right
    right_node = BriefNode(node.right.__class__.__name__, node.right.loc)
    go_down_expression(node.right, right_node)
    child.body["right"] = [right_node]
    return


def go_down_assign_expression(node, child):
    # right side: delve into targets
    for arg in node.targets:
        child.arguments.append(BriefNode(arg.__class__.__name__, arg.loc))
        go_down_expression(arg, child.arguments[-1])

    # left side
    val_node = BriefNode(node.value.__class__.__name__, node.value.loc)
    child.body["_"] = [val_node]
    go_down_expression(node.value, val_node)
    return


def go_down_aug_assign_expression(node, child):
    # target
    child.arguments.append(BriefNode(node.target.__class__.__name__, node.target.loc))
    go_down_expression(node.target, child.arguments[-1])

    # value
    val_node = BriefNode(node.value.__class__.__name__, node.value.loc)
    child.body["_"] = [val_node]
    go_down_expression(node.value, val_node)

    # op
    child.id = node.op.__class__.__name__
    return


def go_down_call_expression(node, child):
    # delve into args
    args = node.args
    if hasattr(node, 'kwargs'):
        if node.kwargs is not None:
            args.append(node.kwargs)
    for arg in args:
        child.arguments.append(BriefNode(arg.__class__.__name__, arg.loc))
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


def go_down_lambda_expression(node, child):
    # args
    for arg in node.args.args:
        a_child = BriefNode(arg.__class__.__name__, arg.loc)
        a_child.id = 'arg'
        child.arguments.append(a_child)

    # body
    b_child = BriefNode(node.body.__class__.__name__, node.body.loc)
    go_down_expression(node.body, b_child)
    child.body[""] = [b_child]
    return


def go_down_if_expression(node, child):
    # delve into (test)
    child.arguments.append(BriefNode(node.test.__class__.__name__, node.test.loc))
    go_down_expression(node.test, child.arguments[0])

    if hasattr(node, 'orelse'):
        child.body['orelse'] = []
        for ore in node.orelse:
            if ore.__class__.__name__ == 'If':
                or_child = BriefNode('Elif', ore.loc)
                go_down_expression(ore, or_child)
                child.body['orelse'].append(or_child)
            else:
                else_child = BriefNode('Else')
                else_body = BriefNode(ore.__class__.__name__, ore.loc)
                go_down_expression(ore, else_body)
                else_child.body[""] = [else_body]
                child.body['orelse'].append(else_child)

    # delve into body
    b_children = []
    for b_item in node.body:
        body_child = BriefNode(b_item.__class__.__name__, b_item.loc)
        b_children.append(body_child)
        go_down_expression(b_item, body_child)
    child.body[""] = b_children
    return


def go_down_for_expression(node, child):
    # iterator
    arg_child = BriefNode(node.target.__class__.__name__, node.target.loc)
    go_down_expression(node.target, arg_child)
    child.arguments.append(arg_child)

    # iterating object
    for_val = BriefNode(node.iter.__class__.__name__, node.iter.loc)
    go_down_expression(node.iter, for_val)
    child.arguments.append(for_val)

    # body
    child.body[""] = get_node_body_list(node.body)
    return


def go_down_while_expression(node, child):
    # test expr
    test_node = BriefNode(node.test.__class__.__name__, node.test.loc)
    go_down_expression(node.test, test_node)
    child.body["test"] = [test_node]

    # body
    child.body["_"] = get_node_body_list(node.body)
    return


def get_node_body_list(node_body):
    b_children = []
    for b_item in node_body:
        body_child = BriefNode(b_item.__class__.__name__, b_item.loc)
        b_children.append(body_child)
        go_down_expression(b_item, body_child)
    return b_children