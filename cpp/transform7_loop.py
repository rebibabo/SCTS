from utils import replace_from_blob, traverse_rec_func, text
from .transform1_blank import rec_IfForWhileNoBracket, cvt_AddIfForWhileBracket

def get_for_info(node):
    # 提取for循环的abc信息，for(a;b;c)以及后面接的语句
    i, abc = 0, [None, None, None, None]
    for child in node.children:
        if child.type in [';', ')', 'declaration']:
            if child.type == 'declaration':
                abc[i] = child
            if child.prev_sibling.type not in ['(', ';']:
                abc[i] = child.prev_sibling
            i += 1
        if child.prev_sibling and child.prev_sibling.type == ')' and i == 3:
            abc[3] = child
    return abc

def get_indent(start_byte, code):
    indent = 0
    i = start_byte
    while i >= 0 and code[i] != '\n':
        if code[i] == ' ':
            indent += 1
        elif code[i] == '\t':
            indent += 8
        i -= 1
    return indent

def contain_id(node, contain):
    # 返回node节点子树中的所有变量名
    if node.child_by_field_name('index'):   # a[i] < 2中的index：i
        contain.add(text(node.child_by_field_name('index')))
    if node.type == 'identifier' and node.parent.type not in ['subscript_expression', 'call_expression']:   # a < 2中的a
        contain.add(text(node))
    if not node.children:
        return
    for n in node.children:
        contain_id(n, contain)

'''==========================匹配========================'''
def rec_For(node):
    if node.type == 'for_statement':
        return True

def rec_while(node):
    if node.type == 'while_statement':
        return True

'''==========================替换========================'''
def cvt_OBC(node, code):
    # a for(;b;c)
    abc = get_for_info(node)
    indent = get_indent(node.start_byte, code)
    if abc[0] is not None:  # 如果有a
        if abc[0].type != 'declaration':    
            return [(abc[0].end_byte, abc[0].start_byte - abc[0].end_byte),
                    (node.start_byte, text(abc[0]) + f';\n{indent * " "}')]
        else:   # 如果是int a, b在for循环里面
            return [(abc[0].end_byte - 1, abc[0].start_byte - abc[0].end_byte + 1),
                    (node.start_byte, text(abc[0]) + f'\n{indent * " "}')]

    
def cvt_AOC(node, code):
    # for(a;;c) if b break
    ret, add_bracket = [], None
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    abc = get_for_info(node)
    if abc[1] is not None:  # 如果有b
        ret.append((abc[1].end_byte, abc[1].start_byte - abc[1].end_byte))
        if abc[3] is None:
            return
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        ret.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
        if add_bracket:
            ret.extend(add_bracket)
        return ret
                
def cvt_ABO(node, code):
    # for(a;b;) c
    ret, add_bracket = [], None
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    abc = get_for_info(node)   
    if abc[2] is not None:  # 如果有c
        ret.append((abc[2].end_byte, abc[2].start_byte - abc[2].end_byte))
        if abc[3] is None:
            return
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        ret.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
        if add_bracket:
            ret.extend(add_bracket)
        return ret

def cvt_AOO(node, code):
    # for(a;;) if b break c
    ret, add_bracket = [], None
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    abc = get_for_info(node)
    if abc[1] is not None:  # 如果有b
        ret.append((abc[1].end_byte, abc[1].start_byte - abc[1].end_byte))
        if abc[3] is None:
            return
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        ret.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
    if abc[2] is not None:  # 如果有c
        ret.append((abc[2].end_byte, abc[2].start_byte - abc[2].end_byte))
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        ret.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
    if add_bracket:
        ret.extend(add_bracket)
    return ret

def cvt_OBO(node, code):
    # a for(;b;) c
    ret, add_bracket = [], None
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    abc = get_for_info(node)
    if abc[0] is not None:  # 如果有a
        indent = get_indent(node.start_byte, code)
        if abc[0].type != 'declaration':
            ret.append((abc[0].end_byte, abc[0].start_byte - abc[0].end_byte))
            ret.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
        else:
            ret.append((abc[0].end_byte - 1, abc[0].start_byte - abc[0].end_byte + 1))
            ret.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))  
    if abc[2] is not None:  # 如果有c
        ret.append((abc[2].end_byte, abc[2].start_byte - abc[2].end_byte))
        if abc[3] is None:
            return
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        ret.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
    if add_bracket:
        ret.extend(add_bracket)
    return ret

