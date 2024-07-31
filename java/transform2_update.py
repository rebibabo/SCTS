from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

'''==========================匹配========================'''
def rec_LeftUpdate(node: Node) -> bool:
    # ++i or --i
    if node.type in ['update_expression']:
        if node.parent.type not in ['array_access', 'assignment_expression']:
            # 不是a[++i] 不是a=++i
            if node.children[1].type == 'identifier':
                return True

def rec_RightUpdate(node: Node) -> bool:
    # i++ or i--
    if node.type in ['update_expression']:
        if node.parent.type not in ['array_access', 'assignment_expression']:
            # 不是a[i++] 不是*p(i++)不是a=i++
            if node.children[0].type == 'identifier':
                return True

def rec_AugmentedCrement(node: Node) -> bool:
    # a += 1 or a -= 1
    if node.type == 'assignment_expression':
        if node.child_count >= 2 and text(node.children[1]) in ['+=', '-=']:
            if text(node.children[2]) == '1':
                return True

def rec_Assignment(node: Node) -> bool:
    # a = a ? 1
    if node.type == 'assignment_expression':
        left_param = node.children[0].text
        if node.children[2].children:
            right_first_param = node.children[2].children[0].text
            if len(node.children[2].children) > 2:
                if text(node.children[2].children[1]) in ['+', '-']:
                    if text(node.children[2].children[2]) == '1':
                        return left_param == right_first_param

def rec_ToLeft(node: Node) -> bool:
    return rec_RightUpdate(node) or rec_AugmentedCrement(node) or rec_Assignment(node)

def rec_ToRight(node: Node) -> bool:
    return rec_LeftUpdate(node) or rec_AugmentedCrement(node) or rec_Assignment(node)

def rec_ToAugment(node: Node) -> bool:
    return rec_LeftUpdate(node) or rec_RightUpdate(node) or rec_Assignment(node)

def rec_ToAssignment(node: Node) -> bool:
    return rec_LeftUpdate(node) or rec_RightUpdate(node) or rec_AugmentedCrement(node)

'''==========================替换========================'''
def cvt_ToRight(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # i++
    if rec_LeftUpdate(node):
        temp_node = node.children[0]
        return [(temp_node.end_byte, temp_node.start_byte), 
                (node.end_byte, text(temp_node))]
    if rec_AugmentedCrement(node):
        temp_node = node.children[0]
        op = text(node.children[1])[0]
        return [(node.end_byte, temp_node.end_byte),
                (temp_node.end_byte, op * 2)]
    if rec_Assignment(node):
        left_param = text(node.children[0])
        op = text(node.children[2].children[1])
        return [(node.end_byte, node.start_byte),
                (node.start_byte, f"{left_param}{op*2}")]

def cvt_ToLeft(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # ++i
    if rec_RightUpdate(node):
        temp_node = node.children[1]
        return [(temp_node.end_byte, temp_node.start_byte), 
                (node.start_byte, text(temp_node))]
    if rec_AugmentedCrement(node):
        temp_node = node.children[0]
        op = text(node.children[1])[0]
        return [(node.end_byte, temp_node.end_byte),
                (temp_node.start_byte, op * 2)]
    if rec_Assignment(node):
        left_param = text(node.children[0])
        op = text(node.children[2].children[1])
        return [(node.end_byte, node.start_byte),
                (node.start_byte, f"{op*2}{left_param}")]

def cvt_ToAugment(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # i += 1
    if rec_LeftUpdate(node):
        op = text(node.children[0])[0]
        param = text(node.children[1])
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f"{param} {op}= 1")]
    if rec_RightUpdate(node):
        op = text(node.children[1])[0]
        param = text(node.children[0])
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f"{param} {op}= 1")]
    if rec_Assignment(node):
        param = text(node.children[0])
        op = text(node.children[2].children[1])
        return [(node.end_byte, node.start_byte),
                (node.start_byte, f"{param} {op}= 1")]

def cvt_ToAssignment(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # i = i + 1
    if rec_LeftUpdate(node):
        op = text(node.children[0])[0]
        param = text(node.children[1])
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f"{param} = {param} {op} 1")]
    if rec_RightUpdate(node):
        op = text(node.children[1])[0]
        param = text(node.children[0])
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f"{param} = {param} {op} 1")]
    if rec_AugmentedCrement(node):
        param = text(node.children[0])
        op = text(node.children[1])[0]
        return [(node.end_byte, node.start_byte),
                (node.start_byte, f"{param} = {param} {op} 1")]
