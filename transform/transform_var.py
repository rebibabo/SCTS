import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import re
import inflection
from transform.Core import Core
from ist_utils import text, parent
from transformers import BertTokenizer

class Tool:
    def __init__(self) -> None:
        self.tokenizer = None
        self.keywords = {
            'c':[
                'auto', 'double', 'int', 'struct', 'break', 'else', 'long', 'switch', 'case', 'enum',
                'register', 'typedef', 'char', 'extern', 'return', 'union', 'const', 'float', 'short',
                'unsigned', 'continue', 'for', 'signed', 'void', 'default', 'goto', 'sizeof', 'volatile',
                'do', 'if', 'while', 'static', 'uint32_t', 'uint64_t'
                ],
            'java':[
                'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const', 'continue', 'default', 
                'do', 'double', 'else', 'enum', 'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements', 'import', 
                'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package', 'private', 'protected', 'public', 'return', 
                'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 
                'void', 'volatile', 'while'
                ]
        }
    
    def get_keywords(self):
        return self.keywords

    def is_all_lowercase(self, name):     # aaabbb
        return name.lower() == name and \
            not self.is_snake(name) and \
            not self.is_init_underscore(name) and \
            not self.is_init_dollar(name) 

    def is_all_uppercase(self, name):     # AAABBB
        return name.upper() == name

    def is_camel(self, name):        # aaaBbb
        if len(name) == 0: return False
        if self.is_all_lowercase(name): return False
        if not name[0].isalpha(): return False
        return inflection.camelize(name, uppercase_first_letter=False) == name

    def is_pascal(self, name):           # AaaBbb
        if len(name) == 0: return False
        if self.is_all_uppercase(name): return False
        if not name[0].isalpha(): return False
        return inflection.camelize(name, uppercase_first_letter=True) == name

    def is_snake(self, name):        # aaa_bbb
        if len(name) == 0: return False
        return name[0] != '_' and '_' in name.strip('_')

    def is_init_underscore(self, name):   # ___aaa
        if len(name) == 0: return False
        return name[0] == '_' and name[1:].strip('_') != ''

    def is_init_dollar(self, name):       # $$$aaa
        if len(name) == 0: return False
        return name[0] == '$' and name[1:].strip('$') != ''

    def is_initcap(self, name):           # AaaBbb
        if self.is_all_uppercase(name): return False
        if not name[0].isalpha(): return False
        return inflection.camelize(name, uppercase_first_letter=True) == name

    def sub_token(self, name):            # 将token变成subtoken
        subtoken = []
        if len(name) == 0:
            return subtoken
        pre_i = 0
        if self.is_camel(name):
            subtoken = []
            for i in range(len(name)):
                if name[i].isupper():
                    subtoken.extend(self.sub_token(name[pre_i: i]))
                    pre_i = i
            subtoken.append(name[pre_i:].lower())
            return subtoken
        elif self.is_pascal(name):
            subtoken = []
            for i in range(1, len(name)):
                if name[i].isupper():
                    subtoken.extend(self.sub_token(name[pre_i: i]))
                    pre_i = i
            subtoken.append(name[pre_i:].lower())
            return subtoken
        elif self.is_snake(name):
            return name.split('_')
        elif self.is_init_underscore(name):
            new_name = name.strip('_')
            return self.sub_token(new_name)
        elif self.is_init_dollar(name):
            new_name = name.strip('$')
            return self.sub_token(new_name)
        else:
            if self.tokenizer is None:
                ddir = os.path.dirname(os.path.dirname(__file__))
                self.tokenizer = BertTokenizer.from_pretrained(os.path.join(ddir, 'base_model', 'bert-base-uncase'))
            tokens = self.tokenizer.tokenize(name.lower())
            tokens = [re.sub(r'[^a-zA-Z0-9]', '', token) for token in tokens]
            return tokens

tool = Tool()

class Var_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
        self.field_pointer_mapping = {'c': 'field_expression', 'java': 'lambda_expression'}
        self.field_point_mapping = {'c': 'field_expression', 'java': 'field_access'}

    def check(self, u):
        if u.type not in ['identifier', 'field_identifier']: return False
        if text(u) in tool.get_keywords()[self.lang]: return False
        # x->a 的 x
        if self.lang in ['c'] and \
            u.parent.type == self.field_pointer_mapping[self.lang] and \
                '->' in text(u.parent):
            if len(text(u.parent).split('->')) == 2 and \
                text(u) == text(parent(u, 1)).split('->')[0]:
                return True
            else:
                return False
        # x.a 的 x
        if u.parent.type == self.field_point_mapping[self.lang] and \
            '.' in text(u.parent):
            if len(text(u.parent).split('.')) == 2 and \
                text(u) == text(parent(u, 1)).split('.')[0]:
                return True
            else: 
                return False
        if u.parent.type in ['function_declarator', 
                             'call_expression', 
                             'argument_list']: return False
        if len(text(u)) == 0: return False
        return True

