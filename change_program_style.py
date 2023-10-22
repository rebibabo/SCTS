from tqdm import tqdm
import os
from tree_sitter import Parser, Language
from utils import replace_from_blob, traverse_rec_func, get_parameter_count

class CodeMarker:
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
        else:
            raise NotImplementedError
        self.style_dict = {
            'python':{
                0.1: ('var', 'camel'), 0.2: ('var', 'initcap'), 0.3: ('var', 'underscore'), 0.4: ('var', 'init_underscore'), 0.5: ('var', 'init_dollar'), 0.6: ('var', 'upper'), 0.7: ('var', 'lower'),
                1.1: ('print', 'add_flush'), 1.2: ('print', 'del_flush'), 1.3: ('print', 'add_end'), 1.4: ('print', 'del_end'),
                2.1: ('list', 'init_call_list'), 2.2: ('list', 'init_list'), 2.3: ('list', 'call_list'), 2.4: ('list', 'list'), 
                3.1: ('dict', 'init_call_dict'), 3.2: ('dict', 'init_dict'), 3.3: ('dict', 'call_dict'), 3.4: ('dict', 'dict'), 
                4.1: ('range', 'add_zero'), 4.2: ('range', 'del_zero'), 4.3: ('range', 'add_slice_index'), 4.4: ('range', 'del_slice_index'), 4.5: ('range', 'add_index'),
                5.1: ('call', 'add_magic_call'), 5.2: ('call', 'del_magic_call'),
                6.1: ('string', 'single'), 6.2: ('string', 'double'), 6.3: ('string', 'add_f'), 6.4: ('string', 'right_format'), 6.5: ('string', 'left_f'),
                7.1: ('op', 'augmented_assignment'), 7.2: ('op', 'assignment'), 7.3: ('op', 'test_left_const'), 7.4:('op', 'smaller'), 7.5:('op', 'bigger'),
                8.1: ('for', 'add_enumerate'), 8.2: ('for', 'while'), 8.3: ('for', 'for'),
                9.1: ('declare', 'split'), 9.2: ('declare', 'merge_simple'), 9.3: ('declare', 'merge'),
                10.1: ('return', 'add_bracket'), 10.2: ('return', 'del_bracket'), 10.3: ('return', 'add_None'), 10.4: ('return', 'del_None'),
            },
            'c':{
                0.1: ('var', 'camel'), 0.2: ('var', 'initcap'), 0.3: ('var', 'underscore'), 0.4: ('var', 'init_underscore'), 0.5: ('var', 'init_dollar'), 0.6: ('var', 'upper'), 0.7: ('var', 'lower'),
                1.1: ('blank', 'bracket_1'), 1.2: ('blank', 'bracket_2'), 1.3: ('blank', 'add_blank'), 1.4: ('blank', 'add_bracket'),
                2.1: ('op', 'augmented_assignment'), 2.2: ('op', 'assignment'), 2.3: ('op', 'test_left_const'), 2.4:('op', 'smaller'), 2.5:('op', 'bigger'),
                3.1: ('update', 'left'), 3.2: ('update', 'right'), 3.3: ('update', 'augment'), 3.4: ('update', 'assignment'),
                4.1: ('main', 'int_void_return'), 4.2: ('main', 'int_void'), 4.3: ('main', 'int_return'), 4.4: ('main', 'int'), 4.5: ('main', 'int_arg_return'), 4.6: ('main', 'int_arg'), 4.7: ('main', 'void_arg'), 4.8: ('main', 'void'),
                5.1: ('array', 'dyn_mem'), 5.2: ('array', 'static_mem'), 5.3: ('array', 'pointer'), 5.4: ('array', 'array'),
                6.1: ('declare', 'split'), 6.2: ('declare', 'merge'), 6.3: ('declare', 'first'), 6.4: ('declare', 'temp'),
                7.1: ('loop', 'obc'), 7.2: ('loop', 'aoc'), 7.3: ('loop', 'abo'), 7.4: ('loop', 'aoo'), 7.5: ('loop', 'obo'), 7.6: ('loop', 'ooc'), 7.7: ('loop', 'ooo'), 7.8: ('loop', 'for'), 7.9: ('loop', 'while'),
            }
        }

    def get_file_popularity(self, style_choice, code):
        style_num = {x:0 for x in style_choice}
        if not isinstance(style_choice, list):
            style_choice = [style_choice]
        for style in style_choice:
            AST = self.parser.parse(bytes(code, encoding='utf-8'))
            (style_type, style_subtype) = self.style_dict[self.language][style]
            (match_func, sub_func) = self.op[style_type][style_subtype]
            match_nodes = []
            traverse_rec_func(AST.root_node, match_nodes, match_func)
            if len(match_nodes) > 0:
                style_num[style] += 1
                # input(code)
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
                    

    def change_file_style(self, style_choice, code):
        orig_code = code
        if not isinstance(style_choice, list):
            style_choice = [style_choice]
        for style in style_choice:
            AST = self.parser.parse(bytes(code, encoding='utf-8'))
            (style_type, style_subtype) = self.style_dict[self.language][style]
            (match_func, sub_func) = self.op[style_type][style_subtype]
            operations, match_nodes = [], []
            traverse_rec_func(AST.root_node, match_nodes, match_func, code)
            for node in match_nodes:
                # try:
                if get_parameter_count(sub_func) == 1:
                    op = sub_func(node)
                else:
                    op = sub_func(node, code)
                # except:
                #     print("error", style_choice)
                #     continue
                if op is not None:
                    operations.extend(op)
            code = replace_from_blob(operations, code)
        succ = orig_code.replace(' ','').replace('\n', '') != code.replace(' ','').replace('\n', '')
        return code, succ

    def change_dir_style(self, style_choice, dir_path, output_path, output_choice=-1):
        # choice = -1:不写
        # choice = 0: 只写入转换成功的代码
        # choice = 1: 分开写入转换成功和转换失败的代码
        # choice = 2: 合并写入转换成功和转换失败的代码
        try_num, succ_num = 0, 0
        file_paths = []
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
        with tqdm(total=len(file_paths)) as pbar:
            for file_path in file_paths:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                    new_code, succ = self.change_file_style(style_choice, code)
                    try_num += 1
                    if succ:
                        # print('='*40)
                        # input(code)
                        # print('-'*30)
                        # input(new_code)
                        succ_num += 1
                        if output_choice == 0 or output_choice == 1:
                            output_file = file_path.replace(dir_path, os.path.join(output_path, 'succ'))
                            if not os.path.exists(os.path.dirname(output_file)):
                                os.makedirs(os.path.dirname(output_file))
                            with open(output_file, 'w') as f_w:
                                f_w.write(new_code)
                    else:
                        if output_choice == 1:
                            output_file = file_path.replace(dir_path, os.path.join(output_path, 'fail'))
                            if not os.path.exists(os.path.dirname(output_file)):
                                os.makedirs(os.path.dirname(output_file))
                            with open(output_file, 'w') as f_w:
                                f_w.write(new_code)
                    if output_choice == 2:
                        output_file = file_path.replace(dir_path, os.path.join(output_path, 'merge'))
                        if not os.path.exists(os.path.dirname(output_file)):
                            os.makedirs(os.path.dirname(output_file))
                        with open(output_file, 'w') as f_w:
                            f_w.write(new_code)
                    pbar.set_description(f'Successful Rate: {succ_num/try_num*100:.2f}%')
                    pbar.update()


if __name__ == '__main__':
    codemarker = CodeMarker('python')
    # code = open('test.c').read()
    # print(code)
    # new_code, succ = codemarker.change_file_style([6.4], code)
    # print(new_code)
    for style_choice in [8.3, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4]:
        print('style_choice:',style_choice)
        codemarker.change_dir_style([style_choice], 'dataset/codesearch/0', f'change/{style_choice}')
    # codemarker.get_dir_popularity([5.1], 'dataset/ProgramData/2')

#[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4]
#[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9]


