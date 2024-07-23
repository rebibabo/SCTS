from utils import text

def get_for_info(node):
    # 提取for循环的abc信息，for(a;b;c)以及后面接的语句
    i, abc = 0, [None, None, None, None]
    for child in node.children:
        if child.type in [';', ')', 'local_variable_declaration']:
            if child.type == 'local_variable_declaration':
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
    while i >= 0 and i < len(code) and code[i] != '\n':
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

def rec_loop(node):
    if node.type in ['while_statement', 'do_statement', 'for_statement']:
        parent = node.parent
        while parent:
            if parent.type in ['while_statement', 'do_statement', 'for_statement']:
                return False
            parent = parent.parent
        return True

def match_While(node):
    if rec_loop(node):
        if node.type == 'while_statement' and node.parent.type != 'labeled_statement':    # 标签语句不处理
            return True

def match_DoWhile(node):
    if rec_loop(node):
        if node.type == 'do_statement' and node.parent.type != 'labeled_statement':    # 标签语句不处理
            return True

def match_ForOBC(node):
    if rec_For(node):
        abc = get_for_info(node)
        if not abc[0] and abc[1] and abc[2]:
            return True

def match_ForAOC(node):
    if rec_For(node):
        abc = get_for_info(node)
        if abc[0] and not abc[1] and abc[2]:
            return True

def match_ForABO(node):
    if rec_For(node):
        abc = get_for_info(node)
        if abc[0] and abc[1] and not abc[2]:
            return True

def match_ForAOO(node):
    if rec_For(node):
        abc = get_for_info(node)
        if abc[0] and not abc[1] and not abc[2]:
            return True

def match_ForOBO(node):
    if rec_For(node):
        abc = get_for_info(node)
        if not abc[0] and abc[1] and not abc[2]:
            return True

def match_ForOOC(node):
    if rec_For(node):
        abc = get_for_info(node)
        if not abc[0] and not abc[1] and abc[2]:
            return True

def match_ForOOO(node):
    if rec_For(node):
        abc = get_for_info(node)
        if not abc[0] and not abc[1] and not abc[2]:
            return True
            
def match_ForAOC(node):
    if rec_For(node):
        abc = get_for_info(node)
        if abc[0] and not abc[1] and abc[2]:
            return True

def match_ForABO(node):
    if rec_For(node):
        abc = get_for_info(node)
        if abc[0] and abc[1] and not abc[2]:
            return True

def match_ForAOO(node):
    if rec_For(node):
        abc = get_for_info(node)
        if abc[0] and not abc[1] and not abc[2]:
            return True

def match_ForOBO(node):
    if rec_For(node):
        abc = get_for_info(node)
        if not abc[0] and abc[1] and not abc[2]:
            return True

def match_ForOOC(node):
    if rec_For(node):
        abc = get_for_info(node)
        if not abc[0] and not abc[1] and abc[2]:
            return True

def match_ForOOO(node):
    if rec_For(node):
        abc = get_for_info(node)
        if not abc[0] and not abc[1] and not abc[2]:
            return True

def rec_IfForWhileNoBracket(node):
    #for(); while(); if();
    if node.type in ['while_statement', 'if_statement', 'for_statement', 'else_clause']:
        for child in node.children:
            if child.type == 'block':
                return False
        return True

'''==========================替换========================'''
def cvt_AddIfForWhileBracket(node, code):
    # 在单行If、For、While添加大括号
    statement_node = None
    for each in node.children:
        if each.type in ['expression_statement', 'return_statement', 'block', 'break_statement', 'for_statement', 'if_statement', 'while_statement']:
            statement_node = each
    if statement_node is None:
        return []
    indent = get_indent(node.start_byte, code)
    
    if '\n' not in text(node):
        return [(statement_node.start_byte, statement_node.prev_sibling.end_byte),
                (statement_node.start_byte, f" {{\n{(indent + 4) * ' '}"), 
                (statement_node.end_byte, f"\n{indent * ' '}}}")]
    else:
        return [(statement_node.prev_sibling.end_byte, f" {{"), 
                (statement_node.end_byte, f"\n{indent * ' '}}}")]

