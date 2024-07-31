from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

'''==========================匹配========================'''
def rec_InitCallList(node: Node) -> bool:
    # 是否是list()
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'list':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 2:
                return True

def rec_InitList(node: Node) -> bool:
    # 是否是[]
    if node.type == 'list' and len(node.children) == 2:
        return True

def rec_CallList(node: Node) -> bool:
    # 是否是list([...])
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'list':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 3 and args.children[1].type == 'list':
                return True

def rec_List(node: Node) -> bool:
    # 是否是[...], 且不是list([...])  
    # node:[...] node.parent:([...]) node.parent.parent:list([...]) node.parent.parent:children[0]:list
    if node.type == 'list' and node.parent.parent.children[0].text != b'list':  
        return True

'''==========================替换========================'''
def cvt_InitList2InitCallList(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # [] -> list()
    # 删除[]                      加上list()
    return [(node.end_byte, node.start_byte), (node.start_byte, 'list()')]
        
def cvt_InitCallList2InitList(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # list() -> []
    return [(node.end_byte, node.start_byte), (node.start_byte, '[]')]

def cvt_List2CallList(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # [...] -> list([...])
    return [(node.start_byte, 'list('), (node.end_byte, ')')]

def cvt_CallList2List(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # list([...]) -> [...]
    args = node.child_by_field_name('arguments')
    return [(args.children[1].start_byte, node.start_byte),   # 删除list( 
            (args.children[2].end_byte, -1)]            # 删除)
