from utils import text
import inflection

java_keywords = ['abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const', 'continue', 'default', 
 'do', 'double', 'else', 'enum', 'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements', 'import', 
 'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package', 'private', 'protected', 'public', 'return', 
 'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 
 'void', 'volatile', 'while']

id_type = {}

def is_all_lowercase(name):     # aaabbb
    return name.lower() == name and \
        not is_underscore(name) and \
        not is_init_underscore(name) and \
        not is_init_dollar(name) 

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

def is_init_underscore(name):   # _aaa
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

def get_id(node):   # 遍历node，获取id
    id = []
    def traverse(node):
        if node.type == 'identifier':
            id.append(text(node))
        for child in node.children:
            traverse(child)
    traverse(node)
    return id[0] if len(id) > 0 else ''

def get_id_type(root, id_type): # 遍历根节点，获取所有id的类型
    for u in root.children:
        if u.type in ['field_declaration', 'local_variable_declaration']:
            type = u.child_by_field_name('type')
            if type.type == 'type_identifier':
                continue
            ids = []
            for v in u.children:
                if text(v) not in [',', ';'] and v.type != 'integral_type':
                    ids.append(get_id(v))
            ids = [id for id in ids if id != '']
            for id in ids:
                id_type[id] = text(type)
        get_id_type(u, id_type)

'''==========================匹配========================'''
def rec_identifier(node):   # tx
    global id_type
    if not node.parent: # 如果是root节点
        id_type.clear()
        get_id_type(node, id_type)
    if node.type not in ['identifier', 'field_identifier']: return False
    if text(node) in java_keywords: return False
    if node.parent.type == 'field_expression' and \
       text(node) == text(node.parent.child_by_field_name('argument')): return True  # x->a的x
    if node.parent.type in ["function_definition", "formal_parameter", "argument_list"]: return False
    if len(text(node)) == 0: return False
    return True

def match_camel(node):
    if rec_identifier(node):
        if is_camel_case(text(node)):
            return True
    
def match_initcap(node):
    if rec_identifier(node):
        if is_initcap(text(node)):
            return True

def match_underscore(node):
    if rec_identifier(node):
        if is_underscore(text(node)):
            return True

def match_init_underscore(node):
    if rec_identifier(node):
        if is_init_underscore(text(node)):
            return True

def match_init_dollar(node):
    if rec_identifier(node):
        if is_init_dollar(text(node)):
            return True

def match_upper(node):
    if rec_identifier(node):
        if is_all_uppercase(text(node)):
            return True

def match_lower(node):
    if rec_identifier(node):
        if is_all_lowercase(text(node)):
            return True

def match_inviChar(node):
    if rec_identifier(node):
        if text(node).startswith(chr(0x200B)) and text(node).endswith(chr(0x200B)):
            return True

def match_hungarian(node):
    if rec_identifier(node):
        for type in ['int', 'char', 'float', 'double', 'long', 'short']:
            if text(node).startswith(type):
                return True

'''==========================替换========================'''
def cvt_camel(node):            # aaaBbb
    id = text(node)
    if is_initcap(id) or is_underscore(id) or is_init_underscore(id) or is_init_dollar(id): 
        subtoken = sub_token(id)
        if len(subtoken) == 0:
            return
        new_id = subtoken[0]
        if len(subtoken) > 1:
            for t in subtoken[1:]:
                new_id += t[0].upper() + t[1:]
        if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
            return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_initcap(node):          # AaaBbb
    id = text(node)
    if is_camel_case(id) or is_underscore(id) or is_init_underscore(id) or is_init_dollar(id): 
        subtoken = sub_token(id)
        new_id = ''
        if len(subtoken) > 1:
            for t in subtoken:
                new_id += t[0].upper() + t[1:]
            if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
                return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]
        
def cvt_underscore(node):       # aaa_bbb
    id = text(node)
    if is_camel_case(id) or is_initcap(id) or is_init_underscore(id) or is_init_dollar(id): 
        subtoken = sub_token(id)
        new_id = '_'.join(subtoken)
        if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
            return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_init_underscore(node):  # _aaa_bbb
    id = text(node)
    new_id = '_' + id
    if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_init_dollar(node):      # $aaa_bbb
    id = text(node)
    new_id = '$' + id
    if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_upper(node):            # AAABBB
    id = text(node)
    new_id = id.upper()
    if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_lower(node):            # aaabbb
    id = text(node)
    new_id = id.lower()
    if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_insertInviChar(node):
    id = text(node)
    invichars = chr(0x200B) + chr(0x200D)
    new_id = invichars + id + invichars
    if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]

def cvt_hungarian(node):        # typeId tx
    id = text(node)
    if id not in id_type: return
    type = id_type[id]
    new_id = f'{type}{id[0].upper() + id[1:]}'
    if new_id not in java_keywords and not new_id.isdigit() and new_id != id:
        return [(node.end_byte, node.start_byte), (node.start_byte, new_id)]