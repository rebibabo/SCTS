from transform.Core import Core
from ist_utils import text, print_children, get_indent

class Loop_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
        self.declaration_mapping = {
            'c': 'declaration', 
            'java': 'local_variable_declaration', 
            'c_sharp': 'local_variable_declaration'
        }
        self.block_mapping = {
            'c': 'compound_statement', 
            'java': 'block', 
            'c_sharp': 'block'
        }

    def get_for_info(self, node):
        # 提取for循环的abc信息，for(a;b;c)以及后面接的语句
        i, abc = 0, [None, None, None, None]
        for child in node.children:
            if child.type in [';', ')', self.declaration_mapping[self.lang]]:
                if child.type == self.declaration_mapping[self.lang]:
                    abc[i] = child
                if child.prev_sibling.type not in ['(', ';']:
                    abc[i] = child.prev_sibling
                i += 1
            if child.prev_sibling and child.prev_sibling.type == ')' and i == 3:
                abc[3] = child
        return abc

    def contain_id(self, node, contain):
        # 返回node节点子树中的所有变量名
        if node.child_by_field_name('index'):   # a[i] < 2中的index：i
            contain.add(text(node.child_by_field_name('index')))
        if node.type == 'identifier' and node.parent.type not in ['subscript_expression', 'call_expression']:   # a < 2中的a
            contain.add(text(node))
        if not node.children:
            return
        for n in node.children:
            self.contain_id(n, contain)
    
    def check_for(self, node):
        if node.type == 'for_statement':
            return True
        return False

    def check_while(self, node):
        if node.type == 'while_statement':
            return True
        return False

    def check_dowhile(self, node):
        if node.type == 'do_statement' and 'while' in text(node):
            return True
        return False
    
class Loop_Type_Core(Loop_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, node):
        return self.check_for(node) or self.check_while(node) or self.check_dowhile(node)

