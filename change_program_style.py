from itertools import combinations
import random
import tqdm
from collections import Counter, defaultdict
from utils import replace_from_blob, traverse_all_children, traverse_rec_func, traverse_type

class CodeMarker:
    def __init__(self, language):
        self.language = language
        LANGUAGE = Language(f'./build/{language}-languages.so', language)
        parser = Parser()
        parser.set_language(LANGUAGE)
        self.parser = parser
        if self.language == 'java':
            from java.config import transformation_operators as op
            self.op = op
        elif self.language == 'python':
            from python.config import transformation_operators as op
            self.op = op
        else:
            raise NotImplementedError
        self.style_dict = {
            'python':{
                0.1: ('var', 'camel'), 0.2: ('var', 'initcap'), 0.3: ('var', 'init_underscore'), 0.4: ('var', 'init_dollar'), 0.5: ('var', 'upper'), 0.6: ('var', 'lower'),
                1.1: ('print', 'add_flush'), 1.2: ('print', 'del_flush'), 1.3: ('print', 'add_end'), 1.4: ('print', 'del_end'),
                2.1: ('list', 'init_call_list'), 2.2: ('list', 'init_list'), 2.3: ('list', 'call_list'), 2.4: ('list', 'list'), 
                3.1: ('dict', 'init_call_dict'), 3.2: ('dict', 'init_dict'), 3.3: ('dict', 'call_dict'), 3.4: ('dict', 'dict'), 
                4.1: ('range', 'add_zero'), 4.2: ('range', 'del_zero'),
                5.1: ('call', 'add_magic_call'), 5.2: ('call', 'del_magic_call'),
            }
        }

    def change_file_style(self, style_choice, code):
        if not isinstance(style_choice, list):
            style_choice = [style_choice]
        for style in style_choice:
            AST = self.parser.parse(bytes(code, encoding='utf-8'))
            (style_type, style_subtype) = self.style_dict[self.language][style]
            (match_func, sub_func) = self.op[style_type][style_subtype]
            operations, match_nodes = [], []
            traverse_rec_func(AST.root_node, match_nodes, match_func)
            for node in match_nodes:
                op = sub_func(node)
                if op is not None:
                    operations.extend(op)
            code = replace_from_blob(operations, code)
        print(code)


if __name__ == '__main__':
    from tree_sitter import Parser, Language
    codemarker = CodeMarker('python')
    code = open('test.py').read()
    print(code)
    codemarker.change_file_style([0.2, 1.1, 2.1, 3.3, 4.1, 5.1], code)
    



