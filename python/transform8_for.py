from utils import replace_from_blob, traverse_rec_func

'''==========================匹配========================'''
def rec_ForIter(node):
    # for i in x:
    if node.type == 'for_statement' and node.children[3].type != 'call' and node.children[3].children[0].text != b'range':
        return True

def rec_ForRange(node):
    # for i in range(a, b):
    if node.type == 'for_statement' and node.children[3].type == 'call' and node.children[3].children[0].text == b'range':
        return True

'''==========================替换========================'''
def cvt_AddEnumerate(node):
    if rec_ForIter(node):
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
    if rec_ForRange(node):
        iter = node.children[1].text.decode('utf-8')
        while_lines = node.parent.parent.text.decode('utf-8').split('\n')
        while_indent = len(while_lines[1]) - len(while_lines[1].lstrip())   # 计算for循环这一行的缩进
        range_str = node.children[3].children[1].text.decode('utf-8')
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
