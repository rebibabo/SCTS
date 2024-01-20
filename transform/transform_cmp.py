from transform.Core import Core
from ist_utils import text, print_children, get_indent

class Cmp_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check(self, u):
        if u.type == 'binary_expression' and \
            text(u.children[1]) in ['>', '>=', '<', '<=', '==', '!='] and \
            len(u.children) == 3:
            return True
        return False

    def check_bigger(self, u):
        if u.type == 'binary_expression' \
                and text(u.children[1]) in ['>', '>=']:
            return True
        return False

    def check_smaller(self, u):
        if u.type == 'binary_expression' \
                and text(u.children[1]) in ['<', '<=']:
            return True
        return False
    
    def check_equal(self, u):
        if u.type == 'binary_expression' \
                and text(u.children[1]) in ['==']:
            return True
        return False

    def check_nequal(self, u):
        if u.type == 'binary_expression' \
                and text(u.children[1]) in ['!=']:
            return True
        return False
    
class Bigger_Core(Cmp_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        [a, op, b] = [text(x) for x in node.children]
        if op in ['>=', '>']: return
        if op in ['<=', '<']:
            reverse_op_dict = {'<':'>', '<=':'>='}
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{b} {reverse_op_dict[op]} {a}')])
        if op in ['==']:
            # a >= b && b >= a
            return self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} >= {b} && {b} >= {a}')])
        if op in ['!=']:
            # a > b || b > a
            return self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} > {b} || {b} > {a}')])
    
    def count(self):
        check_func = self.check
        self.check = self.check_bigger
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Smaller_Core(Cmp_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        [a, op, b] = [text(x) for x in node.children]
        if op in ['<=', '<']: return
        if op in ['>=', '>']:
            reverse_op_dict = {'>':'<', '>=':'<='}
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{b} {reverse_op_dict[op]} {a}')])
        if op in ['==']:
            # b <= a && a <= b
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} <= {b} && {b} <= {a}')])
        if op in ['!=']:
            # a < b || b < a
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} < {b} || {b} < {a}')])
    
    def count(self):
        check_func = self.check
        self.check = self.check_smaller
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)
    
class Equal_Core(Cmp_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        [a, op, b] = [text(x) for x in node.children]
        if op in ['==']: return
        if op in ['<=']:
            # a < b || a == b
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} < {b} || {a} == {b}')])
        if op in ['<']:
            # !(b < a || a == b)
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'!({b} < {a} || {a} == {b})')])
        if op in ['>=']:
            # a > b || a == b
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} > {b} || {a} == {b}')])
        if op in ['>']:
            # !(b > a || a == b)
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'!({b} > {a} || {a} == {b})')])
        if op in ['!=']:
            # !(a == b)
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'!({a} == {b})')])
    
    def count(self):
        check_func = self.check
        self.check = self.check_equal
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class NEqual_Core(Cmp_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        [a, op, b] = [text(x) for x in node.children]
        if op in ['!=']: return
        if op in ['<=']:
            # !(b < a && a != b)
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'!({b} < {a} && {a} != {b})')])
        if op in ['<']:
            # (a < b && a != b)
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} < {b} && {a} != {b}')])
        if op in ['>=']:
            # !(b > a && a != b)
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'!({b} > {a} && {a} != {b})')])
        if op in ['>']:
            # a < b && a != b
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} < {b} && {a} != {b}')])
        if op in ['==']:
            # a != b
            self.operations.extend([
                (node.end_byte, node.start_byte), 
                (node.start_byte, f'{a} != {b}')])
    
    def count(self):
        check_func = self.check
        self.check = self.check_nequal
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)