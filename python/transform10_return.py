from utils import replace_from_blob, traverse_rec_func, text

'''==========================匹配========================'''
def rec_MultiReturnNotTuple(node):
    # return a, b, ...
    if node.type == 'return_statement' and len(node.children) > 1 and node.children[1].type == 'expression_list':
        return True

def rec_MultiReturnWithTuple(node):
    # return (a, b, ...)
    if node.type == 'return_statement' and len(node.children) > 1 and node.children[1].type == 'tuple':
        return True

def rec_MultiReturnWithoutNone(node):
    # return
    if node.type == 'return_statement' and len(node.children) == 1:
        return True

def rec_MultiReturnWithNone(node):
    # return None
    if node.type == 'return_statement' and len(node.children) == 2 and node.children[1].type == 'none':
        return True

'''==========================替换========================'''
def cvt_ReturnTuple(node):
    # return a, b -> return (a, b)
    statement_node = node.children[1]
    return [(statement_node.start_byte, '('), (statement_node.end_byte, ')')]

def cvt_ReturnWithoutTuple(node):
    # return (a, b) -> a, b
    statement_node = node.children[1]
    return [(statement_node.start_byte + 1, -1), (statement_node.end_byte, -1)]

def cvt_AddNone(node):
    # return -> return None
    return [(node.end_byte, ' None')]

def cvt_DelNone(node):
    # return None -> return
    return [(node.children[1].end_byte, node.children[0].end_byte - node.children[1].end_byte)]