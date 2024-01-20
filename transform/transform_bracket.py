from transform.Core import Core
from ist_utils import text, print_children, get_indent

class Bracket_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
        self.block_type_mapping = {'c': 'compound_statement', 'java': 'block'}
    
    def get_opts(self, node):
        statement_node = None
        for each in node.children:
            if each.type in ['expression_statement', 'return_statement', 'compound_statement', 'break_statement', 'for_statement', 'if_statement', 'while_statement']:
                statement_node = each
        if statement_node is None:
            return
        indent = get_indent(node.start_byte, self.code)
        
        if '\n' not in text(node):
            self.operations.extend([
                (statement_node.start_byte, statement_node.prev_sibling.end_byte),
                (statement_node.start_byte, f" {{\n{(indent + 4) * ' '}"), 
                (statement_node.end_byte, f"\n{indent * ' '}}}")
                ])
        else:
            self.operations.extend([
                (statement_node.prev_sibling.end_byte, f" {{"), 
                (statement_node.end_byte, f"\n{indent * ' '}}}")
                ])

    def check(self, u):
        return self.check_nbracket(u)

    def count(self):
        self.check = self.check_bracket
        self.match_nodes = []
        self.match(self.root)
        self.check = self.check_nbracket
        return len(self.match_nodes)

class NBracket_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
        self.block_type_mapping = {'c': 'compound_statement', 'java': 'block'}

    def get_opts(self, node):
        statement_node = None
        for u in node.children:
            if u.type == self.block_type_mapping[self.lang]:
                statement_node = u
                break
        if statement_node is None:
            return
        contents = text(statement_node)
        new_contents = contents.replace('{', '').replace('}', '').replace('\n', '')
        tmps = []
        for new_content in new_contents.split(';'):
            for i in range(len(new_content)):
                if new_content[i] != ' ':
                    tmps.append(' ' + new_content[i:])
                    break
        indent = get_indent(node.start_byte, self.code)
        new_contents = ', '.join(tmps) + ';\n' + ' '*indent
        self.operations.extend([
            (statement_node.end_byte, statement_node.start_byte),
            (statement_node.start_byte, new_contents)
            ])
    
    def check(self, u):
        return self.check_bracket(u)

    def count(self):
        self.check = self.check_nbracket
        self.match_nodes = []
        self.match(self.root)
        self.check = self.check_bracket
        return len(self.match_nodes)

class If_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check_nbracket(self, u):
        if u.type in ['if_statement', 'else_clause'] and '{' not in text(u):
            return True
        return False
    
    def check_bracket(self, u):
        if u.type in ['if_statement', 'else_clause'] and '{' in text(u):
            count = -1
            for v in u.children:
                if v.type == self.block_type_mapping[self.lang]:
                    count = 0
                    for p in v.children:
                        if p.type in ['expression_statement', 'return_statement', 'compound_statement', 'break_statement', 'for_statement', 'if_statement', 'while_statement']:
                            count += 1
            if -1 < count <= 1:
                return True
        return False

class For_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check_nbracket(self, u):
        if u.type in ['for_statement'] and '{' not in text(u):
            return True
        return False
    
    def check_bracket(self, u):
        if u.type in ['for_statement'] and '{' in text(u):
            count = -1
            for v in u.children:
                if v.type == self.block_type_mapping[self.lang]:
                    count = 0
                    for p in v.children:
                        if p.type in ['expression_statement', 'return_statement', 'compound_statement', 'break_statement', 'for_statement', 'if_statement', 'while_statement']:
                            count += 1
            if -1 < count <= 1:
                return True
        return False

    def count(self):
        self.check = self.check_bracket
        self.match(self.root)
        self.check = self.check_nbracket
        return len(self.match_nodes)

class While_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check_nbracket(self, u):
        if u.type in ['while_statement'] and '{' not in text(u):
            return True
        return False
    
    def check_bracket(self, u):
        if u.type in ['while_statement'] and '{' in text(u):
            count = -1
            for v in u.children:
                if v.type == self.block_type_mapping[self.lang]:
                    count = 0
                    for p in v.children:
                        if p.type in ['expression_statement', 'return_statement', 'compound_statement', 'break_statement', 'for_statement', 'if_statement', 'while_statement']:
                            count += 1
            if -1 < count <= 1:
                return True
        return False

    def count(self):
        self.check = self.check_bracket
        self.match(self.root)
        self.check = self.check_nbracket
        return len(self.match_nodes)

class If_Bracket_Core(Bracket_Core, If_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

class For_Bracket_Core(Bracket_Core, For_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

class While_Bracket_Core(Bracket_Core, While_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

class If_NBracket_Core(NBracket_Core, If_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

class For_NBracket_Core(NBracket_Core, For_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

class While_NBracket_Core(NBracket_Core, While_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)