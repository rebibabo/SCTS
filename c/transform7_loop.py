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

def is_contain_id(node, id, contain):
    if node.type == 'identifier' and text(node) == id:
        contain.append(1)
    if not node.children:
        return
    for n in node.children:
        is_contain_id(n, id, contain)

'''==========================匹配========================'''
def rec_For(node):
    if node.type == 'for_statement':
        return True

def rec_while(node):
    if node.type == 'while_statement':
        condition = node.children[1].children[1]
        if condition.type == 'binary_expression':
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
    id = ''
    if b.type == 'binary_expression':
        for each in b.children:
            if each.type == 'identifier':
                id = text(each)
    if id:
        return
    for each in node.prev_sibling.children:
        is_contain = []
        is_contain_id(each, id, is_contain)
        if len(is_contain):
            a = node.prev_sibling
    for each in node.children[2].children[1: -1]:
        is_contain = []
        is_contain_id(each, id, is_contain)
        if len(is_contain):
            c = each
    ret = [(node.children[1].end_byte, node.children[0].start_byte - node.children[1].end_byte)]
    if a:
        ret.append((a.end_byte, a.prev_sibling.end_byte - a.end_byte))
    if c:
        ret.append((c.end_byte, c.prev_sibling.end_byte - c.end_byte))
    text_a = text(a) if a else ''
    for_str = f"for({text_a}{'; ' if ';' not in text_a else ' '}{text(b)}; {text(c).replace(';', '') if c else ''})"
    ret.append((node.start_byte, for_str))
    return ret