from utils import replace_from_blob, traverse_rec_func, text

'''==========================匹配========================'''
def rec_AugmentedAssignment(node):
    # a ?= b
    if node.type == 'augmented_assignment':
        return True

def rec_Assignment(node):
    # a = a ? b
    if node.type == 'assignment':
        left_param = node.children[0].text
        if node.children[2].children:
            right_first_param = node.children[2].children[0].text
            return left_param == right_first_param

def rec_CmpRightConst(node):
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) in ['<', '>', '<=', '>=', '==', '!='] \
            and node.children[2].type in ['integer', 'string', 'list', 'set', 'dictionary', 'float', 'tuple']:
        return True

def rec_CmpOptBigger(node):
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) in ['>', '>=']:
        return True

def rec_CmpOptSmaller(node):
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) in ['<', '<=']:
        return True

'''==========================替换========================'''
def cvt_AugmentedAssignment2Assignment(node):
    # a ?= b -> a = a ? b
    if rec_AugmentedAssignment(node):
        if len(node.children) == 3:
            [a, op, b] = [text(x) for x in node.children]
            new_str = f'{a} = {a} {op[:-1]} {b}'
            return [(node.end_byte, -len(text(node))),
                    (node.start_byte, new_str)] 

def cvt_Assignment2AugmentedAssignment(node):
    # a = a ? b -> a ?= b
    a = text(node.children[0])
    op = text(node.children[2].children[1])
    if len(node.children[2].children) < 3:
        return 
    b = text(node.children[2].children[2])
    new_str = f'{a} {op}= {b}'
    return [(node.end_byte, -len(text(node))),
            (node.start_byte, new_str)] 

def cvt_RightConst2LeftConst(node):
    # a op const -> const po a
    if len(node.children) == 3:
        [a, op, const] = [text(x) for x in node.children]
        reverse_op_dict = {'<':'>', '>=':'<=', '<=':'>=', '>':'<', '==':'==', '!=':'!='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{const} {reverse_op_dict[op]} {a}')]

def cvt_Bigger2Smaller(node):
    # a > b -> b < a
    if len(node.children) == 3:
        [a, op, b] = [text(x) for x in node.children]
        reverse_op_dict = {'>':'<', '>=':'<='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{b} {reverse_op_dict[op]} {a}')]

def cvt_Smaller2Bigger(node):
    # a <= b -> b >= a
    if len(node.children) == 3:
        [a, op, b] = [text(x) for x in node.children]
        reverse_op_dict = {'<':'>', '<=':'>='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{b} {reverse_op_dict[op]} {a}')]