def cvt_OOC(node, code):
    # a for(;;c) if b break
    ret, add_bracket = [], None
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    abc = get_for_info(node)
    if abc[0] is not None:  # 如果有a
        indent = get_indent(node.start_byte, code)
        if abc[0].type != 'declaration':
            ret.append((abc[0].end_byte, abc[0].start_byte - abc[0].end_byte))
            ret.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
        else:
            ret.append((abc[0].end_byte - 1, abc[0].start_byte - abc[0].end_byte + 1))
            ret.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
    if abc[1] is not None:  # 如果有b
        ret.append((abc[1].end_byte, abc[1].start_byte - abc[1].end_byte))
        if abc[3] is None:
            return
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        ret.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
    if add_bracket:
        ret.extend(add_bracket)
    return ret

def cvt_OOO(node, code):
    # a for(;;;) if break b c
    ret, add_bracket = [], None
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    abc = get_for_info(node)
    if abc[0] is not None:  # 如果有a
        indent = get_indent(node.start_byte, code)
        if abc[0].type != 'declaration':
            ret.append((abc[0].end_byte, abc[0].start_byte - abc[0].end_byte))
            ret.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
        else:
            ret.append((abc[0].end_byte - 1, abc[0].start_byte - abc[0].end_byte + 1))
            ret.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
    if abc[1] is not None:  # 如果有b
        ret.append((abc[1].end_byte, abc[1].start_byte - abc[1].end_byte))
        if abc[3] is None:
            return
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        ret.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
    if abc[2] is not None:  # 如果有c
        ret.append((abc[2].end_byte, abc[2].start_byte - abc[2].end_byte))
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        ret.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
    if add_bracket:
        ret.extend(add_bracket)
    return ret

def cvt_for(node, code):
    # for(a;b;c)
    a = b = c = None
    b = node.children[1].children[1]
    id, prev_id, clause_id = set(), set(), set()
    contain_id(b, id)
    if len(id) == 0:
        return
    id = list(id)[0]
    prev = node.prev_sibling
    if prev.type == 'declaration' and prev.child_count == 3 or prev.type == 'expression_statement' and prev.children[0].type in ['update_expression', 'assignment_expression']:
        contain_id(node.prev_sibling, prev_id)
    if len(prev_id):
        for each in list(prev_id):
            if each in id:    # 如果前面一句是声明或者赋值并且和循环的id一样
                a = node.prev_sibling
    for each in node.children[2].children[1: -1]:
        if each.type == 'expression_statement' and each.parent.type not in ['if_statement', 'for_statement', 'else_clause', 'while_statement']:  # 是i++,i+=1这种表达式，且不能在从句里面
            if each.children[0].type in ['update_expression', 'assignment_expression']:
                contain_id(each.children[0], clause_id)
                if len(clause_id) == 1 and id in clause_id: # 从句里面如果有++或者赋值运算并且变量名为id，则添加c
                    c = each
                    break
    ret = [(node.children[1].end_byte, node.children[0].start_byte - node.children[1].end_byte)]
    if a:
        ret.append((a.end_byte, a.prev_sibling.end_byte - a.end_byte))
    if c:
        ret.append((c.end_byte, c.prev_sibling.end_byte - c.end_byte))
    text_a = text(a) if a else ''
    for_str = f"for({text_a}{'; ' if ';' not in text_a else ' '}{text(b)}; {text(c).replace(';', '') if c else ''})"
    ret.append((node.start_byte, for_str))
    return ret

def cvt_while(node, code):
    # a while(b) c
    ret, add_bracket = [], None
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    abc = get_for_info(node)
    child_index = 3 + (4 - abc.count(None)) - (abc[0] is not None and abc[0].type == 'declaration')
    ret = [(node.children[child_index].end_byte, node.children[0].start_byte - node.children[child_index].end_byte)]    # 删除for(a;b;c)
    if abc[0] is not None:  # 如果有a
        indent = get_indent(node.start_byte, code)
        if abc[0].type != 'declaration':
            ret.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
        else:
            ret.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
    if abc[2] is not None:  # 如果有c
        if abc[3].type == 'compound_statement':     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        ret.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
    while_str = f"while({text(abc[1]) if abc[1] else ''})"
    ret.append((node.children[0].start_byte, while_str))
    if add_bracket:
        ret.extend(add_bracket)
    return ret