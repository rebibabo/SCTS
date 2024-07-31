from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

def get_indent(start_byte: int, code: str) -> int:
    indent = 0
    i = start_byte
    while i >= 0 and code[i] != '\n':
        if code[i] == ' ':
            indent += 1
        elif code[i] == '\t':
            indent += 4
        i -= 1
    return indent
    
'''==========================匹配========================'''
def rec_BracketSameLine(node: Node) -> bool:
    # statement {
    if node.text == b'{':
        if node.parent.type == 'compound_statement':
            # {的行号                   上一句的行号
            if node.start_point[0] == node.parent.prev_sibling.end_point[0]:
                return True

def rec_BracketNextLine(node: Node) -> bool:
    # statement 
    #{
    if node.text == b'{':
        if node.parent.type == 'compound_statement':
            if node.start_point[0] == node.parent.prev_sibling.end_point[0] + 1:
                return True

def rec_OperatorOrSpliter(node: Node, code) -> bool:
    # + - * / ... , ; 没有间隔
    if text(node) in ['+', '-', '*', '/', '%', '=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '+=', '-=', '*=', '/=', '%=', '&', '|', '<<', '>>', '<<=', '>>=', ',',  '&', ':', ';', 'if', 'for', 'while', 'do']:
        return True

def rec_IfForWhileNoBracket(node: Node) -> bool:
    #for(); while(); if();
    if node.type in ['while_statement', 'if_statement', 'for_statement', 'else_clause']:
        for child in node.children:
            if child.type == 'compound_statement':
                return False
        return True
            
def rec_IfForWhileHasBracket(node: Node, code) -> bool: # tx
    # 单个语句的if/for/while且有花括号
    if node.type in ['while_statement', 'if_statement', 'for_statement', 'else_clause']:
        statement_node = None
        for u in node.children:
            if u.type == 'compound_statement':
                statement_node = u
                break
        if statement_node is None:
            return
        if statement_node.child_count == 3: 
            return True

'''==========================替换========================'''
def cvt_BracketSame2NextLine(node: Node, code: str) -> List[Tuple[int, Union[int, str]]]:
    # 大括号写到下一行
    indent = get_indent(node.parent.start_byte, code)
    return [(node.start_byte, '\n' + ' '*(indent))]

def cvt_BracketNext2SameLine(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # 大括号写到同一行
    insert_idx = node.parent.prev_sibling.end_byte
    if node.parent.prev_sibling.type == 'comment':  # 如果前面是注释，就在注释前面添加括号
        insert_idx = node.parent.prev_sibling.start_byte
    return [(node.start_byte, insert_idx)]

def cvt_AddBlankSpace(node: Node, code: str) -> List[Tuple[int, Union[int, str]]]:
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

def cvt_AddIfForWhileBracket(node: Node, code: str) -> List[Tuple[int, Union[int, str]]]:
    indent = get_indent(node.start_byte, code)
    ret = []
    if node.type == 'if_statement':
        consequence_node = node.child_by_field_name('consequence')
        if consequence_node: 
            if consequence_node.start_point[0] == node.start_point[0]:    # 如果在同一行
                ret.append((consequence_node.start_byte, '{\n' + ' '*(indent + 4)))
                ret.append((consequence_node.end_byte, '\n' + ' '*indent + '}'))
            else:
                insert_idx = consequence_node.prev_sibling.end_byte
                if consequence_node.prev_sibling.type == 'comment':  # 如果前面是注释，就在注释前面添加括号
                    insert_idx = consequence_node.prev_sibling.start_byte
                ret.append((insert_idx, '{'))
                ret.append((consequence_node.end_byte, '\n' + ' '*indent + '}'))
            alternative = node.child_by_field_name('alternative')
            if alternative:
                else_node = alternative.children[1]
                if else_node and else_node.type != 'if_statement' and 'statement' in else_node.type:  # else语句
                    ret.extend(cvt_AddIfForWhileBracket(alternative, code))
    else:   # for, while, else
        for child in node.children:
            if 'statement' in child.type:
                statement_node = child
                break
        if statement_node:
            if statement_node.start_point[0] == node.start_point[0]:    # 如果在同一行
                ret.append((statement_node.start_byte, '{\n' + ' '*(indent + 4)))
                ret.append((statement_node.end_byte, '\n' + ' '*indent + '}'))
            else:
                insert_idx = statement_node.prev_sibling.end_byte
                if statement_node.prev_sibling.type == 'comment':  # 如果前面是注释，就在注释前面添加括号
                    insert_idx = statement_node.prev_sibling.start_byte
                ret.append((insert_idx, '{'))
                ret.append((statement_node.end_byte, '\n' + ' '*indent + '}'))
    return ret

def cvt_DelIfForWhileBracket(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # { statement } -> statement
    statement_node = None
    for u in node.children:
        if u.type == 'compound_statement':
            statement_node = u
    return [(statement_node.children[0].end_byte, statement_node.children[0].start_byte),
            (statement_node.children[2].end_byte, statement_node.children[2].start_byte)]