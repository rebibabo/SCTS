from utils import replace_from_blob, traverse_rec_func, text

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
def cvt_Merge2Split(node):
    # a, b = c, d -> a = c, b = d
    pattern_list = text(node.children[0]).replace(' ','').split(',')
    expression_list = text(node.children[2]).replace(' ','').split(',')
    if len(pattern_list) != len(expression_list):
        return
    indent = get_indent(node)
    ret = [(node.end_byte, node.start_byte - node.end_byte - 1)]
    for i in range(len(pattern_list)):
        ret.append((node.start_byte, f'{indent*" " if i else ""}{pattern_list[i]} = {expression_list[i]}\n'))
    return ret

def cvt_Merge2MergeSimple(node):
    # a, b = c, c -> a = b = c
    pattern_list = text(node.children[0]).replace(' ','').split(',')
    expression_list = text(node.children[2]).replace(' ','').split(',')
    if len(pattern_list) != len(expression_list):
        return
    indent = get_indent(node)
    str = f'{" = ".join(pattern_list + [expression_list[0]])}'
    return [(node.end_byte, node.start_byte - node.end_byte),
            (node.start_byte, str)]

def cvt_Split2Merge(node):
    # a = b\n c = d -> a, c = b, d,最多合并四个
    insert_index = 0
    merge_num = 0       # 记录要合并的个数
    pattern_list, expression_list, ret = [], [], []
    is_first = True
    for child in node.children:
        if child.type == 'expression_statement':
            temp_node = child.children[0]
            if temp_node.type == 'assignment':
                if is_first:
                    insert_index = temp_node.start_byte     # 第一个声明的位置
                    is_first = False
                pattern_str = text(temp_node.children[0])
                expression_str = text(temp_node.children[2])
                if rec_AssignmentMerge(temp_node):  # 如果是a, b = c, d型的
                    pattern_str_list = pattern_str.replace(' ','').split(',')
                    expression_str_list = expression_str.replace(' ','').split(',')
                    if len(pattern_str_list) != len(expression_str_list):
                        continue
                    for i in range(len(pattern_str_list)):
                        if pattern_str_list[i] not in pattern_list:     # pattern_list不能冲突
                            pattern_list.append(pattern_str_list[i])
                            expression_list.append(expression_str_list[i])
                            ret.append((temp_node.end_byte, temp_node.start_byte - temp_node.end_byte))     # 删除这个声明
                            merge_num += 1
                else:       # 如果是a = b
                    if pattern_str not in pattern_list:
                        pattern_list.append(pattern_str)
                        expression_list.append(expression_str)
                        ret.append((temp_node.end_byte, temp_node.start_byte - temp_node.end_byte))
                        merge_num += 1
                if merge_num > 3:
                    break
    merge_str = f"{', '.join(pattern_list)} = {', '.join(expression_list)}"
    ret.append((insert_index, merge_str))
    return ret
    