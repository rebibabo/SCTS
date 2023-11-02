from utils import replace_from_blob, traverse_rec_func, text

'''==========================匹配========================'''
def rec_String(node):
    # "string"
    if node.type == 'string_literal' and not rec_NewString(node.parent.parent):
        return True

def rec_NewString(node):
    # new String("string")
    if node.type == 'object_creation_expression':
        if node.children[0].text== b'new' and node.children[1].text == b'String':
            return True

def rec_StringConcat(node):
    # a.concat(b).concat(c)
    if node.type == 'method_invocation' and node.parent.type != 'method_invocation':
        if node.child_count > 2 and node.children[2].text == b'concat':
            return True

'''==========================替换========================'''
def cvt_ToNewString(node):
    # "string" -> new String("string")
    return [(node.start_byte, 'new String('), (node.end_byte, ')')]

def cvt_ToString(node):
    # new String("string") -> "string"
    return [(node.children[2].children[1].start_byte, node.start_byte),
            (node.children[2].children[2].end_byte, node.children[2].children[1].end_byte)]

def cvt_Concat2Add(node):
    # a.concat(b).concat(c) -> a + b + c
    string_list = []
    temp_node = node
    while temp_node.type == 'method_invocation':
        string_list.insert(0, text(temp_node.children[3].children[1]))
        temp_node = temp_node.children[0]
    string_list.insert(0, text(node.parent.children[0]))
    return [(node.end_byte, node.start_byte),
            (node.start_byte, ' + '.join(string_list))]