from utils import replace_from_blob, traverse_rec_func, text

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
    
'''==========================匹配========================'''
def rec_BracketSameLine(node):
    # statement {
    if node.text == b'{':
        if node.parent.type == 'compound_statement':
            # {的行号                   上一句的行号
            if node.start_point[0] == node.parent.prev_sibling.end_point[0]:
                return True

def rec_BracketNextLine(node):
    # statement 
    #{
    if node.text == b'{':
        if node.parent.type == 'compound_statement':
            if node.start_point[0] == node.parent.prev_sibling.end_point[0] + 1:
                return True

def rec_OperatorOrSpliter(node, code):
    # + - * / ... , ; 没有间隔
    if text(node) in ['+', '-', '*', '/', '%', '=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '+=', '-=', '*=', '/=', '%=', '&', '|', '<<', '>>', '<<=', '>>=', ',',  '&', ':', ';', 'if', 'for', 'while', 'do']:
        return True

def rec_IfForWhileNoBracket(node):
    #for(); while(); if();
    # input((node.type, node.text))
    if node.type in ['while_statement', 'if_statement', 'for_statement', 'else_clause']:
        if '{' not in text(node):
            return True
            
'''==========================替换========================'''
def cvt_BracketSame2NextLine(node, code):
    # 大括号写到下一行
    indent = get_indent(node.parent.start_byte, code)
    return [(node.start_byte, '\n' + ' '*(indent))]

def cvt_BracketNext2SameLine(node):
    # 大括号写到同一行
    return [(node.start_byte, node.parent.prev_sibling.end_byte - node.start_byte)]

def cvt_AddBlankSpace(node, code):
    # 添加空格
    node_text = text(node)
    ret = []
    if node_text in [',', ';', 'if', 'for', 'while', 'do']:
        if node.end_byte < len(code) and code[node.end_byte] != ' ':
            ret.append((node.end_byte, ' '))
    elif node_text in ['*', '&']:
        if node.parent.type == 'binary_expression':
            if node.end_byte < len(code) and code[node.end_byte] != ' ':
                ret.append((node.end_byte, ' '))
            if node.start_byte - 1 < len(code) and code[node.start_byte - 1] != ' ':
                ret.append((node.start_byte, ' '))
    else:
        if node.end_byte < len(code) and code[node.end_byte] != ' ':
            ret.append((node.end_byte, ' '))
        if node.start_byte - 1 < len(code) and code[node.start_byte - 1] != ' ':
            ret.append((node.start_byte, ' '))
    return ret

def cvt_AddIfForWhileBracket(node, code):
    # 在单行If、For、While添加大括号
    statement_node = None
    for each in node.children:
        if each.type in ['expression_statement', 'return_statement', 'compound_statement', 'break_statement']:
            statement_node = each
    if statement_node is None:
        return
    indent = get_indent(node.start_byte, code)
    
    if '\n' not in text(node):
        return [(statement_node.start_byte, statement_node.prev_sibling.end_byte - statement_node.start_byte),
                (statement_node.start_byte, f" {{\n{(indent + 4) * ' '}"), 
                (statement_node.end_byte, f"\n{indent * ' '}}}")]
    else:
        return [(statement_node.prev_sibling.end_byte, f" {{"), 
                (statement_node.end_byte, f"\n{indent * ' '}}}")]