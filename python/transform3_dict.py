from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

'''==========================匹配========================'''
def rec_InitCallDict(node: Node) -> bool:
    # 是否是dict()
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'dict':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 2:
                return True

def rec_InitDict(node: Node) -> bool:
    # 是否是{}
    if node.type == 'dictionary' and len(node.children) == 2:
        return True

def rec_CallDict(node: Node) -> bool:
    # 是否是dict({...})
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'dict':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 3 and args.children[1].type == 'dictionary':
                return True

def rec_Dict(node: Node) -> bool:
    # 是否是{...}, 且不是dict({...})  
    # node:{...} node.parent:({...}) node.parent.parent:dict({...}) node.parent.parent:children[0]:dict
    if node.type == 'dictionary' and node.parent.parent.children[0].text != b'dict':  
        return True
        
'''==========================替换========================'''
def cvt_InitDict2InitCallDict(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # {} -> dict()
    # 删除{}                      加上dict()
    return [(node.end_byte, node.start_byte), (node.start_byte, 'dict()')]
    
def cvt_InitCallDict2InitDict(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # dict() -> {}
    return [(node.end_byte, node.start_byte), (node.start_byte, '{}')]

def cvt_Dict2CallDict(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # {...} -> dict({...})
    return [(node.start_byte, 'dict('), (node.end_byte, ')')]

def cvt_CallDict2Dict(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # dict({...}) -> {...}
    args = node.child_by_field_name('arguments')
    return [(args.children[1].start_byte, node.start_byte),   # 删除dict( 
            (args.children[2].end_byte, -1)]
