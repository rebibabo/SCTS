from utils import text
import re

index = ['i', 'j', 'k', 'l', 'm', 'n', '_', 'x', 'y', 'z', 't', 'u', 'v', 'w']
last_code = ''
last_identifiers = set()
identifiers = set()

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
        
def clear_identifier(code):
    global last_code, last_identifiers, identifiers
    if code != last_code:
        last_code = code
        last_identifiers = identifiers
        identifiers = set()

'''==========================匹配========================'''
def rec_ForIter(node):
    # for i in x:
    if node.type == 'for_statement' and node.children[3].type != 'call' \
        and len(node.children[3].children) > 0 and node.children[3].children[0].text != b'range':
        return True

def rec_ForRange(node):
    # for i in range(a, b):
    if node.type == 'identifier':
        identifiers.add(text(node))
    if node.type == 'for_statement':
        return True

def rec_ListComprehension(node):
    # x = [f(i) for i in x if condition]
    if node.type == 'assignment':
        if len(node.children) > 2 and node.children[2].type == 'list_comprehension' \
            and node.children[0].type == 'identifier':
            return True

def match_ForEnumerate(node):
    if node.type == 'for_statement':
        right = node.child_by_field_name('right')
        if right.type == 'call':
            function = text(right.child_by_field_name('function'))
            if function == 'enumerate':
                return True

def match_While(node):
    if node.type == 'while_statement':
        return True

'''==========================替换========================'''
def cvt_AddEnumerate(node):
    ret = [(node.children[0].end_byte + 1, 'idx, '), 
            (node.children[3].start_byte, 'enumerate('),
            (node.children[3].end_byte, ')')]
    if node.children[1].type not in ['pattern_list', 'tuple_pattern']:
        # for i in x -> for idx, i in enumerate(x)
        return ret
    else:
        if node.children[1].type == 'pattern_list':
            # for i, j in x -> for idx, (i, j) in enumerate(x)
            ret.append((node.children[1].start_byte, '('))
            ret.append((node.children[1].end_byte, ')'))
        # for (i, j) in x -> for idx, (i, j) in enumerate(x)
        return ret

def cvt_ForRange2While(node, code):
    # for a in x -> i = 0\nwhile i < len(x):\n    a = x[i]\n    i += 1
    clear_identifier(code)
    indent = get_indent(node.start_byte, code)
    iter = text(node.child_by_field_name('left'))
    container_node = node.child_by_field_name('right')
    container = text(container_node)
    body = node.child_by_field_name('body')
    new_iter = ''
    for each in index:
        if each not in last_identifiers:
            new_iter = each
            break
    ret = []
    ret.append((container_node.next_sibling.end_byte, node.start_byte))
    new_str = f'{new_iter} = 0\n{indent*" "}while {new_iter} < len({container}):\n{(indent+4)*" "}{iter} = {container}[{new_iter}]{(indent+4)*" "}'
    ret.append((node.start_byte, new_str))
    new_str = f'\n{(indent+4)*" "}{new_iter} += 1'
    ret.append((body.end_byte, new_str))
    last_identifiers.add(new_iter)
    return ret

def cvt_ListComprehension2For(node, code):
    # x = [str(i).replace(' ','') for i in x if i < 2 else '']
    #                   ->
    # temp_x = []
    # for i in x:
    #     if x < 2:
    #         temp_x.append(str(i).replace(' ',''))
    # x = temp_x
    indent = get_indent(node.start_byte, code)
    left_id = text(node.child_by_field_name('left'))
    right = node.child_by_field_name('right')
    body = text(right.child_by_field_name('body'))
    for_in_clause = right.children[2]
    container = text(for_in_clause.child_by_field_name('right'))
    if right.child_count == 4:
        # x = [f(i) for i in x]
        if left_id == container:
            temp_container = 'temp_' + container
            new_str = f'{temp_container} = []\n{indent*" "}{text(for_in_clause)}:\n{(indent+4)*" "}{temp_container}.append({body})\n{indent*" "}{left_id} = {temp_container}'
            return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]
        else:
            new_str = f'{left_id} = []\n{indent*" "}{text(for_in_clause)}:\n{(indent+4)*" "}{left_id}.append({body})'
            return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]
    elif right.child_count == 5:
        # x = [f(i) for i in x if condition]
        condition = text(right.children[3])
        if left_id == container:
            temp_container = 'temp_' + container
            new_str = f'{temp_container} = []\n{indent*" "}{text(for_in_clause)}:\n{(indent+4)*" "}{condition}:\n{(indent+8)*" "}{temp_container}.append({body})\n{indent*" "}{left_id} = {temp_container}'
            return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]
        else:
            new_str = f'{left_id} = []\n{indent*" "}{text(for_in_clause)}:\n{(indent+4)*" "}{condition}:\n{(indent+8)*" "}{left_id}.append({body})'
            return [(node.end_byte, node.start_byte), (node.start_byte, new_str)]