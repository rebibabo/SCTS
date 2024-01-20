from utils import text

def get_indent(start_byte, code):
    indent = 0
    i = start_byte
    while i >= 0 and code[i] != '\n':
        if code[i] == ' ':
            indent += 1
        elif code[i] == '\t':
            indent += 4
        i -= 1
    return indent
    
'''==========================匹配========================'''
def rec_AssignmentMerge(node):
    # a, b = c, d
    if node.type == 'assignment':
        left = node.children[0]
        right = node.children[2]
        if left.type == 'pattern_list' and right.type == 'expression_list':
            return True

def rec_AssignmentMergeSame(node):
    # a, b = 0, 0
    if node.type == 'assignment':
        left = node.children[0]
        right = node.children[2]
        if left.type == 'pattern_list' and right.type == 'expression_list':
            ele = right.children[0].text
            for each in right.children:
                if each.text == b',':
                    continue
                if each.text != ele:
                    return
            return True

def rec_MultiAssignment(node):
    # a = 0\n  c = [] ... 
    num = 0
    for child in node.children:
        if child.type == 'expression_statement':
            temp_node = child.children[0]
            if temp_node.type == 'assignment':
                num += 1
    return num > 1

'''==========================替换========================'''
def cvt_Merge2Split(node, code):
    # a, b = c, d -> a = c, b = d
    pattern_list = text(node.children[0]).replace(' ','').split(',')
    expression_list = text(node.children[2]).replace(' ','').split(',')
    if len(pattern_list) != len(expression_list):
        return
    indent = get_indent(node.start_byte, code)
    new_str = ''
    for i in range(len(pattern_list)):
        start = '\n' + indent*' ' if i != 0 else ''
        new_str += f'{start}{pattern_list[i]} = {expression_list[i]}'
    return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]

def cvt_Merge2MergeSimple(node, code):
    # a, b = c, c -> a = b = c
    pattern_list = text(node.children[0]).replace(' ','').split(',')
    expression_list = text(node.children[2]).replace(' ','').split(',')
    if len(pattern_list) != len(expression_list):
        return
    indent = get_indent(node, code)
    str = f'{" = ".join(pattern_list + [expression_list[0]])}'
    return [(node.end_byte, node.start_byte),
            (node.start_byte, str)]