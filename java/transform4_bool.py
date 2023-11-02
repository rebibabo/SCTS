from utils import replace_from_blob, traverse_rec_func, text

'''==========================匹配========================'''
def rec_EqualBool(node):
    # true == a or a == true
    if node.type == 'binary_expression':
        if text(node.children[0]) in ['true', 'false'] or text(node.children[2]) in ['true', 'false']:
            if text(node.children[1]) == '==':
                return True

def rec_NotEqualBool(node):
    # true != a or a != true
    if node.type == 'binary_expression':
        if text(node.children[0]) in ['true', 'false'] or text(node.children[2]) in ['true', 'false']:
            if text(node.children[1]) == '!=':
                return True

def rec_Bool(node):
    # a == true or a != false
    if node.type == 'binary_expression':
        if text(node.children[0]) in ['true', 'false'] or text(node.children[2]) in ['true', 'false']:
            return True

'''==========================替换========================'''
def cvt_Equal2NotEqual(node):
    # a == true -> a != false
    ret = [(node.children[1].end_byte, node.children[1].start_byte),
           (node.children[1].start_byte, '!=')]
    if text(node.children[0]) in ['true', 'false']:
        index = 0
    else:
        index = 2
    ret.append((node.children[index].end_byte, node.children[index].start_byte))
    if text(node.children[index]) == 'true':
        ret.append((node.children[index].start_byte, 'false'))
    else:
        ret.append((node.children[index].start_byte, 'true'))
    return ret

def cvt_NotEqual2Equal(node):
    # a != true -> a == false
    ret = [(node.children[1].end_byte, node.children[1].start_byte),
           (node.children[1].start_byte, '==')]
    if text(node.children[0]) in ['true', 'false']:
        index = 0
    else:
        index = 2
    ret.append((node.children[index].end_byte, node.children[index].start_byte))
    if text(node.children[index]) == 'true':
        ret.append((node.children[index].start_byte, 'false'))
    else:
        ret.append((node.children[index].start_byte, 'true'))
    return ret

def cvt_Binary2Single(node):
    # a == false -> !a
    if text(node.children[0]) in ['true', 'false']:
        id = text(node.children[2])
        bool = text(node.children[0]) == 'true'
    else:
        id = text(node.children[0])
        bool = text(node.children[2]) == 'true'
    isNot = True
    if (bool and text(node.children[1]) == '==') or (not bool and text(node.children[1]) == '!='):
        isNot = False
    return [(node.end_byte, node.start_byte),
            (node.start_byte, f"{'!' if isNot else ''}{id}")]