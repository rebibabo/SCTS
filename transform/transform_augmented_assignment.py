from transform.Core import Core
from ist_utils import text, print_children, get_indent

class Assignment_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
        self.augmented_opts = ['+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '|=', '^=', '~=']
        self.naugmented_opts = ['+', '-', '*', '/', '%', '<<', '>>', '&', '|', '^', '~']

    def check_augmented_assignment(self, u):
        if u.type == 'assignment_expression' and u.child_count == 3 and \
            text(u.children[1]) in self.augmented_opts:
            return True
        return False
    
    def check_naugmented_assignment(self, u):
        if u.type != 'assignment_expression': return False
        main_var = u.children[0]
        calc_expr = u.children[2]
        if len(calc_expr.children) < 3: return False
        if text(calc_expr.children[1]) not in self.naugmented_opts: return False
        if text(main_var) == text(calc_expr.children[0]) or \
            text(main_var) == text(calc_expr.children[2]): return True
        return False

class Augmented_Assignment_Core(Assignment_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, node):
        return self.check_naugmented_assignment(node)
    
    def get_opts(self, node):
        # a = a ? b -> a ?= b
        main_var  = node.children[0]
        calc_expr = node.children[2]
        op = calc_expr.children[1]
        if text(calc_expr.children[0]) == text(main_var):
            new_str = f'{text(main_var)} {text(op)}= {text(calc_expr.children[2])}'
        else:
            new_str = f'{text(main_var)} {text(op)}= {text(calc_expr.children[0])}'
        self.operations.extend([
            (node.end_byte, node.start_byte),
            (node.start_byte, new_str)])
    
    def count(self):
        self.check = self.check_augmented_assignment
        self.match_nodes = []
        self.match(self.root)
        self.check = self.check_naugmented_assignment
        return len(self.match_nodes)
    
class NAugmented_Assignment_Core(Assignment_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, u):
        return self.check_augmented_assignment(u)
    
    def get_opts(self, node):
        # a ?= b -> a = a ? b
        [a, op, b] = [text(x) for x in node.children]
        new_str = f'{a} = {a} {op[:-1]} {b}'
        self.operations.extend([
            (node.end_byte, node.start_byte),
            (node.start_byte, new_str)])
    
    def count(self):
        self.check = self.check_naugmented_assignment
        self.match_nodes = []
        self.match(self.root)
        self.check = self.check_augmented_assignment
        return len(self.match_nodes)