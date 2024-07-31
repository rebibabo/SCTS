from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

'''==========================匹配========================'''
def rec_EqualBool(node: Node) -> bool:
    # true == a or a == true
    if node.type == 'binary_expression':
        if text(node.children[0]) in ['true', 'false'] or text(node.children[2]) in ['true', 'false']:
            if text(node.children[1]) == '==':
                return True

def rec_NotEqualBool(node: Node) -> bool:
    # true != a or a != true
    if node.type == 'binary_expression':
        if text(node.children[0]) in ['true', 'false'] or text(node.children[2]) in ['true', 'false']:
            if text(node.children[1]) == '!=':
                return True

def rec_Bool(node: Node) -> bool:
    # a == true or a != false
    if node.type == 'binary_expression':
        if text(node.children[0]) in ['true', 'false'] or text(node.children[2]) in ['true', 'false']:
            return True

def match_Bool(node: Node) -> bool:
    # !a
    if node.type == 'unary_expression':
        return True

'''==========================替换========================'''
def cvt_Equal2NotEqual(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a == true -> a != false
    left = text(node.child_by_field_name('left'))
    right = text(node.child_by_field_name('right'))
    if left in ['true', 'false']:
        right = 'false' if left == 'true' else 'true'
        left = right
    elif right in ['true', 'false']:
        right = 'false' if right == 'true' else 'true'
    new_str = f'{left} != {right}'
    return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]

def cvt_NotEqual2Equal(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a != true -> a == false
    left = text(node.child_by_field_name('left'))
    right = text(node.child_by_field_name('right'))
    if left in ['true', 'false']:
        right = 'false' if left == 'true' else 'true'
        left = right
    elif right in ['true', 'false']:
        right = 'false' if right == 'true' else 'true'
    new_str = f'{left} == {right}'
    return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]

def cvt_Binary2Single(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a == false -> !a
    left = text(node.child_by_field_name('left'))
    right = text(node.child_by_field_name('right'))
    if left in ['true', 'false']:
        right = 'false' if left == 'true' else 'true'
        left = right
    elif right in ['true', 'false']:
        right = 'false' if right == 'true' else 'true'
    new_str = f'!{left}'
    return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]