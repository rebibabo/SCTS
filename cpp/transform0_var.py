from utils import text
import inflection
from tree_sitter import Node
from typing import List, Tuple, Union, Dict

cpp_keywords = [
    'alignas', 'alignof', 'and', 'and_eq', 'asm', 'atomic_cancel', 'atomic_commit', 'atomic_noexcept', 'auto',
    'bitand', 'bitor', 'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t', 'class',
    'compl', 'concept', 'const', 'consteval', 'constexpr', 'constinit', 'const_cast', 'continue', 'co_await',
    'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do', 'double', 'dynamic_cast', 'else', 'enum',
    'explicit', 'export', 'extern', 'false', 'float', 'for', 'friend', 'goto', 'if', 'inline', 'int', 'long',
    'mutable', 'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq', 'private',
    'protected', 'public', 'reflexpr', 'register', 'reinterpret_cast', 'requires', 'return', 'short', 'signed',
    'sizeof', 'static', 'static_assert', 'static_cast', 'struct', 'switch', 'synchronized', 'template', 'this',
    'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using',
    'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq'
]

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

def get_id(node: Node) -> str:   # 遍历node，获取id
    id = []
    def traverse(node):
        if node.type == 'identifier':
            id.append(text(node))
        for child in node.children:
            traverse(child)
    traverse(node)
    return id[0] if len(id) > 0 else ''

def get_id_type(root: Node, id_type: Dict[str, str]) -> None: # 遍历根节点，获取所有id的类型
    for u in root.children:
        if u.type == 'declaration':
            type = text(u.child_by_field_name('type'))
            ids = []
            for v in u.children:
                if v.type == 'type_qualifier':
                    type = 'const ' + type
                    continue
                elif v.type == 'storage_class_specifier':
                    type = 'static ' + type
                    continue
                elif text(v) not in [',', ';'] and v.type != 'primitive_type':
                    ids.append(get_id(v))
            for id in ids:
                id_type[id] = type
        get_id_type(u, id_type)

'''==========================匹配========================'''
def rec_identifier(node: Node) -> bool:
    global id_type
    if not node.parent: # 如果是root节点
        id_type.clear()
        get_id_type(node, id_type)
    if node.type not in ['identifier', 'field_identifier']: return False
    if text(node) in ['cout', 'endl']: return False
    if text(node) in cpp_keywords: return False
    if node.parent.type == 'field_expression' and text(node) == text(node.parent.child_by_field_name('argument')): return True  # x->a的x
    if node.parent.type in ["function_definition", "declaration", "argument_list", "init_declarator", "binary_expression", "return_statement"]: return False
    # if node.id in for_statement_identifiers_ids: return False
    if len(text(node)) == 0: return False
    return True

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

def match_hungarian(node: Node) -> bool:
    if rec_identifier(node):
        for type in ['int', 'char', 'float', 'double', 'long', 'short']:
            if text(node).startswith(type):
                return True

'''==========================替换========================'''
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
        if new_id not in cpp_keywords and not new_id.isdigit() and new_id != id:
            return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_initcap(node: Node) -> List[Tuple[int, Union[int, str]]]:          # AaaBbb
    id = text(node)
    if is_camel_case(id) or is_underscore(id) or is_init_underscore(id) or is_init_dollar(id):
        subtoken = sub_token(id)
        new_id = ''
        if len(subtoken) > 1:
            for t in subtoken:
                new_id += t[0].upper() + t[1:]
            if new_id not in cpp_keywords and not new_id.isdigit() and new_id != id:
                return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]
        
def cvt_underscore(node: Node) -> List[Tuple[int, Union[int, str]]]:       # aaa_bbb
    id = text(node)
    if is_camel_case(id) or is_initcap(id) or is_init_underscore(id) or is_init_dollar(id):
        subtoken = sub_token(id)
        new_id = '_'.join(subtoken)
        if new_id not in cpp_keywords and not new_id.isdigit() and new_id != id:
            return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_init_underscore(node: Node) -> List[Tuple[int, Union[int, str]]]:  # _aaa_bbb
    id = text(node)
    new_id = '_' + id
    if not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_init_dollar(node: Node) -> List[Tuple[int, Union[int, str]]]:      # $aaa_bbb
    id = text(node)
    new_id = '$' + id
    if not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_upper(node: Node) -> List[Tuple[int, Union[int, str]]]:            # AAABBB
    id = text(node)
    new_id = id.upper()
    if not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_lower(node: Node) -> List[Tuple[int, Union[int, str]]]:            # aaabbb
    id = text(node)
    new_id = id.lower()
    if new_id not in cpp_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_hungarian(node: Node) -> List[Tuple[int, Union[int, str]]]:        # typeId tx
    id = text(node)
    type = id_type[id]
    type = type.replace('const ', '').replace('static ', '')
    new_id = f'{type}{id[0].upper() + id[1:]}'
    if new_id not in cpp_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]
