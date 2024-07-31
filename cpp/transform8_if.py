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

def dfs(u: Node) -> str:
    if len(u.children) != 3 or text(u.children[1]) != '&&':
        while len(u.children) >= 2 and text(u.children[0]) == '(':
            u = u.children[1]
        return text(u)
    l = [dfs(u.children[0]), dfs(u.children[2])]
    return ';'.join(l)

'''==========================匹配========================'''
def rec_IfMerge(node: Node) -> bool:  # tx
    # if ( a && b )
    if node.type != 'if_statement': return False
    expr_node = node.child_by_field_name('condition')
    expr_in_node = expr_node.children[1]
    while len(expr_in_node.children) >= 2 and text(expr_in_node.children[0]) == '(':
        expr_in_node = expr_in_node.children[1]
    if len(expr_in_node.children) < 3: return False
    if text(expr_in_node.children[1]) != '&&': return False
    return True

def rec_IfSplit(node: Node) -> bool:
    # if(a) if(b)
    if node.type != 'if_statement': return False
    consequence = node.child_by_field_name('consequence')
    if consequence.type != 'if_statement': return False
    return True

def rec_If(node: Node) -> bool:   # tx change
    # if(a==0) else if(a==1) else if(a==2)...
    if node.type != 'if_statement': return False
    if node.parent.type == 'if_statement': return False
    parent = node.parent
    while parent:   # if语句里面的if不变
        if parent.type in ['if_statement', 'else_clause']: 
            return False
        parent = parent.parent
    condition = node.child_by_field_name('condition')
    if condition.children[1].type != 'binary_expression': return False
    if text(condition.children[1].child_by_field_name('operator')) != '==': return False
    var = condition.children[1].child_by_field_name('left')
    if var.type != 'identifier': return False
    alternative = node.child_by_field_name('alternative')
    while alternative:  # 如果还有If语句
        if alternative.type == 'if_statement':
            condition = alternative.child_by_field_name('condition')
            if condition.children[0].type != 'binary_expression': return False
            var2 = condition.children[0].child_by_field_name('left')
            if var2.type != 'identifier': return False
            if text(var) != text(var2): return False
            alternative = alternative.child_by_field_name('alternative')
        else:
            break
    return True

def rec_Switch(node: Node) -> bool:    # tx
    if node.type == 'switch_statement':
        return True

'''==========================替换========================'''
def cvt_IfSplit(node: Node) -> List[Tuple[int, Union[int, str]]]:  # tx
    expr_node = node.child_by_field_name('condition')
    expr_in_node = expr_node.children[1]
    while len(expr_in_node.children) >= 1 and text(expr_in_node.children[0]) == '(':
        expr_in_node = expr_in_node.children[1]
    expr_list = dfs(expr_in_node).split(';')
    if_expr_list = []
    for expr in expr_list:
        if_expr_list.append(f'if({expr})')
    new_str = ' '.join(if_expr_list)
    return [(expr_node.end_byte, node.start_byte),
            (node.start_byte, new_str),]

def cvt_if2switch(node: Node, code: str) -> List[Tuple[int, Union[int, str]]]:  # tx change
    # if(a==b) else if (a==c) -> switch(a){case b: break; case c: break; default:}
    ori_node = node
    condition = node.child_by_field_name('condition')
    var = text(condition.children[1].child_by_field_name('left'))   # 变量
    indent = get_indent(node.start_byte, code)
    new_str = f"switch({var}){{\n"
    while node: # 如果还有else if
        condition = node.child_by_field_name('condition')
        value = text(condition.children[1].child_by_field_name('right'))
        new_str += f"{' '*(indent+4)}case {value}:\n"
        consequence = node.child_by_field_name('consequence')
        if consequence.type == 'compound_statement':
            compound_text = text(node.children[1])
            # 找到第一个'{'和最后一个'}'的位置
            l = compound_text.find('{')
            r = compound_text.rfind('}')
            compound_text = compound_text[l+1:r]
            new_str += '\n'.join([f"{' '*(indent+4)}{v}" for v in compound_text.split('\n')][1:])
        else:
            new_str += f"{' '*(indent+8)}{text(consequence)}\n"
        new_str += f"{' '*(indent+8)}break;\n"
        node = node.child_by_field_name('alternative')
        if node and node.type == 'else_clause':
            if node.children[1].type == 'if_statement': # 如果有else if，则循环
                node = node.children[1]
            else:   # else语句变成default
                new_str += f"{' '*(indent+4)}default:\n"
                if node.children[1].type == 'compound_statement':
                    compound_text = text(node.children[1])
                    # 找到第一个'{'和最后一个'}'的位置
                    l = compound_text.find('{')
                    r = compound_text.rfind('}')
                    compound_text = compound_text[l+1:r]
                    new_str += '\n'.join([f"{' '*(indent+4)}{v}" for v in compound_text.split('\n')][1:])
                else:
                    new_str += f"{' '*(indent+8)}{text(node.children[1])}\n"
                break
        else:
            break
    new_str += f"{' '*indent}}}\n{' '*indent}"
    return [(ori_node.end_byte, ori_node.start_byte),
            (ori_node.start_byte, new_str)]
                

def cvt_switch2if(node: Node, code: str) -> List[Tuple[int, Union[int, str]]]:  # tx
    var_str = text(node.children[1].children[1])
    compound_node = node.children[2]
    case_nodes = []
    for v in compound_node.children:
        if v.type == 'case_statement':
            case_nodes.append(v)
    if_strs = []
    indent = get_indent(node.start_byte, code)
    for i, case_node in enumerate(case_nodes):
        condition_str = text(case_node.children[1])
        if len(case_node.children) >= 4 and text(case_node.children[0]) == 'case':
            main_str = text(case_node.children[3])
        elif len(case_node.children) >= 3 and text(case_node.children[0]) == 'default':
            main_str = text(case_node.children[2])
        else:
            main_str = ''

        if i == 0:
            if_strs.append(f"if({var_str} == {condition_str}){{\n{' '*indent*2}{main_str}\n{' '*indent}}}")
        elif i == len(case_nodes) - 1:
            if_strs.append(f"{' '*indent}else{{\n{' '*indent*2}{main_str}\n{' '*indent}}}")
        else:
            if_strs.append(f"{' '*indent}else if({var_str} == {condition_str}){{\n{' '*indent*2}{main_str}\n{' '*indent}}}")
    
    return [(node.end_byte, node.start_byte),
            (node.start_byte, '\n'.join(if_strs))]