class Camel_Core(Var_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def count(self):
        res = 0
        if not self.match_nodes:
            self.match(self.root)
        for node in self.match_nodes:
            res += tool.is_camel(node)
        return res

    def get_opts(self, node): # zs
        # aaaBbb        
        id = text(node)
        subtoken = tool.sub_token(id)
        if len(subtoken) == 0:
            return
        new_id = subtoken[0]
        if len(subtoken) > 1:
            for t in subtoken[1:]:
                new_id += t[0].upper() + t[1:]
        if new_id not in tool.keywords[self.lang] and not new_id.isdigit() and new_id != id:
            self.operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_id)])

class Pascal_Core(Var_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def count(self):
        res = 0
        if not self.match_nodes:
            self.match(self.root)
        for node in self.match_nodes:
            res += tool.is_camel(node)
        return res

    def get_opts(self, node): # zs  
        # AaaBbb
        id = text(node)
        subtoken = tool.sub_token(id)
        new_id = ''
        if len(subtoken) > 1:
            for t in subtoken:
                new_id += t[0].upper() + t[1:]
            if new_id not in tool.keywords[self.lang] and not new_id.isdigit() and new_id != id:
                self.operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_id)])

class Snake_Core(Var_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def count(self):
        res = 0
        if not self.match_nodes:
            self.match(self.root)
        for node in self.match_nodes:
            res += tool.is_snake(node)
        return res

    def get_opts(self, node):  # zs    
        # aaa_bbb
        id = text(node)
        subtoken = tool.sub_token(id)
        new_id = '_'.join(subtoken)
        if new_id not in tool.keywords[self.lang] and not new_id.isdigit() and new_id != id:
            self.operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_id)])

class Hungarian_Core(Var_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def find_type(self, u):
        if self.lang == 'c':
            if len(self._type) > 0: return
            if text(u) == text(self.node) and u.parent.type in ['declaration', 'init_declarator']:
                if u.parent.type == 'declaration':
                    self._type.append(text(u.parent.children[0]))
                elif u.parent.type == 'init_declarator':
                    self._type.append(text(u.parent.parent.children[0]))
            for v in u.children:
                self.find_type(v)
        elif self.lang in ['java', 'c_sharp']:
            if len(self._type) > 0: return
            if text(u) == text(self.node) and u.parent.type in ['variable_declarator', 'formal_parameter']:
                if u.parent.type == 'variable_declarator':
                    self._type.append(text(u.parent.parent.children[0]))
                elif u.parent.type == 'formal_parameter':
                    self._type.append(text(u.parent.children[0]))
            for v in u.children:
                self.find_type(v)

    def count(self):
        res = 0
        if not self.match_nodes:
            self.match(self.root)
        res = 0
        for node in self.match_nodes:
            self._type = []
            self.node = node
            self.find_type(node)
            if len(self._type) == 0: continue
            res += self._type[0] == text(node)[:len(self._type[0])]
        return res

    def find_root(self, u):
        root = None
        while u.parent:
            root = u
            u = u.parent
        return root

    def get_opts(self, node):     
        # intAabb
        root = self.find_root(node)
        if root is None: return
        self._type = []
        self.node = node
        self.find_type(root)
        if len(self._type) == 0: return
        new_id = self._type[0] + text(node)[0].upper() + text(node)[1:]
        self.operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_id)])

class Init_Underscore_Core(Var_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def count(self):
        res = 0
        if not self.match_nodes:
            self.match(self.root)
        for node in self.match_nodes:
            res += tool.is_init_underscore(node)
        return res

    def get_opts(self, node):     # zs 
        # _aaa_bbb
        id = text(node)
        new_id = '_' + id
        if new_id not in tool.keywords[self.lang] and not new_id.isdigit() and new_id != id:
            self.operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_id)])

class Init_Dollar_Core(Var_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def count(self):
        res = 0
        if not self.match_nodes:
            self.match(self.root)
        for node in self.match_nodes:
            res += tool.is_init_dollar(node)
        return res

    def get_opts(self, node):       # zs
        # $aaa_bbb
        id = text(node)
        new_id = '$' + id
        if new_id not in tool.keywords[self.lang] and not new_id.isdigit() and new_id != id:
            self.operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_id)])

class Upper_Core(Var_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def count(self):
        res = 0
        if not self.match_nodes:
            self.match(self.root)
        for node in self.match_nodes:
            res += tool.is_all_uppercase(node)
        return res

    def get_opts(self, node):   # zs    
        # AAABBB
        id = text(node)
        new_id = id.upper()
        if new_id not in tool.keywords[self.lang] and not new_id.isdigit() and new_id != id:
            self.operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_id)])

class Lower_Core(Var_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def count(self):
        res = 0
        if not self.match_nodes:
            self.match(self.root)
        for node in self.match_nodes:
            res += tool.is_all_lowercase(node)
        return res

    def get_opts(self, node):       
        # aaabbb
        id = text(node)
        new_id = id.lower()
        if new_id not in tool.keywords[self.lang] and not new_id.isdigit() and new_id != id:
            self.operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_id)])