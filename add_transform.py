import os
import argparse

def main():
    # 新建转换器，格式为python add_transform --l language --n name
    parser = argparse.ArgumentParser()
    parser.add_argument("--l", required=True, type=str, help="language")
    parser.add_argument("--n", required=True, type=str, help="transform name")
    args = parser.parse_args()
    language = args.l
    name = args.n
    is_empty = False
    if not os.path.exists(language):
        os.mkdir(language)
        is_empty = True
        index = 0
    else:
        files = os.listdir(language)
        index = sorted([int(x[9:].split('_')[0]) for x in files if 'transform' in x])[-1] + 1
        for file in files:
            if name in file:
                return
    with open(f'{language}/transform{index}_{name}.py', 'w') as f:
        f.write(
'''from utils import replace_from_blob, traverse_rec_func, text

\'''==========================匹配========================\'''

\'''==========================替换========================\'''
''')

    is_import = False
    config_num = 0
    new_lines = []
    if is_empty:
        with open(f'{language}/config.py', 'w') as f:
            f.write(f'from .transform{index}_{name} import *\n\n')
            f.write(f'''transformation_operators = {{\n    '{name}': {{\n        \n    }},\n}}''')
    else:
        with open(f'{language}/config.py', 'r') as f:
            lines = f.readlines()
        for line in lines:
            new_lines.append(line)
            if line.strip() == "" and is_import == False:
                is_import = True
                new_lines[-1] = f'from .transform{index}_{name} import *\n'
                new_lines.append('\n')
            if line.strip() == '},':
                config_num += 1
                if config_num == index:
                    new_lines.append(f"    '{name}': {{\n")
                    new_lines.append('        \n')
                    new_lines.append('    },\n')
        with open(f'{language}/config.py', 'w') as f:
            f.write(''.join(new_lines))

if __name__ == '__main__':
    main()