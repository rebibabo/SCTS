from utils import text

'''==========================匹配========================'''
def rec_string(node):
    if node.type == 'string':
        return True

def rec_not_format_string(node):
    if node.type == 'string':
        if text(node)[0] != 'f' and len(node.parent.children) > 2 and node.parent.children[2].text != b'format':
            return True

def match_StringSingle(node):
    if node.type == 'string':
        if '"""' in str or "'''" in str:
            return False
        if text(node)[0] == "'" and text(node)[-1] == "'":
            return True

def match_StringDouble(node):
    if node.type == 'string':
        if '"""' in str or "'''" in str:
            return False
        if text(node)[0] == '"' and text(node)[-1] == '"':
            return True   

def match_format_string(node):
    if node.type == 'string':
        if text(node)[0] == 'f' and len(node.parent.children) > 2:
            return True

'''==========================替换========================'''
def cvt_single_quotation(node):
    # ''
    str = text(node).strip()
    if '"""' in str or "'''" in str:
        return
    new_str = str[1: -1].replace("'", '"')
    new_str = f"'{new_str}'"
    return [(node.end_byte, -len(str)), (node.start_byte, new_str)]

def cvt_double_quotation(node):
    # ""
    str = text(node).strip()
    if '"""' in str or "'''" in str:
        return
    new_str = str[1: -1].replace('"', "'")
    new_str = f'"{new_str}"'
    return [(node.end_byte, -len(str)), (node.start_byte, new_str)]

def cvt_add_f(node):
    # '' -> f''
    str = text(node).strip()
    new_str = str.replace('{', '{{').replace('}', '}}')
    new_str = f'f{new_str}'
    return [(node.end_byte, -len(str)), (node.start_byte, new_str)]
