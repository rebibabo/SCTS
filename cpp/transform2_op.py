from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

def get_parent_type(node: Node) -> List[str]:
    parents = []
    while node.parent:
        parents.append(node.parent.type)
        node = node.parent
    return parents

'''==========================匹配========================'''
def rec_AugmentedAssignment(node: Node) -> bool:
    # a ?= b
    if node.type == 'assignment_expression':
        if node.child_count >= 2 and text(node.children[1]) in ['+=', '-=', '*=', '/=', '%=', '<<=', '>>=']:
            return True

def rec_Assignment(node: Node) -> bool:
    # a = a ? b
    if node.type == 'assignment_expression':
        left_param = node.children[0].text
        if node.children[2].children:
            right_first_param = node.children[2].children[0].text
            if text(node.children[2].children[1]) in ['+', '-', '*', '/', '%', '<<', '>>']:
                return left_param == right_first_param

def rec_CmpRightConst(node: Node) -> bool:
    # a op const
    if node.type == 'binary_expression' \
            and text(node.children[1]) in ['<', '>', '<=', '>=', '==', '!='] \
            and node.children[2].type == 'number_literal':
        if 'binary_expression' not in get_parent_type(node):
            return True

def rec_CmpOptBigger(node: Node) -> bool:
    # a > b
    if node.type == 'binary_expression' \
            and text(node.children[1]) in ['>', '>=']:
        if 'binary_expression' not in get_parent_type(node):
            return True

def rec_CmpOptSmaller(node: Node) -> bool:
    # a <= b
    if node.type == 'binary_expression' \
            and text(node.children[1]) in ['<', '<=']:
        if 'binary_expression' not in get_parent_type(node):
            return True

def rec_Cmp(node: Node) -> bool:  # tx
    # a == b
    if node.type == 'binary_expression' \
            and text(node.children[1]) in ['>', '>=', '<', '<=', '==', '!=']:
        if 'binary_expression' not in get_parent_type(node):
            return True

def match_Equal(node: Node) -> bool:
    # a == b
    if node.type == 'binary_expression' \
            and text(node.children[1]) in ['==']:
        if 'binary_expression' not in get_parent_type(node):
            return True

def match_NotEqual(node: Node) -> bool:
    # a != b
    if node.type == 'binary_expression' \
            and text(node.children[1]) in ['!=']:
        if 'binary_expression' not in get_parent_type(node):
            return True

def match_LeftConst(node: Node) -> bool:
    # const op a
    if node.type == 'binary_expression' \
            and text(node.children[1]) in ['<', '>', '<=', '>=', '==', '!='] \
            and node.children[0].type == 'number_literal':
        if 'binary_expression' not in get_parent_type(node):
            return True

'''==========================替换========================'''
def cvt_AugmentedAssignment2Assignment(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a ?= b -> a = a ? b
    if rec_AugmentedAssignment(node):
        if len(node.children) == 3:
            [a, op, b] = [text(x) for x in node.children]
            new_str = f'{a} = {a} {op[:-1]} {b}'
            return [(node.end_byte, node.start_byte),
                    (node.start_byte, new_str)] 

def cvt_Assignment2AugmentedAssignment(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a = a ? b -> a ?= b
    a = text(node.children[0])
    op = text(node.children[2].children[1])
    if len(node.children[2].children) < 3:
        return 
    b = text(node.children[2].children[2])
    new_str = f'{a} {op}= {b}'
    return [(node.end_byte, node.start_byte),
            (node.start_byte, new_str)] 

def cvt_RightConst2LeftConst(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a op const -> const po a
    if len(node.children) == 3:
        [a, op, const] = [text(x) for x in node.children]
        reverse_op_dict = {'<':'>', '>=':'<=', '<=':'>=', '>':'<', '==':'==', '!=':'!='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{const} {reverse_op_dict[op]} {a}')]

def cvt_Bigger2Smaller(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a > b -> b < a
    if len(node.children) == 3:
        [a, op, b] = [text(x) for x in node.children]
        reverse_op_dict = {'>':'<', '>=':'<='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{b} {reverse_op_dict[op]} {a}')]

def cvt_Smaller2Bigger(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a <= b -> b >= a
    if len(node.children) == 3:
        [a, op, b] = [text(x) for x in node.children]
        reverse_op_dict = {'<':'>', '<=':'>='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{b} {reverse_op_dict[op]} {a}')]

def cvt_Equal(node: Node) -> List[Tuple[int, Union[int, str]]]:    # tx
    [a, op, b] = [text(x) for x in node.children]
    if op in ['==']: return
    if op in ['<=']:
        # a < b || a == b
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} < {b} || {a} == {b}')]
    if op in ['<']:
        # !(b < a || a == b)
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'!({b} < {a} || {a} == {b})')]
    if op in ['>=']:
        # a > b || a == b
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} > {b} || {a} == {b}')]
    if op in ['>']:
        # !(b > a || a == b)
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'!({b} > {a} || {a} == {b})')]
    if op in ['!=']:
        # !(a == b)
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'!({a} == {b})')]

def cvt_NotEqual(node: Node) -> List[Tuple[int, Union[int, str]]]:    # tx
    [a, op, b] = [text(x) for x in node.children]
    if op in ['!=']: return
    if op in ['<=']:
        # !(b < a && a != b)
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'!({b} < {a} && {a} != {b})')]
    if op in ['<']:
        # (a < b && a != b)
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} < {b} && {a} != {b}')]
    if op in ['>=']:
        # !(b > a && a != b)
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'!({b} > {a} && {a} != {b})')]
    if op in ['>']:
        # a < b && a != b
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} < {b} && {a} != {b}')]
    if op in ['==']:
        # a != b
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} != {b}')]