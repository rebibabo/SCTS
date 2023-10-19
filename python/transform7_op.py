from utils import replace_from_blob, traverse_rec_func

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

def rec_TestBool(node):
    input(node.text)
    input(node.type)

'''==========================替换========================'''
def cvt_AugmentedAssignment2Assignment(node):
    # a ?= b -> a = a ? b
    if rec_AugmentedAssignment(node):
        [a, op, b] = [x.text.decode('utf-8') for x in node.children]
        new_str = f'{a} = {a} {op[:-1]} {b}'
        return [(node.end_byte, -len(node.text.decode('utf-8'))),
                (node.start_byte, new_str)] 

def cvt_Assignment2AugmentedAssignment(node):
    # a = a ? b -> a ?= b
    if rec_Assignment(node):
        a = node.children[0].text.decode('utf-8')
        op = node.children[2].children[1].text.decode('utf-8')
        if len(node.children[2].children) < 3:
            return 
        b = node.children[2].children[2].text.decode('utf-8')
        new_str = f'{a} {op}= {b}'
        return [(node.end_byte, -len(node.text.decode('utf-8'))),
                (node.start_byte, new_str)] 
