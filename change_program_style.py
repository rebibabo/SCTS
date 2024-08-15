from tqdm import tqdm
import os
import json
from tree_sitter import Parser, Language, Node
from utils import *
import subprocess
import time
from typing import Callable, Literal, Dict, Tuple, Union, List

try:
    from graphviz import Digraph
except:
    os.system('sudo apt-get install graphviz graphviz-doc')
    os.system('pip install graphviz')
    from graphviz import Digraph

class SCTS:
    def __init__(
        self, 
        language: Literal["java", "python", "c", "cpp"]
    ):
        self.language: str = language
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
        self.parser: Parser = parser
        
        if self.language == 'java':
            from java.config import transformation_operators as op
        elif self.language == 'python':
            from python.config import transformation_operators as op
        elif self.language == 'c':
            from c.config import transformation_operators as op
        elif self.language == 'cpp':
            from cpp.config import transformation_operators as op
        else:
            raise NotImplementedError
        self.op: Dict[str, Dict[str, Tuple[Callable, Callable]]] = op
        self.style_dict: Dict[str, Dict[str, Tuple[str, str]]] = json.load(open("styleList.json","r"))

    def get_file_popularity(self, 
        style_choice: Union[Literal['all'], List[str]], 
        code: str
    ) -> Dict[str, int]:
        # 返回文件的风格分布
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

    def get_dir_popularity(
        self, 
        style_choice: Union[Literal['all'], List[str]], 
        dir_path: str
    ) -> Dict[str, int]:
        # 统计目录下所有文件的风格分布
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
        return tot_style_num           

    def change_file_style(
        self, 
        style_choice: Union[str, List[str]], 
        code: str, 
        format: bool = False
    ) -> Tuple[str, bool]:
        '''
        改变代码的风格
        style_choice: 风格名称或风格名称列表
        code: 代码字符串
        format: 是否格式化代码
        返回修改后的代码字符串，以及修改是否成功
        '''
        if format:
            format_code = self.format(code)
        else:
            format_code = code
        if not isinstance(style_choice, list):
            style_choice = [style_choice]
        for style in style_choice:
            AST = self.parser.parse(bytes(format_code, encoding='utf-8'))
            node: Node = AST.root_node
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

    def see_tree(self, 
        code:str, 
        view:bool = True
    ) -> None:
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        dot = Digraph(comment='AST Tree')
        create_ast_tree(dot, root_node)
        dot.render('ast_tree', view=view)

    def tokenize(self, code: str) -> List[str]:
        # 给定代码，返回token列表
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        tokens = []
        tokenize_help(root_node, tokens)
        return tokens

    def check_syntax(self, code: str) -> bool:
        # 检查代码是否符合语法
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        return not AST.root_node.has_error

    def format(self, code: str) -> str:
        # 输入代码，返回格式化后的代码
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

def timer(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time cost: {end_time - start_time:.2f}s")
        return result
    return wrapper

@ timer
def main(language: Literal["java", "python", "c", "cpp"], style: Union[str, List[str]]) -> None:
    dataset = open(f'dataset/{language}_formatted.jsonl').readlines()
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
        bar.set_description(f"Success rate: {succ_num/try_num*100:.2f}%")

if __name__ == '__main__':
    language = 'java'
    style = ["0.1"]  # "3.1"
    main(language, style)
    

# 'python': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4],\
# 'cpp': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9],\
# 'cpp': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.11],\
# 'java': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.1, 6.2, 6.3, 6.4]