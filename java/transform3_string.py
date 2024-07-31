from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

String_ids = set()

def get_id(node: Node) -> str:   # 遍历node，获取id
    id = []
    def traverse(node: Node):
        if node.type == 'identifier':
            id.append(text(node))
        for child in node.children:
            traverse(child)
    traverse(node)
    return id[0] if len(id) > 0 else ''

def get_id_type(root, id_type): # 遍历根节点，获取所有id的类型
    for u in root.children:
        if u.type in ['field_declaration', 'local_variable_declaration']:
            type = text(u.child_by_field_name('type'))
            if type != 'String':
                continue
            for v in u.children:
                if text(v) not in [',', ';'] and v.type != 'integral_type':
                    String_ids.add(get_id(v))
        get_id_type(u, id_type)

'''==========================匹配========================'''
def rec_String(node: Node) -> bool:
    # "string"
    if node.type == 'string_literal' and not rec_NewString(node.parent.parent):
        return True

def rec_NewString(node: Node) -> bool:
    # new String("string")
    if node.type == 'object_creation_expression':
        if node.children[0].text== b'new' and node.children[1].text == b'String':
            arguments = node.child_by_field_name('arguments')
            if arguments and arguments.children[1].type == 'string_literal':
                return True

def rec_StringConcat(node: Node) -> bool:
    # a.concat(b).concat(c)
    if node.type == 'method_invocation' and node.parent.type != 'method_invocation':
        if node.child_count > 2 and node.children[2].text == b'concat':
            return True

def match_StringAdd(node: Node) -> bool:
    global String_ids
    if not node.parent:
        String_ids.clear()
        get_id_type(node, String_ids)
    if node.type == 'binary_expression':
        while node:
            if node.type != 'binary_expression': break
            left = node.child_by_field_name('left')
            right = node.child_by_field_name('right')
            if text(right) not in String_ids:   return False
            if node.children[1] != '+':         return False
            node = left
        return True

'''==========================替换========================'''
def cvt_ToNewString(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # "string" -> new String("string")
    return [(node.start_byte, 'new String('), (node.end_byte, ')')]

def cvt_ToString(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # new String("string") -> "string"
    return [(node.children[2].children[1].start_byte, node.start_byte),
            (node.children[2].children[2].end_byte, node.children[2].children[1].end_byte)]

def cvt_Concat2Add(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a.concat(b).concat(c) -> a + b + c
    string_list = []
    temp_node = node
    while temp_node.type == 'method_invocation' and text(temp_node.child_by_field_name('name')) == 'concat':
        id = text(temp_node.child_by_field_name('object'))
        string_list.append(id)
        arguments = temp_node.child_by_field_name('arguments')
        temp_node = arguments.children[1]
    string_list.append(text(temp_node))
    return [(node.end_byte, node.start_byte),
            (node.start_byte, ' + '.join(string_list))]