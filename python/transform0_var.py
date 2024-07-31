from utils import text
import inflection
from tree_sitter import Node
from typing import List, Tuple, Union

python_keywords = ['self', 'args', 'kwargs', 'with', 'def', 'if', 'else', 'and', 'as', 'assert', 'break', 'class', 'continue', 'del', 
 'elif except', 'False', 'finally', 'for', 'from', 'global', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal', 
 'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'yield', 'open', 'none', 'true', 'false', 'list', 
 'set', 'dict', 'module', 'ValueError', 'KonchrcNotAuthorizedError', 'IOError']

id_type = {}

def is_all_lowercase(name: str) -> bool:     # aaabbb
    return name.lower() == name and \
        not is_underscore(name) and \
        not is_init_underscore(name) and \
        not is_init_dollar(name) 

def is_all_uppercase(name: str) -> bool:     # AAABBB
    return name.upper() == name

def is_camel_case(name: str) -> bool:        # aaaBbb
    if is_all_lowercase(name): return False
    if not name[0].isalpha(): return False
    return inflection.camelize(name, uppercase_first_letter=False) == name

def is_initcap(name: str) -> bool:           # AaaBbb
    if is_all_uppercase(name): return False
    if not name[0].isalpha(): return False
    return inflection.camelize(name, uppercase_first_letter=True) == name

def is_underscore(name: str) -> bool:        # aaa_bbb
    return name[0] != '_' and '_' in name.strip('_')

def is_init_underscore(name: str) -> bool:   # _aaa
    return name[0] == '_' and name[1:].strip('_') != ''

def is_init_dollar(name: str) -> bool:       # $$$aaa
    return name[0] == '$' and name[1:].strip('$') != ''

def sub_token(name: str) -> List[str]:            # 将token变成subtoken
    subtoken = []
    if len(name) == 0:
        return subtoken
    pre_i = 0
    if is_camel_case(name):
        for i in range(len(name)):
            if name[i].isupper():
                subtoken.extend(sub_token(name[pre_i: i]))
                pre_i = i
        subtoken.append(name[pre_i:].lower())
    elif is_initcap(name):
        for i in range(1, len(name)):
            if name[i].isupper():
                subtoken.extend(sub_token(name[pre_i: i]))
                pre_i = i
        subtoken.append(name[pre_i:].lower())
    elif is_underscore(name):
        for each in name.split('_'):
            subtoken.extend(sub_token(each))
    elif is_init_underscore(name):
        new_name = name.strip('_')
        return sub_token(new_name)
    elif is_init_dollar(name):
        new_name = name.strip('$')
        return sub_token(new_name)
    else:
        return [name]
    return subtoken
    
'''==========================匹配========================'''
def rec_identifier(node: Node) -> bool:
    if node.type != 'identifier': return False
    if text(node) in ['cout', 'endl']: return False
    if text(node) in python_keywords: return False
    if node.parent.type == 'field_expression' and text(node) == text(node.parent.child_by_field_name('argument')): return True  # x->a的x
    if node.parent.type in ['function_declarator', 'call_expression', 'field_expression']: return False
    # if node.id in for_statement_identifiers_ids: return False
    if len(text(node)) == 0: return False
    return True

def cvt_camel(node: Node) -> List[Tuple[int, Union[int, str]]]:            # aaaBbb
    id = text(node)
    if is_initcap(id) or is_underscore(id) or is_init_underscore(id) or is_init_dollar(id):
        subtoken = sub_token(id)
        if len(subtoken) == 0:
            return
        new_id = subtoken[0]
        if len(subtoken) > 1:
            for t in subtoken[1:]:
                new_id += t[0].upper() + t[1:]
        if new_id not in python_keywords and not new_id.isdigit() and new_id != id:
            return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def match_camel(node: Node) -> bool:
    if rec_identifier(node):
        if is_camel_case(text(node)):
            return True
    
def match_initcap(node: Node) -> bool:
    if rec_identifier(node):
        if is_initcap(text(node)):
            return True

def match_underscore(node: Node) -> bool:
    if rec_identifier(node):
        if is_underscore(text(node)):
            return True

def match_init_underscore(node: Node) -> bool:
    if rec_identifier(node):
        if is_init_underscore(text(node)):
            return True

def match_init_dollar(node: Node) -> bool:
    if rec_identifier(node):
        if is_init_dollar(text(node)):
            return True

def match_upper(node: Node) -> bool:
    if rec_identifier(node):
        if is_all_uppercase(text(node)):
            return True

def match_lower(node: Node) -> bool:
    if rec_identifier(node):
        if is_all_lowercase(text(node)):
            return True

'''==========================替换========================'''

def cvt_initcap(node: Node) -> List[Tuple[int, Union[int, str]]]:          # AaaBbb
    id = text(node)
    if is_camel_case(id) or is_underscore(id) or is_init_underscore(id) or is_init_dollar(id):
        subtoken = sub_token(id)
        new_id = ''
        if len(subtoken) > 1:
            for t in subtoken:
                new_id += t[0].upper() + t[1:]
            if new_id not in python_keywords and not new_id.isdigit() and new_id != id:
                return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]
        
def cvt_underscore(node: Node) -> List[Tuple[int, Union[int, str]]]:       # aaa_bbb
    id = text(node)
    if is_camel_case(id) or is_initcap(id) or is_init_underscore(id) or is_init_dollar(id):
        subtoken = sub_token(id)
        new_id = '_'.join(subtoken)
        if new_id not in python_keywords and not new_id.isdigit() and new_id != id:
            return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_init_underscore(node: Node) -> List[Tuple[int, Union[int, str]]]:  # _aaa_bbb
    id = text(node)
    new_id = '_' + id
    if new_id not in python_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_init_dollar(node: Node) -> List[Tuple[int, Union[int, str]]]:      # $aaa_bbb
    id = text(node)
    new_id = '$' + id
    if new_id not in python_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_upper(node: Node) -> List[Tuple[int, Union[int, str]]]:            # AAABBB
    id = text(node)
    new_id = id.upper()
    if new_id not in python_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_lower(node: Node) -> List[Tuple[int, Union[int, str]]]:            # aaabbb
    id = text(node)
    new_id = id.lower()
    if new_id not in python_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]
