from utils import replace_from_blob, traverse_rec_func, text

'''==========================匹配========================'''
def rec_string(node):
    if node.type == 'string':
        return True

def rec_not_format_string(node):
    if node.type == 'string':
        if text(node)[0] != 'f' and len(node.parent.children) > 2 and node.parent.children[2].text != b'format':
            return True

def rec_format_string_left(node):
    if node.type == 'string':
        if text(node)[0] == 'f':
            return True

def rec_format_string_right(node):
    if node.type == 'string':
        if len(node.parent.children) > 2 and node.parent.children[2].text == b'format':
            return True
        
'''==========================替换========================'''
def cvt_single_quotation(node):
    # ''
    str = text(node).strip()
    new_str = str[1: -1].replace("'", '"')
    new_str = f"'{new_str}'"
    return [(node.end_byte, -len(str)), (node.start_byte, new_str)]

def cvt_double_quotation(node):
    # ""
    str = text(node).strip()
    new_str = str[1: -1].replace('"', "'")
    new_str = f'"{new_str}"'
    return [(node.end_byte, -len(str)), (node.start_byte, new_str)]

def cvt_add_f(node):
    # '' -> f''
    str = text(node).strip()
    new_str = str.replace('{', '{{').replace('}', '}}')
    new_str = f'f{new_str}'
    return [(node.end_byte, -len(str)), (node.start_byte, new_str)]

def cvt_LeftF2RightFormat(node):
    # f'{a}{b}' -> '{}{}'.format(a, b)
    str = text(node).strip()
    params, ret = [], [(node.start_byte + 1, -1)]
    for i in range(len(str)):
        if str[i] == '}':
            param = str[:i].split('{')[-1]
            params.append((i, param))
            ret.append((node.start_byte + i, -len(param)))
    format_str = f".format({', '.join([x[1] for x in params])})"
    ret.append((node.end_byte, format_str))
    return ret

def cvt_RightFormat2LeftF(node):
    # '{}{}'.format(a, b) -> f'{a}{b}'
    str = text(node).strip()
    params_node = node.parent.parent.children[1]
    params_list = text(node)    # (a, b)
    params = params_list[1: -1].replace(' ','').split(',')
    ret = [(node.start_byte, 'f'), 
        (params_node.end_byte, node.end_byte - params_node.end_byte)]
    param_index = 0
    if str.count('{') != len(params):
        return
    for i in range(len(str)):
        if str[i] == '{':
            ret.append((node.start_byte + i + 1, params[param_index]))
            param_index += 1
    return ret