from utils import replace_from_blob, traverse_rec_func, text
import re

def get_indent(node):
    # 计算node节点处的缩进
    indent = 0
    if node.parent.parent.type == 'block':
        block_text = text(node.parent.parent.parent)
        lines = block_text.split('\n')
        if len(lines) > 1:
            return len(lines[1]) - len(lines[1].strip())
    return 0
        
'''==========================匹配========================'''
def rec_ForIter(node):
    # for i in x:
    if node.type == 'for_statement' and node.children[3].type != 'call' \
        and len(node.children[3].children) > 0 and node.children[3].children[0].text != b'range':
        return True

def rec_ForRange(node):
    # for i in range(a, b):
    if node.type == 'for_statement' and node.children[3].type == 'call' \
        and len(node.children[3].children) > 0 and node.children[3].children[0].text == b'range':
        return True

def rec_ListComprehension(node):
    # x = [f(i) for i in x if condition]
    if node.type == 'assignment':
        if len(node.children) > 2 and node.children[2].type == 'list_comprehension' \
            and node.children[0].type == 'identifier':
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

def cvt_ForRange2While(node):
    # for i in range() -> while
    iter = text(node.children[1])
    while_lines = text(node.parent.parent).split('\n')
    while_indent = len(while_lines[1]) - len(while_lines[1].lstrip())   # 计算for循环这一行的缩进
    range_str = text(node.children[3].children[1])
    range_list = range_str[1: -1].split(',')
    left, right, incre = 0, 0, '1'
    if len(range_list) == 1:
        # range(C)
        right = range_list[0]
    elif len(range_list) == 2:
        # range(left, right)
        [left, right] = range_list[:2]
    elif len(range_list) == 3:
        # range(left, right, incre)
        [left, right, incre] = range_list
    else:
        return
    cmp = '>' if incre.isdigit() and int(incre) < 0 else '<'
    sign = '-' if incre.isdigit() and int(incre) < 0 else '+'
    incre = abs(int(incre)) if incre.isdigit() else incre
    return [(node.children[4].end_byte, node.start_byte - node.children[4].end_byte),
            (node.start_byte, f'{iter} = {left}\n'),
            (node.start_byte, f"{while_indent*' '}while {iter} {cmp} {right}:"),
            (node.end_byte + 1, f"\n{(while_indent+4)*' '}{iter} {sign}= {incre}\n")]

def cvt_ListComprehension2For(node):
    # x = [str(i).replace(' ','') for i in x if i < 2]
    #                   ->
    # temp_x = []
    # for i in range(len(b)):
    #     if b[i] < 2:
    #         temp_x[i] = str(b[i]).replace(' ','')
    # x = temp_x
    indent = get_indent(node)
    left_id = text(node.children[0])
    temp_node = node.children[2]
    ret = [(node.end_byte, node.start_byte - node.end_byte)]
    if temp_node.child_count == 5:
        func_, for_, if_ = temp_node.children[1:4]
        if for_.child_count < 4:
            return
        iter_name = text(for_.children[1])
        list_name = text(for_.children[3])
        if left_id == list_name:
            left_id = 'temp_' + left_id
            ret.append((node.end_byte, f'{indent*" "}{left_id[5:]} = {left_id}'))
        ret.append((node.start_byte, f"{left_id} = []\n"))
        for_text = text(for_)
        if_text = text(if_)
        func_text = text(func_)
        if 'range' not in text(for_):
            pattern = re.compile(r'(?<!\w)'+iter_name+'(?!\w)')
            try:
                if_text = pattern.sub(f'{list_name}[{iter_name}]', if_text)
                func_text = pattern.sub(f'{list_name}[{iter_name}]', func_text)
            except:
                return
            ret.append((node.start_byte, f"{indent*' '}for {iter_name} in range(len({list_name})):\n"))
            ret.append((node.start_byte, f"{(indent+4)*' '}{if_text}:\n"))
            ret.append((node.start_byte, f"{(indent+8)*' '}{left_id}[{iter_name}] = {func_text}\n"))
        else:
            ret.append((node.start_byte, f"{indent*' '}{for_text}:\n"))
            ret.append((node.start_byte, f"{(indent+4)*' '}{if_text}:\n"))
            ret.append((node.start_byte, f"{(indent+8)*' '}{left_id}[{iter_name}] = {func_text}\n"))
    elif temp_node.child_count == 4:
        func_, for_ = temp_node.children[1:3]
        iter_name = text(for_.children[1])
        list_name = text(for_.children[3])
        if left_id == list_name:
            left_id = 'temp_' + left_id
            ret.append((node.end_byte, f'{indent*" "}{left_id[5:]} = {left_id}'))
        ret.append((node.start_byte, f"{left_id} = []\n"))
        for_text = text(for_)
        func_text = text(func_)
        if 'range' not in for_text:
            pattern = re.compile(r'(?<!\w)'+iter_name+'(?!\w)')
            try:
                func_text = pattern.sub(f'{list_name}[{iter_name}]', func_text)
            except:
                return
            ret.append((node.start_byte, f"{indent*' '}for {iter_name} in range(len({list_name})):\n"))
            ret.append((node.start_byte, f"{(indent+4)*' '}{left_id}[{iter_name}] = {func_text}\n"))
        else:
            ret.append((node.start_byte, f"{indent*' '}{for_text}:\n"))
            ret.append((node.start_byte, f"{(indent+4)*' '}{left_id}[{iter_name}] = {func_text}\n"))
    return ret