class Loop_Type_For_Core(Loop_Type_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        opts = []
        if node.type == 'while_statement':
            # for(a;b;c)
            a = b = c = None
            if self.lang == 'c_sharp':
                b = node.children[4].children[1]
            else:
                b = node.children[1].children[1]
            id, prev_id, clause_id = set(), set(), set()
            self.contain_id(b, id)
            if len(id) == 0:
                return
            id = list(id)[0]
            prev = node.prev_sibling
            if prev.type == self.declaration_mapping[self.lang] and prev.child_count == 3 or prev.type == 'expression_statement' and prev.children[0].type in ['update_expression', 'assignment_expression']:
                self.contain_id(node.prev_sibling, prev_id)
            if len(prev_id):
                for u in list(prev_id):
                    if u in id:    # 如果前面一句是声明或者赋值并且和循环的id一样
                        a = node.prev_sibling
            for u in node.children[2].children[1: -1]:
                if u.type == 'expression_statement' and u.parent.type not in ['if_statement', 'for_statement', 'else_clause', 'while_statement']:  # 是i++,i+=1这种表达式，且不能在从句里面
                    if u.children[0].type in ['update_expression', 'assignment_expression']:
                        self.contain_id(u.children[0], clause_id)
                        if len(clause_id) == 1 and id in clause_id: # 从句里面如果有++或者赋值运算并且变量名为id，则添加c
                            c = u
                            break
            opts = [(node.children[1].end_byte, node.children[0].start_byte)]
            if a:
                opts.append((a.end_byte, a.prev_sibling.end_byte))
            if c:
                opts.append((c.end_byte, c.prev_sibling.end_byte))
            text_a = text(a) if a else ''
            for_str = f"for({text_a}{'; ' if ';' not in text_a else ' '}{text(b)}; {text(c).replace(';', '') if c else ''})"
            opts.append((node.start_byte, for_str))
        elif node.type == 'do_statement':
            # for(a;b;c)
            a = b = c = None
            for v in node.children:
                if v.type == 'parenthesized_expression':
                    b = v.children[1]
                    break
            id, prev_id, clause_id = set(), set(), set()
            self.contain_id(b, id)
            if len(id) == 0:
                return
            id = list(id)[0]
            prev = node.prev_sibling
            if prev.type == self.declaration_mapping[self.lang] and prev.child_count == 3 or prev.type == 'expression_statement' and prev.children[0].type in ['update_expression', 'assignment_expression']:
                self.contain_id(node.prev_sibling, prev_id)
            if len(prev_id):
                for u in list(prev_id):
                    if u in id:    # 如果前面一句是声明或者赋值并且和循环的id一样
                        a = node.prev_sibling
            for u in node.children[1].children[1: -1]:
                if u.type == 'expression_statement' and u.parent.type not in ['if_statement', 'for_statement', 'else_clause', 'while_statement']:  # 是i++,i+=1这种表达式，且不能在从句里面
                    if u.children[0].type in ['update_expression', 'assignment_expression']:
                        self.contain_id(u.children[0], clause_id)
                        if len(clause_id) == 1 and id in clause_id: # 从句里面如果有++或者赋值运算并且变量名为id，则添加c
                            c = u
                            break
            opts = [(node.children[0].end_byte, node.children[0].start_byte),
                (node.children[4].end_byte, node.children[2].start_byte)]
            if a:
                opts.append((a.end_byte, a.prev_sibling.end_byte))
            if c:
                opts.append((c.end_byte, c.prev_sibling.end_byte))
            text_a = text(a) if a else ''
            for_str = f"for({text_a}{'; ' if ';' not in text_a else ' '}{text(b)}; {text(c).replace(';', '') if c else ''})"
            opts.append((node.start_byte, for_str))
        self.operations.extend(opts)

    def count(self):
        check_func = self.check
        self.check = self.check_for
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Loop_Type_While_Core(Loop_Type_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def get_opts(self, node):
        # a while(b) c
        opts = []
        if node.type == 'for_statement':
            opts, add_bracket = [], None
            abc = self.get_for_info(node)
            child_index = 3 + (4 - abc.count(None)) - (abc[0] is not None and abc[0].type == self.declaration_mapping[self.lang])
            opts = [(node.children[child_index].end_byte, node.children[0].start_byte - node.children[child_index].end_byte)]    # 删除for(a;b;c)
            if abc[0] is not None:  # 如果有a
                indent = get_indent(node.start_byte, self.code)
                if abc[0].type != self.declaration_mapping[self.lang]:
                    opts.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
                else:
                    opts.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
            if abc[2] is not None:  # 如果有c
                if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                    last_expression_node = abc[3].children[-2]
                else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                    last_expression_node = abc[3]
                indent = get_indent(last_expression_node.start_byte, self.code)
                opts.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
            while_str = f"while({text(abc[1]) if abc[1] else ''})"
            opts.append((node.children[0].start_byte, while_str))
            if add_bracket:
                opts.extend(add_bracket)
        elif node.type == 'do_statement':
            condition_node = node.children[3]
            opts = [(node.children[0].end_byte, node.children[0].start_byte),
                    (node.children[4].end_byte, node.children[2].start_byte),
                    (node.children[0].start_byte, f"whlie{text(condition_node)}")]
        self.operations.extend(opts)

    def count(self):
        check_func = self.check
        self.check = self.check_while
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Loop_Type_DoWhile_Core(Loop_Type_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        opts = []
        if node.type == 'for_statement':
            # a while(b) c
            opts, add_bracket = [], None
            abc = self.get_for_info(node)
            child_index = 3 + (4 - abc.count(None)) - (abc[0] is not None and abc[0].type == self.declaration_mapping[self.lang])
            opts = [(node.children[child_index].end_byte, node.children[0].start_byte - node.children[child_index].end_byte)]    # 删除for(a;b;c)
            if abc[0] is not None:  # 如果有a
                indent = get_indent(node.start_byte, self.code)
                if abc[0].type != self.declaration_mapping[self.lang]:
                    opts.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
                else:
                    opts.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
            if abc[2] is not None:  # 如果有c
                if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                    last_expression_node = abc[3].children[-2]
                else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                    last_expression_node = abc[3]
                indent = get_indent(last_expression_node.start_byte, self.code)
                opts.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
            while_str = f"while({text(abc[1]) if abc[1] else ''})"
            do_str = "do"
            opts.append((node.children[0].start_byte, do_str))
            opts.append((node.end_byte, while_str))
            if add_bracket:
                opts.extend(add_bracket)
        
        elif node.type == 'while_statement':
            condition_node = node.children[1]
            opts = [(node.children[1].end_byte, node.children[0].start_byte),
                    (node.children[0].start_byte, "do"),
                    (node.children[2].end_byte, f"while{text(condition_node)}")]
        self.operations.extend(opts)

    def count(self):
        check_func = self.check
        self.check = self.check_dowhile
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)
    

class Loop_Inf_Core(Loop_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

class Loop_While_Inf_Core(Loop_Inf_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
        self.opposite = {
            '==': '!=', '!=': '==', 
            '>': '<=',  '<=': '>',
            '<': '>=',  '>=': '<',
            '&&': '||', '||': '&&'}
    
    def check(self, node):
        return self.check_while(node)

    def get_opts(self, node):
        res = []
        compound_node = node.children[-1]
        indent = get_indent(compound_node.children[1].start_byte, self.code)
        mp = {}
        def opp_dfs(u):
            while len(u.children) >= 2 and text(u.children[0]) == '(':
                u = u.children[1]
            if len(u.children) == 0:
                mp[text(u)] = '!' + text(u)
                return
            if '&&' not in text(u) and '||' not in text(u) and len(u.children) == 3:
                if text(u.children[1]) in self.opposite:
                    mp[text(u)] = text(u.children[0]) + self.opposite[text(u.children[1])] + text(u.children[2])
                else:
                    mp[text(u)] = '!' + text(u)
                return
            elif len(u.children) == 2 and text(u.children[0]) == '!':
                mp[text(u)] = text(u.children[1])
                return
            elif len(u.children) == 3:
                try:
                    mp[text(u)] = text(u.children[0]) + self.opposite[text(u.children[1])] + text(u.children[2])
                except:
                    mp[text(u)] = '!' + text(u)
            
            for v in u.children:
                opp_dfs(v)
        conditional_node = node.children[1].children[1]
        opp_dfs(conditional_node)
        conditional_str = text(conditional_node)
        for key, val in mp.items():
            conditional_str = conditional_str.replace(key, val)
        
        break_str = f"\n{' '*indent}if({conditional_str}) break;"
        res.append((compound_node.children[0].start_byte+1, break_str))

        res.append((conditional_node.end_byte, conditional_node.start_byte))
        res.append((conditional_node.start_byte, 'true'))
        self.operations.extend(res)

    