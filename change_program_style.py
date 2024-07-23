from tqdm import tqdm
import os
import json
from tree_sitter import Parser, Language
from utils import *
import subprocess

try:
    from graphviz import Digraph
except:
    os.system('sudo apt-get install graphviz graphviz-doc')
    os.system('pip install graphviz')
    from graphviz import Digraph

class SCTS:
    def __init__(self, language):
        self.language = language
        if not os.path.exists(f'./build/{language}-languages.so'):
            if not os.path.exists(f'./tree-sitter-{language}'):
                os.system(f'git clone https://github.com/tree-sitter/tree-sitter-{language}')
            Language.build_library(
                f'./build/{language}-languages.so',
                [
                    f'./tree-sitter-{language}',
                ]
            )
            os.system(f'rm -rf ./tree-sitter-{language}')
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
        elif self.language == 'c':
            from c.config import transformation_operators as op
            self.op = op
        elif self.language == 'cpp':
            from cpp.config import transformation_operators as op
            self.op = op
        else:
            raise NotImplementedError
        self.style_dict = {
            'python':{
                "0.1": ('var', 'camel'), "0.2": ('var', 'initcap'), "0.3": ('var', 'underscore'), "0.4": ('var', 'init_underscore'), "0.5": ('var', 'init_dollar'), "0.6": ('var', 'upper'), "0.7": ('var', 'lower'),
                "1.1": ('print', 'add_flush'), "1.2": ('print', 'del_flush'), "1.3": ('print', 'add_end'), "1.4": ('print', 'del_end'),
                "2.1": ('list', 'init_call_list'), "2.2": ('list', 'init_list'), "2.3": ('list', 'call_list'), "2.4": ('list', 'list'), 
                "3.1": ('dict', 'init_call_dict'), "3.2": ('dict', 'init_dict'), "3.3": ('dict', 'call_dict'), "3.4": ('dict', 'dict'), 
                "4.1": ('range', 'add_zero'), "4.2": ('range', 'del_zero'), "4.3": ('range', 'add_slice_index'), "4.4": ('range', 'del_slice_index'), "4.5": ('range', 'add_index'),
                "5.1": ('call', 'add_magic_call'), "5.2": ('call', 'del_magic_call'),
                "6.1": ('string', 'single'), "6.2": ('string', 'double'), "6.3": ('string', 'add_f'),
                "7.1": ('op', 'augmented_assignment'), "7.2": ('op', 'assignment'), "7.3": ('op', 'test_left_const'), "7.4":('op', 'smaller'), "7.5":('op', 'bigger'), "7.6":('op', 'chain'),
                "8.1": ('for', 'add_enumerate'), "8.2": ('for', 'while'), "8.3": ('for', 'for'),
                "9.1": ('declare', 'split'), "9.2": ('declare', 'merge_simple'),
                "10.1": ('return', 'add_bracket'), "10.2": ('return', 'del_bracket'), "10.3": ('return', 'add_None'), "10.4": ('return', 'del_None'),
            },
            'c':{
                "0.1": ('var', 'camel'), "0.2": ('var', 'initcap'), "0.3": ('var', 'underscore'), "0.4": ('var', 'init_underscore'), "0.5": ('var', 'init_dollar'), "0.6": ('var', 'upper'), "0.7": ('var', 'lower'), "0.8": ('var', 'hungarian'),
                "1.1": ('blank', 'bracket_1'), "1.2": ('blank', 'bracket_2'), "1.3": ('blank', 'add_blank'), "1.4": ('blank', 'add_bracket'), "1.5": ('blank', 'del_bracket'),
                "2.1": ('op', 'assignment'), "2.2": ('op', 'augmented_assignment'), "2.3": ('op', 'test_left_const'), "2.4":('op', 'smaller'), "2.5":('op', 'bigger'), "2.6": ('op', 'equal'), "2.7": ('op', 'not_equal'),
                "3.1": ('update', 'left'), "3.2": ('update', 'right'), "3.3": ('update', 'augment'), "3.4": ('update', 'assignment'),
                "4.1": ('main', 'int_void_return'), "4.2": ('main', 'int_void'), "4.3": ('main', 'int_return'), "4.4": ('main', 'int'), "4.5": ('main', 'int_arg_return'), "4.6": ('main', 'int_arg'), "4.7": ('main', 'void_arg'), "4.8": ('main', 'void'),
                "5.1": ('array', 'dyn_mem'), "5.2": ('array', 'static_mem'), "5.3": ('array', 'pointer'), "5.4": ('array', 'array'),
                "6.1": ('declare', 'split'), "6.2": ('declare', 'merge'), "6.3": ('declare', 'first'), "6.4": ('declare', 'temp'), "6.5": ('declare', 'assign_split'),
                "7.1": ('loop', 'obc'), "7.2": ('loop', 'aoc'), "7.3": ('loop', 'abo'), "7.4": ('loop', 'aoo'), "7.5": ('loop', 'obo'), "7.6": ('loop', 'ooc'), "7.7": ('loop', 'ooo')," 7.8": ('loop', 'for'), "7.9": ('loop', 'while'), "7.10": ('loop', 'do_while'),
                "8.1": ('if', 'merge'), "8.2": ('if', 'switch'), "8.3": ('if', 'if')
            },
            'cpp':{
                "0.1": ('var', 'camel'), "0.2": ('var', 'initcap'), "0.3": ('var', 'underscore'), "0.4": ('var', 'init_underscore'), "0.5": ('var', 'init_dollar'), "0.6": ('var', 'upper'), "0.7": ('var', 'lower'), "0.8": ('var', 'hungarian'),
                "1.1": ('blank', 'bracket_1'), "1.2": ('blank', 'bracket_2'), "1.3": ('blank', 'add_blank'), "1.4": ('blank', 'add_bracket'), "1.5": ('blank', 'del_bracket'),
                "2.1": ('op', 'assignment'), "2.2": ('op', 'augmented_assignment'), "2.3": ('op', 'test_left_const'), "2.4":('op', 'smaller'), "2.5":('op', 'bigger'), "2.6": ('op', 'equal'), "2.7": ('op', 'not_equal'),
                "3.1": ('update', 'left'), "3.2": ('update', 'right'), "3.3": ('update', 'augment'), "3.4": ('update', 'assignment'),
                "4.1": ('main', 'int_void_return'), "4.2": ('main', 'int_void'), "4.3": ('main', 'int_return'), "4.4": ('main', 'int'), "4.5": ('main', 'int_arg_return'), "4.6": ('main', 'int_arg'), "4.7": ('main', 'void_arg'), "4.8": ('main', 'void'),
                "5.1": ('array', 'dyn_mem'), "5.2": ('array', 'static_mem'), "5.3": ('array', 'pointer'), "5.4": ('array', 'array'),
                "6.1": ('declare', 'split'), "6.2": ('declare', 'merge'), "6.3": ('declare', 'first'), "6.4": ('declare', 'temp'), "6.5": ('declare', 'assign_split'),
                "7.1": ('loop', 'obc'), "7.2": ('loop', 'aoc'), "7.3": ('loop', 'abo'), "7.4": ('loop', 'aoo'), "7.5": ('loop', 'obo'), "7.6": ('loop', 'ooc'), "7.7": ('loop', 'ooo')," 7.8": ('loop', 'for'), "7.9": ('loop', 'while'), "7.10": ('loop', 'do_while'),
                "8.1": ('if', 'merge'), "8.2": ('if', 'switch'), "8.3": ('if', 'if'),
                "9.1": ('cpp', 'stdc++'), "9.2": ('cpp', 'namespace'), "9.3": ('cpp', 'sync_with_false'), "9.4": ('cpp', 'struct'), "9.5": ('cpp', 'coutendl'), "9.6": ('cpp', 'cout'), "9.7": ('cpp', 'del_endl'), "9.8": ('cpp', 'printf'), "9.9": ('cpp', 'cin')," 9.10": ('cpp', 'scanf'),
            },
            'java':{
                "0.1": ('var', 'camel'), "0.2": ('var', 'initcap'), "0.3": ('var', 'underscore'), "0.4": ('var', 'init_underscore'), "0.5": ('var', 'init_dollar'), "0.6": ('var', 'upper'), "0.7": ('var', 'lower'), "0.8": ('var', 'invichar'), "0.9": ('var', 'hungarian'),
                "1.1": ('op', 'assignment'), "1.2": ('op', 'augmented_assignment'), "1.3": ('op', 'test_left_const'), "1.4":('op', 'smaller'), "1.5":('op', 'bigger'),
                "2.1": ('update', 'left'), "2.2": ('update', 'right'), "2.3": ('update', 'augment'), "2.4": ('update', 'assignment'),
                "3.1": ('string', 'new_string'), "3.2": ('string', 'string'), "3.3": ('string', 'add'),
                "4.1": ('bool', 'not_equal'), "4.2": ('bool', 'equal'), "4.3": ('bool', 'single'),
                "5.1": ('loop', 'obc'), "5.2": ('loop', 'aoc'), "5.3": ('loop', 'abo'), "5.4": ('loop', 'aoo'), "5.5": ('loop', 'obo'), "5.6": ('loop', 'ooc'), "5.7": ('loop', 'ooo'), "5.8": ('loop', 'for'), "5.9": ('loop', 'while'), "5.10": ('loop', 'do_while'),
                "6.1": ('array', 'index_zero'), "6.2": ('array', 'index'), "6.3": ('array', 'size'), "6.4": ('array', 'is_empty'),
            }
        }

    def get_file_popularity(self, style_choice, code):
        if style_choice == 'all':
            style_choice = list(self.style_dict[self.language].keys())
        style_num = {x:0 for x in style_choice}
        if not isinstance(style_choice, list):
            style_choice = [style_choice]
        for style in style_choice:
            AST = self.parser.parse(bytes(code, encoding='utf-8'))
            (style_type, style_subtype) = self.style_dict[self.language][style]
            (_, _, match_func) = self.op[style_type][style_subtype]
            match_nodes = []
            traverse_rec_func(AST.root_node, match_nodes, match_func)
            style_num[style] += len(match_nodes)
        return style_num

    def get_dir_popularity(self, style_choice, dir_path):
        tot_style_num = {x:0 for x in style_choice}
        file_paths = []
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
        with tqdm(total=len(file_paths)) as pbar:
            for file_path in file_paths:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                    style_num = self.get_file_popularity(style_choice, code)
                    for key, value in style_num.items():
                        tot_style_num[key] += value
                    pbar.update()
        print(tot_style_num)            

    def change_file_style(self, style_choice, code, format=False):
        if format:
            format_code = self.format(code)
        else:
            format_code = code
        if not isinstance(style_choice, list):
            style_choice = [style_choice]
        for style in style_choice:
            AST = self.parser.parse(bytes(format_code, encoding='utf-8'))
            (style_type, style_subtype) = self.style_dict[self.language][style]
            (rec_func, sub_func, _) = self.op[style_type][style_subtype]
            operations, match_nodes = [], []
            traverse_rec_func(AST.root_node, match_nodes, rec_func, format_code)
            for node in match_nodes:
                try:
                    if get_parameter_count(sub_func) == 1:
                        op = sub_func(node)
                    else:
                        op = sub_func(node, format_code)
                except:
                    op = None
                if op is not None:
                    operations.extend(op)
            code = replace_from_blob(operations, format_code.encode('utf-8')).decode('utf-8', errors='ignore')       # 要将code转为bytes类型，否则start_byte会出现偏移问题，然后解码
        succ = format_code.replace(' ','').replace('\n', '') != code.replace(' ','').replace('\n', '')
        return code, succ

    def see_tree(self, code):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        dot = Digraph(comment='AST Tree')
        create_ast_tree(dot, root_node)
        dot.render('ast_tree')

    def tokenize(self, code):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        tokens = []
        tokenize_help(root_node, tokens)
        return tokens

    def check_syntax(self, code):
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        return not AST.root_node.has_error

    def format(self, code):
        if self.language == 'c' or self.language == 'cpp':
            # clang-format -style="{IndentWidth: 4}" -
            try:
                formatted_code = subprocess.run(
                    ["clang-format", "-style={IndentWidth: 4}", "-"],
                    input=code, 
                    text=True,  
                    capture_output=True 
                ).stdout
            except:
                os.system('sudo apt-get install clang-format')
                return code
            return formatted_code
        elif self.language == 'python':
            # yapf -p YourPythonFile.py
            try:
                formatted_code = subprocess.run(
                    ["yapf", "-p"],
                    input=code, 
                    text=True,  
                    capture_output=True 
                ).stdout
            except:
                os.system('pip install yapf')
                return code
            return formatted_code
        elif self.language == 'java':
            # astyle --style=java -n YourJavaFile.java
            try:
                formatted_code = subprocess.run(
                    ["astyle", "--style=java", "-n"],
                    input=code, 
                    text=True,  
                    capture_output=True 
                ).stdout
            except:
                os.system('sudo apt-get install astyle')
                return code
            return formatted_code


if __name__ == '__main__':
    language = 'java'
    style = ["3.1","1.5"]  # "3.1"
    dataset = open(f'dataset/{language}_formatted.jsonl').readlines()[:1000]
    scts = SCTS(language)
    try_num, succ_num = 0, 0
    bar = tqdm(dataset, total=len(dataset))
    for i, line in enumerate(bar):
        try_num += 1
        code = json.loads(line)['code']
        if not scts.check_syntax(code):
            continue
        new_code, succ = scts.change_file_style(style, code)
        if succ:
            succ_num += 1
        succ_rate = succ_num / try_num
        bar.set_description(f"style {style} succ rate {succ_rate * 100:.2f}%")

# 'python': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4],\
# 'cpp': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9],\
# 'cpp': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.11],\
# 'java': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.1, 6.2, 6.3, 6.4]