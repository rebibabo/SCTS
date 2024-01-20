import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import random
import argparse
import subprocess
from ist_utils import *
from tqdm import tqdm
from tree_sitter import Parser, Language
from transform.transform_var import *
from transform.transform_bracket import *
from transform.transform_augmented_assignment import *
from transform.transform_cmp import *
from transform.transform_for_update import *
from transform.transform_declare_lines import *
from transform.transform_declare_position import *

class IST:
    def __init__(self, language):
        self.language = language
        parent_dir = os.path.dirname(__file__)
        languages_so_path = os.path.join(parent_dir, 'build', f'{language}-languages.so')
        tree_sitter_path = os.path.join(parent_dir, f'tree-sitter-{language}')

        if not os.path.exists(languages_so_path):
            if not os.path.exists(tree_sitter_path):
                process = subprocess.Popen(['git', 'clone', f'https://github.com/tree-sitter/tree-sitter-{language}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                if process.returncode == 0:
                    print(f"Download of tree-sitter-{language} successful.")
                else:
                    print(f"Poor internet connection, please download https://github.com/tree-sitter/tree-sitter-{language} manually.")
                    exit(0)
            
            Language.build_library(languages_so_path, 
                                   [tree_sitter_path])
            # os.system(f'rm -rf ./tree-sitter-{language}')
         
        parser = Parser()
        parser.set_language(Language(languages_so_path, language))
        self.parser = parser
        
        self.style_Core = {
            '0.1': Camel_Core, '0.2': Pascal_Core, '0.3': Snake_Core, '0.4': Hungarian_Core, '0.5': Init_Underscore_Core, '0.6': Init_Dollar_Core, '0.7': Upper_Core, '0.8': Lower_Core,
            '1.1': If_Bracket_Core, '1.2': If_NBracket_Core,
            '2.1': For_Bracket_Core, '2.2': For_NBracket_Core,
            '3.1': While_Bracket_Core, '3.2': While_NBracket_Core,
            '4.1': Augmented_Assignment_Core, '4.2': NAugmented_Assignment_Core,    
            '5.1': Bigger_Core, '5.2': Smaller_Core, '5.3': Equal_Core, '5.4': NEqual_Core,                                                           
            '6.1': Left_Uqdate_Core, '6.2': Right_Uqdate_Core, '6.3': Augmented_Uqdate_Core, '6.4': Assignment_Uqdate_Core,
            '7.1': Decalare_Line_Merge_Core, '7.2': Decalare_Line_Split_Core,
            '8.1': Decalare_Position_First, '8.2': Decalare_Position_Temp
        }

        self.need_bracket = ['12.4']
        self.exclude = {'java': ['5', '6'], 'c': [], 'c_sharp': []}

    def transfer(self, styles, code):
        if not isinstance(styles, list):
            styles = [styles]
        gsucc = 1
        for style in styles:
            if style in self.exclude[self.language]: continue
            AST = self.parser.parse(bytes(code, encoding='utf-8'))
            core = self.style_Core[style](AST.root_node, self.language)
            code, succ = core.run()
            gsucc &= succ
        return code, gsucc
    
    def get_style(self, code, styles=[]):
        if not isinstance(styles, list): styles = [styles]
        res = {}
        if len(styles) == 0:
            styles = list(self.style_Core[self.language].keys())
        for style in styles:
            AST = self.parser.parse(bytes(code, encoding='utf-8'))
            core = self.style_Core[style](AST.root_node, self.language)
            if style in res:
                res[style] += core.count()
            else:
                res[style] = core.count()
        return res

    def tokenize(self, code):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        tokens = []
        tokenize_help(root_node, tokens)
        return tokens

    def check_syntax(self, code):
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        return not AST.root_node.has_error

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', type=str, default='c', choices=['c', 'java', 'c_sharp'])
    parser.add_argument('--task', type=str, default='trans', choices=['trans', 'count'])
    parser.add_argument('--scope', type=str, default='one', choices=['one', 'all'])
    parser.add_argument('--style', nargs='+', type=str)
    args = parser.parse_args()

    lang = args.lang
    task = args.task
    scope = args.scope
    ist = IST(lang)
    styles = args.style
    print(styles)
    
    if task == 'trans':
        if scope == 'all':
            with open(f'./data/{lang}.jsonl', 'r') as file:
                lines = file.readlines()
                try_count = suc_count = 0
                pbar = tqdm(lines, ncols=100)
                pairs = []
                bad_pairs = []
                for line in pbar:
                    obj = json.loads(line)
                    if lang == 'c': code = obj['func']
                    elif lang == 'java': code = obj['fixed']
                    elif lang == 'c_sharp': code = obj['code1']
                    # if not ist.check_syntax(code): continue
                    if 0 <= len(code):
                        try_count += 1
                        try:
                            new_code, succ = ist.transfer(styles, code)
                        except Exception as e:
                            print()
                            print(code)
                            print(f"{e}")
                            exit(0)
                        if succ:
                            pairs.append((code, new_code))
                            suc_count += 1
                    if try_count:
                        pbar.set_description(f'{round(suc_count/try_count * 100, 2)}%, {suc_count}/{try_count}')
                
                # for ori_code, new_code in random.sample(bad_pairs, 10):
                #     print(ori_code)
                #     # print(new_code)
                #     input()
                #     os.system('cls')

        elif scope == 'one':
            if lang == 'c_sharp':
                code = open(f'./test_code/test.cs', 'r').read()
            else:
                code = open(f'./test_code/test.{lang}', 'r').read()
            print(code)
            new_code, succ = ist.transfer(styles, code)
            if succ:
                print(new_code)

    elif task == 'count':
        if scope == 'all':
            with open(f'./data/{lang}.jsonl', 'r') as f:
                lines = f.readlines()
                all_mp = {}
                unexpected_codes = []
                tot_num = len(lines)
                print(f"tot_num = {tot_num}")
                for line in tqdm(lines, ncols=100):
                    obj = json.loads(line)
                    if lang == 'c': code = obj['func']
                    elif lang == 'java': code = obj['fixed']
                    elif lang == 'c_sharp': code = obj['code1']
                    sub_map = ist.get_style(code, styles)
                    if len(list(sub_map.values())) == 0 or max(list(sub_map.values())) == 0:
                        unexpected_codes.append(code)
                    for key, val in sub_map.items():
                        if key in all_mp: all_mp[key] += min(val, 1)
                        else: all_mp[key] = min(val, 1)
            
            for key, val in all_mp.items():
                print(f"{key}: {val} [{round(val / tot_num * 100, 2)}%]")

        elif scope == 'one':
            with open(f'./test_code/test.{lang}', 'r') as f:
                code = f.read()
                mp = ist.get_style(code, styles)
                for key, val in mp.items():
                    print(f"{key}: {val}")