def cvt_OBC(node, code):
    # a for(;b;c)
    add_bracket = []
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    if node.parent.type in ['if_statement', 'while_statement', 'for_statement', 'else_clause'] and rec_IfForWhileNoBracket(node.parent):    # 如果上层循环没有花括号
        add_bracket += cvt_AddIfForWhileBracket(node.parent, code)
    abc = get_for_info(node)
    indent = get_indent(node.start_byte, code)
    if abc[1] and abc[2]:   # 如果有b和c
        if abc[0] is not None:  # 如果有a
            if abc[0].type != 'local_variable_declaration': 
                return add_bracket + [(abc[0].end_byte, abc[0].start_byte),
                        (node.start_byte, text(abc[0]) + f';\n{indent * " "}')]
            else:   # 如果是int a, b在for循环里面
                return add_bracket + [(abc[0].end_byte - 1, abc[0].start_byte),
                        (node.start_byte, text(abc[0]) + f'\n{indent * " "}')]

def cvt_AOC(node, code):
    # for(a;;c) if b break
    ret, add_bracket = [], []
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    abc = get_for_info(node)
    if abc[0] and abc[2]:
        if abc[1] is not None:  # 如果有b
            ret.append((abc[1].end_byte, abc[1].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == 'block':     # 复合语句在第一句插入if b break
                first_expression_node = abc[3].children[1]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                first_expression_node = abc[3]
            indent = get_indent(first_expression_node.start_byte, code)
            ret.append((first_expression_node.start_byte, f"if (!({text(abc[1])}))\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
            if add_bracket:
                ret.extend(add_bracket)
            return ret
                
def cvt_ABO(node, code):
    # for(a;b;) c
    ret, add_bracket = [], []
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    if node.parent.type in ['if_statement', 'while_statement', 'for_statement', 'else_clause'] and rec_IfForWhileNoBracket(node.parent):    # 如果上层循环没有花括号
        add_bracket += cvt_AddIfForWhileBracket(node.parent, code)
    abc = get_for_info(node)   
    if abc[0] and abc[1]:
        if abc[2] is not None:  # 如果有c
            ret.append((abc[2].end_byte, abc[2].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == 'block':     # 复合语句在第一句插入if b break
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
    ret, add_bracket = [], []
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    if node.parent.type in ['if_statement', 'while_statement', 'for_statement', 'else_clause'] and rec_IfForWhileNoBracket(node.parent):    # 如果上层循环没有花括号
        add_bracket += cvt_AddIfForWhileBracket(node.parent, code)
    abc = get_for_info(node)
    if abc[0]:
        if abc[1] is not None:  # 如果有b
            ret.append((abc[1].end_byte, abc[1].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == 'block':     # 复合语句在第一句插入if b break
                first_expression_node = abc[3].children[1]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                first_expression_node = abc[3]
            indent = get_indent(first_expression_node.start_byte, code)
            ret.append((first_expression_node.start_byte, f"if (!({text(abc[1])}))\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
        if abc[2] is not None:  # 如果有c
            ret.append((abc[2].end_byte, abc[2].start_byte))
            if abc[3].type == 'block':     # 复合语句在第一句插入if b break
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
    ret, add_bracket = [], []
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    if node.parent.type in ['if_statement', 'while_statement', 'for_statement', 'else_clause'] and rec_IfForWhileNoBracket(node.parent):    # 如果上层循环没有花括号
        add_bracket += cvt_AddIfForWhileBracket(node.parent, code)
    abc = get_for_info(node)
    if abc[1]:
        if abc[0] is not None:  # 如果有a
            indent = get_indent(node.start_byte, code)
            if abc[0].type != 'local_variable_declaration':
                ret.append((abc[0].end_byte, abc[0].start_byte))
                ret.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
            else:
                ret.append((abc[0].end_byte - 1, abc[0].start_byte))
                ret.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))  
        if abc[2] is not None:  # 如果有c
            ret.append((abc[2].end_byte, abc[2].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == 'block':     # 复合语句在第一句插入if b break
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
    ret, add_bracket = [], []
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    if node.parent.type in ['if_statement', 'while_statement', 'for_statement', 'else_clause'] and rec_IfForWhileNoBracket(node.parent):    # 如果上层循环没有花括号
        add_bracket += cvt_AddIfForWhileBracket(node.parent, code)
    abc = get_for_info(node)
    if abc[2]:
        if abc[0] is not None:  # 如果有a
            indent = get_indent(node.start_byte, code)
            if abc[0].type != 'local_variable_declaration':
                ret.append((abc[0].end_byte, abc[0].start_byte))
                ret.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
            else:
                ret.append((abc[0].end_byte - 1, abc[0].start_byte))
                ret.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
        if abc[1] is not None:  # 如果有b
            ret.append((abc[1].end_byte, abc[1].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == 'block':     # 复合语句在第一句插入if b break
                first_expression_node = abc[3].children[1]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                first_expression_node = abc[3]
            indent = get_indent(first_expression_node.start_byte, code)
            ret.append((first_expression_node.start_byte, f"if (!({text(abc[1])}))\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
        if add_bracket:
            ret.extend(add_bracket)
        return ret

def cvt_OOO(node, code):
    # a for(;;;) if break b c
    ret, add_bracket = [], []
    if rec_IfForWhileNoBracket(node):
        add_bracket = cvt_AddIfForWhileBracket(node, code)
    if node.parent.type in ['if_statement', 'while_statement', 'for_statement', 'else_clause'] and rec_IfForWhileNoBracket(node.parent):    # 如果上层循环没有花括号
        add_bracket += cvt_AddIfForWhileBracket(node.parent, code)
    abc = get_for_info(node)
    if abc[0] is not None:  # 如果有a
        indent = get_indent(node.start_byte, code)
        if abc[0].type != 'local_variable_declaration':
            ret.append((abc[0].end_byte, abc[0].start_byte))
            ret.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
        else:
            ret.append((abc[0].end_byte - 1, abc[0].start_byte))
            ret.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
    if abc[1] is not None:  # 如果有b
        ret.append((abc[1].end_byte, abc[1].start_byte))
        if abc[3] is None:
            return
        if abc[3].type == 'block':     # 复合语句在第一句插入if b break
            first_expression_node = abc[3].children[1]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            first_expression_node = abc[3]
        indent = get_indent(first_expression_node.start_byte, code)
        ret.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
    if abc[2] is not None:  # 如果有c
        ret.append((abc[2].end_byte, abc[2].start_byte))
        if abc[3].type == 'block':     # 复合语句在第一句插入if b break
            last_expression_node = abc[3].children[-2]
        else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
            last_expression_node = abc[3]
        indent = get_indent(last_expression_node.start_byte, code)
        ret.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
    if add_bracket:
        ret.extend(add_bracket)
    return ret

def cvt_for(node, code):
    if node.type == 'while_statement':
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
        ret = [(node.children[1].end_byte, node.children[0].start_byte)]
        if a:
            ret.append((a.end_byte, a.prev_sibling.end_byte))
        if c:
            ret.append((c.end_byte, c.prev_sibling.end_byte))
        text_a = text(a) if a else ''
        for_str = f"for({text_a}{'; ' if ';' not in text_a else ' '}{text(b)}; {text(c).replace(';', '') if c else ''})"
        ret.append((node.start_byte, for_str))
    elif node.type == 'do_statement':   # tx
        a = b = c = None
        for v in node.children:
            if v.type == 'parenthesized_expression':
                b = v.children[1]
                break
        id, prev_id, clause_id = set(), set(), set()
        contain_id(b, id)
        if len(id) == 0:
            return
        id = list(id)[0]
        prev = node.prev_sibling
        if prev.type == 'declaration' and prev.child_count == 3 or prev.type == 'expression_statement' and prev.children[0].type in ['update_expression', 'assignment_expression']:
            contain_id(node.prev_sibling, prev_id)
        if len(prev_id):
            for u in list(prev_id):
                if u in id:    # 如果前面一句是声明或者赋值并且和循环的id一样
                    a = node.prev_sibling
        for u in node.children[1].children[1: -1]:
            if u.type == 'expression_statement' and u.parent.type not in ['if_statement', 'for_statement', 'else_clause', 'while_statement']:  # 是i++,i+=1这种表达式，且不能在从句里面
                if u.children[0].type in ['update_expression', 'assignment_expression']:
                    contain_id(u.children[0], clause_id)
                    if len(clause_id) == 1 and id in clause_id: # 从句里面如果有++或者赋值运算并且变量名为id，则添加c
                        c = u
                        break
        ret = [(node.children[0].end_byte, node.children[0].start_byte),
               (node.children[4].end_byte, node.children[2].start_byte)]
        if a:
            ret.append((a.end_byte, a.prev_sibling.end_byte))
        if c:
            ret.append((c.end_byte, c.prev_sibling.end_byte))
        text_a = text(a) if a else ''
        for_str = f"for({text_a}{'; ' if ';' not in text_a else ' '}{text(b)}; {text(c).replace(';', '') if c else ''})"
        ret.append((node.start_byte, for_str))
    else:
        return
    return ret

def cvt_while(node, code):
    # a while(b) c
    add_parent_bracket = False
    if rec_IfForWhileNoBracket(node.parent):
        add_parent_bracket = True
    if node.type == 'for_statement':
        abc = get_for_info(node)
        indent = get_indent(node.start_byte, code)
        new_str = ''
        if abc[0] is not None:  # 如果有a
            if abc[0].type != 'local_variable_declaration':
                new_str += text(abc[0]) + f';\n{indent * " "}'
            else:
                new_str += text(abc[0]) + f'\n{indent * " "}'
        new_str += f'while({text(abc[1]) if abc[1] else "1"})'
        if abc[3].type == 'block':
            text_statement = text(abc[3])
            if abc[2]:  # 如果有c
                right_bracket_index = text_statement.rfind('}')
                c_str = f'    {text(abc[2])};\n{indent * " "}'
                text_statement = text_statement[:right_bracket_index] + c_str + text_statement[right_bracket_index:]
            new_str += text_statement
        else:
            new_str += f'{{\n{(indent + 4) * " "}{text(abc[3])}\n{indent * " "}}}'
        if add_parent_bracket:
            new_str = f'{{{new_str}\n{(indent - 4)* " "}}}'
        return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]
    elif node.type == 'do_statement':   # tx
        condition_node = node.children[3]
        body = node.child_by_field_name('body')
        new_str = f'while{text(condition_node)}'
        indent = get_indent(node.start_byte, code)
        if body.type == 'block':
            new_str += text(body)
        else:
            new_str += f'{{\n{(indent + 4) * " "}{text(body)}\n{indent * " "}}}'    
        if add_parent_bracket:
            new_str = f'{{{new_str}\n{(indent - 4)* " "}}}'
        return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]

def cvt_do_while(node, code):   # tx
    add_parent_bracket = False
    if rec_IfForWhileNoBracket(node.parent):
        add_parent_bracket = True
    if node.type == 'for_statement':
        # a while(b) c
        abc = get_for_info(node)
        new_str = ''
        indent = get_indent(node.start_byte, code)
        if abc[0] is not None:  # 如果有a
            if abc[0].type != 'local_variable_declaration':
                new_str += text(abc[0]) + f';\n{indent * " "}'
            else:
                new_str += text(abc[0]) + f'\n{indent * " "}'
        new_str += 'do'
        if abc[3].type == 'block':
            text_statement = text(abc[3])
            if abc[2]:  # 如果有c
                right_bracket_index = text_statement.rfind('}')
                c_str = f'    {text(abc[2])};\n{indent * " "}'
                text_statement = text_statement[:right_bracket_index] + c_str + text_statement[right_bracket_index:]
            new_str += text_statement
        else:
            new_str += f'{{\n{(indent + 4) * " "}{text(abc[3])}\n{indent * " "}}}'
        b_str = text(abc[1]) if abc[1] else '1'
        new_str += f'while({b_str});'
        if add_parent_bracket:
            new_str = f'{{{new_str}\n{(indent - 4)* " "}}}'
        return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]
    elif node.type == 'while_statement':
        condition_node = node.children[1]
        new_str = 'do'
        indent = get_indent(node.start_byte, code)
        body = node.child_by_field_name('body')
        if body.type == 'block':
            body = text(body)
        else:
            body = f'{{\n{(indent + 4) * " "}{text(body)}\n{indent * " "}}}'
        new_str += body
        while_str = f'while{text(condition_node)};'
        new_str += while_str
        if add_parent_bracket:
            new_str = f'{{{new_str}\n{(indent - 4)* " "}}}'
        return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]
