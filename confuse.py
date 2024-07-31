from change_program_style import SCTS
from utils import *
import random

class Confuse(SCTS):
    def __init__(self, langauge):
        super().__init__(langauge)

    def confuse_code(self, code):
        operations = []
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        self.remove_comments(AST.root_node, operations)
        code = replace_from_blob(operations, code.encode('utf-8')).decode('utf-8', errors='ignore')

        class_name = []
        operations = []
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        vars = set()
        self.var_rename(AST.root_node ,vars)
        convert_map = {}
        for i, (var, type) in enumerate(vars):
            convert_map[var] = f'{type}_{i}'
            if type == 'c':
                class_name.append(var)
        # self.cvt_var(AST.root_node, convert_map, operations)
        # code = replace_from_blob(operations, code.encode('utf-8')).decode('utf-8', errors='ignore')

        operations = []
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        self.cvt_call(AST.root_node, class_name, operations)
        code = replace_from_blob(operations, code.encode('utf-8')).decode('utf-8', errors='ignore')

        operations = []
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        true_expressions = [x.replace('\n','') for x in open('sample/true.txt', 'r').readlines()]
        self.cvt_if_condition(AST.root_node, true_expressions, operations)
        code = replace_from_blob(operations, code.encode('utf-8')).decode('utf-8', errors='ignore')

        operations = []
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        one_expressions = [x.replace('\n','') for x in open('sample/one.txt', 'r').readlines()]
        self.cvt_const(AST.root_node, one_expressions, operations)
        code = replace_from_blob(operations, code.encode('utf-8')).decode('utf-8', errors='ignore')

        operations = []
        AST = self.parser.parse(bytes(code, encoding='utf-8'))
        self.cvt_string(AST.root_node, operations)
        code = replace_from_blob(operations, code.encode('utf-8')).decode('utf-8', errors='ignore')

        with open('sample/confused.py', 'w', encoding='utf-8') as f:
            f.write(code)

    def remove_comments(self, node, operations):
        if node.type == 'comment':
            operations.append((node.end_byte, node.start_byte))
        for child in node.children:
            self.remove_comments(child, operations)

    def var_rename(self, node, vars):
        if node.type == 'identifier':
            if self.mp(node, ['for_in_clause', 'assignment', 'for_statement']):
                vars.add((text(node), 't'))
            elif 'parameter' in node.parent.type and text(node) not in ['self', 'cls']:
                vars.add((text(node), 't'))
            elif self.mp(node, [['attribute', 'assignment'], ['pattern_list', 'for_statement']]) and text(node) not in ['self', 'cls']:
                vars.add((text(node), 't'))
            elif node.parent.type =='function_definition' and not text(node).startswith("__"):
                vars.add((text(node), 'f'))
            elif node.parent.type =='class_definition':
                vars.add((text(node), 'c'))
        for child in node.children:
            self.var_rename(child, vars)

    def cvt_var(self, node, convert_map, operations):
        if node.type == 'identifier':
            if text(node) in convert_map and not (self.mp(node, [('keyword_argument', 0)]) and text(node) not in convert_map):
                operations.extend([(node.end_byte, node.start_byte), (node.start_byte, convert_map[text(node)])])
        for child in node.children:
            self.cvt_var(child, convert_map, operations)
    
    def cvt_const(self, node, one_expressions, operations):
        if node.type == 'integer':
            random_one = random.choice(one_expressions)
            if text(node) == '1':
                operations.extend([(node.end_byte, node.start_byte), (node.start_byte, f"({random_one})")])
            elif text(node) == '0':
                operations.extend([(node.end_byte, node.start_byte), (node.start_byte, f'(({random_one}) - 1)')])
            elif text(node) == '-1':
                operations.extend([(node.end_byte, node.start_byte), (node.start_byte, f"-({random_one})")])
            else:
                factors = [str(factor) for factor in self.prime_factors(int(text(node)))]
                factors.append(f"({random_one})")
                random.shuffle(factors)
                factors = '*'.join(factors)
                operations.extend([(node.end_byte, node.start_byte), (node.start_byte, f"({factors})")])

        for child in node.children:
            self.cvt_const(child, one_expressions, operations)

    def cvt_string(self, node, operations):
        def decode(str):
            escape_map = {'\\': r'\x5c', '"': r'\x22', "'": r'\x27', 'a': r'\x07', 'b': r'\x08', 'f': r'\x0c', 'n': r'\x0a', 'r': r'\x0d', 't': r'\x09', 'v': r'\x0b', '0': r'\x00', '?': r'\x3f'}
            decoded_str = ''
            i = 0
            while i < len(str):
                if str[i] == '\\' and i + 1 < len(str):
                    if str[i+1] in ['\\', '"', "'", 'a', 'b', 'f', 'n', 'r', 't', 'v', '0', '?']:
                        decoded_str += escape_map[str[i+1]]
                        i += 1
                elif ord(str[i]) > 127:
                    decoded_str += f'\\u{ord(str[i]):04x}'
                else:
                    decoded_str += f'\\x{ord(str[i]):02x}'
                i += 1
            return decoded_str

        if node.type == 'string_content':
            unicode_str = decode(text(node))
            operations.extend([(node.end_byte, node.start_byte), (node.start_byte, f'{unicode_str}')])
        for child in node.children:
            self.cvt_string(child, operations)

    def cvt_call(self, node, class_name, operations):
        if node.type == 'identifier':
            if self.mp(node, ['call', [('attribute', 2), 'call']]) and text(node) not in class_name:
                operations.append((node.end_byte, '.__call__'))
        for child in node.children:
            self.cvt_call(child, class_name, operations)

    def cvt_if_condition(self, node, true_expressions, operations):
        random_true = random.choice(true_expressions)
        if node.type == 'if_statement':
            random_int = random.randint(0, 1)
            if random_int == 1:
                new_condition = f"({text(node.children[1])}) and ({random_true})"
            else:
                if random_true.startswith("not"):
                    new_condition = f"({text(node.children[1])}) or ({random_true.split('not ')[1]})"
                else:
                    new_condition = f"({text(node.children[1])}) or not ({random_true})"
            operations.extend([(node.children[1].end_byte, node.children[1].start_byte), (node.children[1].start_byte, new_condition)])
        elif text(node) == 'True':
            operations.extend([(node.end_byte, node.start_byte), (node.start_byte, random_true)])
        elif text(node) == 'False':
            if random_true.startswith("not"):
                new_condition = f"not ({random_true.split('not ')[1]})"
            else:
                new_condition = f"not ({random_true})"
            operations.extend([(node.end_byte, node.start_byte), (node.start_byte, new_condition)])
        for child in node.children:
            self.cvt_if_condition(child, true_expressions, operations)

    def prime_factors(self, n):
        factors = []
        while n % 2 == 0:
            factors.append(2)
            n = n // 2
        for i in range(3, int(n**0.5) + 1, 2):
            while n % i == 0:
                factors.append(i)
                n = n // i
        if n > 2:
            factors.append(n)
        return factors

    def mp(self, node, parents_list):    # match parent
        for parents in parents_list:
            if isinstance(parents, str):
                if node.parent.type == parents:
                    return True
            if isinstance(parents, tuple):
                if node.parent.type == parents[0] and node.parent.children[parents[1]] == node:
                    return True
            else:
                temp_node = node
                flag = True
                for parent in parents:
                    if not temp_node.parent:
                        flag = False
                        break
                    if isinstance(parent, str) and temp_node.parent.type == parent:
                        temp_node = temp_node.parent
                    elif isinstance(parent, tuple) and temp_node.parent.type == parent[0] and temp_node.parent.children[parent[1]] == temp_node:
                        temp_node = temp_node.parent
                    else:   
                        flag = False
                        break
                if flag:
                    return True
        return False

if __name__ == '__main__':
    confuse = Confuse('python')
    code = open('sample/test.py', 'r', encoding='utf-8').read()
    confuse.confuse_code(code)