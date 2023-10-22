from utils import replace_from_blob, traverse_rec_func, text
import inflection

def is_all_lowercase(name):     # aaabbb
    return name.lower() == name

def is_all_uppercase(name):     # AAABBB
    return name.upper() == name

def is_camel_case(name):        # aaaBbb
    if is_all_lowercase(name): return False
    if not name[0].isalpha(): return False
    return inflection.camelize(name, uppercase_first_letter=False) == name

def is_initcap(name):           # AaaBbb
    if is_all_uppercase(name): return False
    if not name[0].isalpha(): return False
    return inflection.camelize(name, uppercase_first_letter=True) == name

def is_underscore(name):        # aaa_bbb
    return name[0] != '_' and '_' in name.strip('_')

def is_init_underscore(name):   # ___aaa
    return name[0] == '_' and name[1:].strip('_') != ''

def is_init_dollar(name):       # $$$aaa
    return name[0] == '$' and name[1:].strip('$') != ''

def sub_token(name):            # 将token变成subtoken
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
def rec_identifier(node):
    if node.type == 'identifier' and node.parent.type not in ['function_declarator', 'call_expression', 'field_expression']:
        return True

'''==========================替换========================'''
def cvt_camel(node):            # aaaBbb
    id = text(node)
    subtoken = sub_token(id)
    if len(subtoken) == 0:
        return
    new_id = subtoken[0]
    if len(subtoken) > 1:
        for t in subtoken[1:]:
            new_id += t[0].upper() + t[1:]
    return [(node.end_byte, -len(id)), (node.start_byte, new_id)]

def cvt_initcap(node):          # AaaBbb
    id = text(node)
    subtoken = sub_token(id)
    new_id = ''
    if len(subtoken) > 1:
        for t in subtoken:
            new_id += t[0].upper() + t[1:]
        return [(node.end_byte, -len(id)), (node.start_byte, new_id)]
        
def cvt_underscore(node):       # aaa_bbb
    id = text(node)
    subtoken = sub_token(id)
    new_id = '_'.join(subtoken)
    return [(node.end_byte, -len(id)), (node.start_byte, new_id)]

def cvt_init_underscore(node):  # _aaa_bbb
    id = text(node)
    new_id = '_' + id
    return [(node.end_byte, -len(id)), (node.start_byte, new_id)]

def cvt_init_dollar(node):      # $aaa_bbb
    id = text(node)
    new_id = '$' + id
    return [(node.end_byte, -len(id)), (node.start_byte, new_id)]

def cvt_upper(node):            # AAABBB
    id = text(node)
    new_id = id.upper()
    return [(node.end_byte, -len(id)), (node.start_byte, new_id)]

def cvt_lower(node):            # aaabbb
    id = text(node)
    new_id = id.lower()
    return [(node.end_byte, -len(id)), (node.start_byte, new_id)]