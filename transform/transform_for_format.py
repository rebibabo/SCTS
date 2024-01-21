from ist_utils import text
from transform.lang import get_lang

declaration_map = {'c': 'declaration', 'java': 'local_variable_declaration', 'c_sharp': 'local_variable_declaration'}
block_map = {'c': 'compound_statement', 'java': 'block', 'c_sharp': 'block'}

def get_for_info(node):
    # 提取for循环的abc信息，for(a;b;c)以及后面接的语句
    i, abc = 0, [None, None, None, None]
    for child in node.children:
        if child.type in [';', ')', declaration_map[get_lang()]]:
            if child.type == declaration_map[get_lang()]:
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
            indent += 4
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

def match_for(root):
    def check(node):
        if node.type == 'for_statement':
            return True
        return False
    res = []
    def match(u):
        if check(u): res.append(u)
        for v in u.children:
            match(v)
    match(root)
    return res

'''==========================替换========================'''
def convert_obc(node, code):
    # a for(;b;c)
    abc = get_for_info(node)
    indent = get_indent(node.start_byte, code)
    if abc[0] is not None:  # 如果有a
        if abc[0].type != declaration_map[get_lang()]:    
            return [(abc[0].end_byte, abc[0].start_byte),
                    (node.start_byte, text(abc[0]) + f';\n{indent * " "}')]
        else:   # 如果是int a, b在for循环里面
            return [(abc[0].end_byte - 1, abc[0].start_byte),
                    (node.start_byte, text(abc[0]) + f'\n{indent * " "}')]

def count_obc(node):
    return 0

def convert_aoc(node, code):
    # for(a;;c) if b break
    res, add_bracket = [], None
    abc = get_for_info(node)
    if abc[1] is not None:  # 如果有b
        res.append((abc[1].end_byte, abc[1].start_byte))
        if abc[3] is None:
            return
        if abc[3].type == block_map[get_lang()]:     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        res.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
        if add_bracket:
            res.extend(add_bracket)
        return res
                
def convert_abo(node, code):
    # for(a;b;) c
    res, add_bracket = [], None
    abc = get_for_info(node)   
    if abc[2] is not None:  # 如果有c
        res.append((abc[2].end_byte, abc[2].start_byte))
        if abc[3] is None:
            return
        if abc[3].type == block_map[get_lang()]:     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        res.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
        if add_bracket:
            res.extend(add_bracket)
        return res

def convert_aoo(node, code):
    # for(a;;) if b break c
    res, add_bracket = [], None
    abc = get_for_info(node)
    if abc[1] is not None:  # 如果有b
        res.append((abc[1].end_byte, abc[1].start_byte))
        if abc[3] is None:
            return
        if abc[3].type == block_map[get_lang()]:     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        res.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
    if abc[2] is not None:  # 如果有c
        res.append((abc[2].end_byte, abc[2].start_byte))
        if abc[3].type == block_map[get_lang()]:     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        res.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
    if add_bracket:
        res.extend(add_bracket)
    return res

def convert_obo(node, code):
    # a for(;b;) c
    res, add_bracket = [], None
    abc = get_for_info(node)
    if abc[0] is not None:  # 如果有a
        indent = get_indent(node.start_byte, code)
        if abc[0].type != declaration_map[get_lang()]:
            res.append((abc[0].end_byte, abc[0].start_byte))
            res.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
        else:
            res.append((abc[0].end_byte - 1, abc[0].start_byte))
            res.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))  
    if abc[2] is not None:  # 如果有c
        res.append((abc[2].end_byte, abc[2].start_byte))
        if abc[3] is None:
            return
        if abc[3].type == block_map[get_lang()]:     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        res.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
    if add_bracket:
        res.extend(add_bracket)
    return res

def convert_ooc(node, code):
    # a for(;;c) if b break
    res, add_bracket = [], None
    abc = get_for_info(node)
    if abc[0] is not None:  # 如果有a
        indent = get_indent(node.start_byte, code)
        if abc[0].type != declaration_map[get_lang()]:
            res.append((abc[0].end_byte, abc[0].start_byte))
            res.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
        else:
            res.append((abc[0].end_byte - 1, abc[0].start_byte))
            res.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
    if abc[1] is not None:  # 如果有b
        res.append((abc[1].end_byte, abc[1].start_byte))
        if abc[3] is None:
            return
        if abc[3].type == block_map[get_lang()]:     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        res.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
    if add_bracket:
        res.extend(add_bracket)
    return res

def convert_ooo(node, code):
    # a for(;;;) if break b c
    res, add_bracket = [], None
    abc = get_for_info(node)
    if abc[0] is not None:  # 如果有a
        indent = get_indent(node.start_byte, code)
        if abc[0].type != declaration_map[get_lang()]:
            res.append((abc[0].end_byte, abc[0].start_byte))
            res.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
        else:
            res.append((abc[0].end_byte - 1, abc[0].start_byte))
            res.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
    if abc[1] is not None:  # 如果有b
        res.append((abc[1].end_byte, abc[1].start_byte))
        if abc[3] is None:
            return
        if abc[3].type == block_map[get_lang()]:     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        res.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
    if abc[2] is not None:  # 如果有c
        res.append((abc[2].end_byte, abc[2].start_byte))
        if abc[3].type == block_map[get_lang()]:     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        res.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
    if add_bracket:
        res.extend(add_bracket)
    return res