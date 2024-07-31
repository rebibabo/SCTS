from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

'''==========================匹配========================'''
def rec_IndexOf(node: Node) -> bool:
    # a.indexOf(i)
    if node.type == 'method_invocation' and node.child_by_field_name('object'):
        identifier = node.child_by_field_name('name')
        args = node.child_by_field_name('arguments')
        if text(identifier) == 'indexOf' and args and len(args.children) == 3:
            return True

def rec_IndexOfStart(node: Node) -> bool:
    # a.indexOf(i, 0)
    if node.type == 'method_invocation' and node.child_by_field_name('object'):
        identifier = node.child_by_field_name('name')
        args = node.child_by_field_name('arguments')
        if text(identifier) == 'indexOf' and args and len(args.children) == 5:
            if args.children[3].type == 'decimal_integer_literal' and text(args.children[3]) == '0':
                return True

def rec_IsEmpty(node: Node) -> bool:
    # a.isEmpty()
    if node.type == 'method_invocation' and node.child_by_field_name('object'):
        identifier = node.child_by_field_name('name')
        if text(identifier) == 'isEmpty':
            return True

def rec_SizeEqZero(node: Node) -> bool:
    # a.size() == 0
    if node.type == 'binary_expression':
        if node.child_by_field_name('operator').type == '==':
            left_node = node.child_by_field_name('left')
            right_node = node.child_by_field_name('right')
            if left_node.type == 'method_invocation' and right_node.type == 'decimal_integer_literal':
                left_identifier = left_node.child_by_field_name('name')
                if left_node.child_by_field_name('object') and text(left_identifier) == 'size' and text(right_node) == '0':
                    return True

'''==========================替换========================'''
def cvt_AddZero(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a.indexOf(i) -> a.indexOf(i, 0)
    args = node.child_by_field_name('arguments').children[1]
    return [(args.end_byte, ', 0')]

def cvt_DelZero(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a.indexOf(i, 0) -> a.indexOf(i)
    last_args = node.child_by_field_name('arguments').children[-2]
    return [(last_args.end_byte, last_args.prev_sibling.start_byte)]

def cvt_SizeEqZero2IsEmpty(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a.size() == 0 => a.isEmpty()
    obj = text(node.child_by_field_name('left').child_by_field_name('object'))
    return [(node.end_byte, node.start_byte),
            (node.start_byte, f"{obj}.isEmpty()")]

def cvt_IsEmpty2SizeEqZero(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a.isEmpty() -> a.size() == 0
    obj = text(node.child_by_field_name('object'))
    return [(node.end_byte, node.start_byte),
            (node.start_byte, f"({obj}.size() == 0)")]