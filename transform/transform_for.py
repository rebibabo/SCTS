from transform.Core import Core
from ist_utils import text, print_children, get_indent

class For_Update_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check_left(self, node):
        # ++i or --i
        if node.type in ['update_expression']:
            if node.parent.type not in ['subscript_expression', 'argument_list', 'assignment_expression']:
                # 不是a[++i] 不是*p(++i)不是a=++i
                if text(node.children[0]) in ['--', '++']:
                    return True
        return False

    def check_right(self, node):
        # i++ or i--
        if node.type in ['update_expression']:
            if node.parent.type not in ['subscript_expression', 'argument_list', 'assignment_expression']:
                # 不是a[i++] 不是*p(i++)不是a=i++
                if text(node.children[1]) in ['--', '++']:
                    return True

    def check_augmented(self, node):
        # a += 1 or a -= 1
        if node.type == 'assignment_expression':
            if node.child_count >= 2 and \
                text(node.children[1]) in ['+=', '-='] and \
                text(node.children[2]) == '1':
                    return True

    def check_assignment(self, node):
        # a = a ? 1
        if node.type == 'assignment_expression':
            left_param = node.children[0].text
            if node.children[2].children:
                right_first_param = node.children[2].children[0].text
                if len(node.children[2].children) > 2:
                    if text(node.children[2].children[1]) in ['+', '-'] and \
                        text(node.children[2].children[2]) == '1':
                            return left_param == right_first_param

class Left_Uqdate_Core(For_Update_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, u):
        return self.check_right(u) or self.check_assignment(u) or self.check_augmented(u)

    def get_opts(self, node):
        # ++i
        opts = []
        if self.check_right(node):
            temp_node = node.children[1]
            opts = [(temp_node.end_byte, temp_node.start_byte), 
                    (node.start_byte, text(temp_node))]
        if self.check_augmented(node):
            temp_node = node.children[0]
            op = text(node.children[1])[0]
            opts = [(node.end_byte, temp_node.end_byte),
                    (temp_node.start_byte, op * 2)]
        if self.check_assignment(node):
            left_param = text(node.children[0])
            op = text(node.children[2].children[1])
            opts = [(node.end_byte, node.start_byte),
                    (node.start_byte, f"{op*2}{left_param}")]
        self.operations.extend(opts)
    
    def count(self):
        check_func = self.check
        self.check = self.check_left
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Right_Uqdate_Core(For_Update_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, u):
        return self.check_left(u) or self.check_assignment(u) or self.check_augmented(u)

    def get_opts(self, node):
        # i++
        opts = []
        if self.check_left(node):
            temp_node = node.children[0]
            opts = [(temp_node.end_byte, temp_node.start_byte), 
                    (node.end_byte, text(temp_node))]
        if self.check_augmented(node):
            temp_node = node.children[0]
            op = text(node.children[1])[0]
            opts = [(node.end_byte, temp_node.end_byte),
                    (temp_node.end_byte, op * 2)]
        if self.check_assignment(node):
            left_param = text(node.children[0])
            op = text(node.children[2].children[1])
            opts = [(node.end_byte, node.start_byte),
                    (node.start_byte, f"{left_param}{op*2}")]
        self.operations.extend(opts)
    
    def count(self):
        check_func = self.check
        self.check = self.check_right
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Assignment_Uqdate_Core(For_Update_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, u):
        return self.check_left(u) or self.check_right(u) or self.check_augmented(u)

    def get_opts(self, node):
        # i = i + 1
        opts = []
        if self.check_left(node):
            op = text(node.children[0])[0]
            param = text(node.children[1])
            opts = [(node.end_byte, node.start_byte), 
                    (node.start_byte, f"{param} = {param} {op} 1")]
        if self.check_right(node):
            op = text(node.children[1])[0]
            param = text(node.children[0])
            opts = [(node.end_byte, node.start_byte), 
                    (node.start_byte, f"{param} = {param} {op} 1")]
        if self.check_augmented(node):
            param = text(node.children[0])
            op = text(node.children[1])[0]
            opts = [(node.end_byte, node.start_byte),
                    (node.start_byte, f"{param} = {param} {op} 1")]
        
        self.operations.extend(opts)

    def count(self):
        check_func = self.check
        self.check = self.check_assignment
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Augmented_Uqdate_Core(For_Update_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, u):
        return self.check_left(u) or self.check_right(u) or self.check_assignment(u)
    
    def get_opts(self, node):
        # i += 1
        opts = []
        if self.check_left(node):
            op = text(node.children[0])[0]
            param = text(node.children[1])
            opts = [(node.end_byte, node.start_byte), 
                    (node.start_byte, f"{param} {op}= 1")]
        if self.check_right(node):
            op = text(node.children[1])[0]
            param = text(node.children[0])
            opts = [(node.end_byte, node.start_byte), 
                    (node.start_byte, f"{param} {op}= 1")]
        if self.check_assignment(node):
            param = text(node.children[0])
            op = text(node.children[2].children[1])
            opts = [(node.end_byte, node.start_byte),
                    (node.start_byte, f"{param} {op}= 1")]
        self.operations.extend(opts)
    
    def count(self):
        check_func = self.check
        self.check = self.check_augmented
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class For_Format_Core(Core):
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

    def check(self, node):
        if node.type == 'for_statement':
            return True

class For_Format_OBC_Core(For_Format_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def get_opts(self, node):
        # a for(;b;c)
        abc = self.get_for_info(node)
        indent = get_indent(node.start_byte, self.code)
        opts = []
        if abc[0] is not None:  # 如果有a
            if abc[0].type != self.declaration_mapping[self.lang]:    
                opts = [(abc[0].end_byte, abc[0].start_byte),
                        (node.start_byte, text(abc[0]) + f';\n{indent * " "}')]
            else:   # 如果是int a, b在for循环里面
                opts = [(abc[0].end_byte - 1, abc[0].start_byte),
                        (node.start_byte, text(abc[0]) + f'\n{indent * " "}')]
        self.operations.extend(opts)

class For_Format_AOC_Core(For_Format_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        # for(a;;c) if b break
        opts, add_bracket = [], None
        abc = self.get_for_info(node)
        if abc[1] is not None:  # 如果有b
            opts.append((abc[1].end_byte, abc[1].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                first_expression_node = abc[3].children[1]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                first_expression_node = abc[3]
            indent = get_indent(first_expression_node.start_byte, self.code)
            opts.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
            if add_bracket:
                opts.extend(add_bracket)
        self.operations.extend(opts)

class For_Format_ABO_Core(For_Format_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        # for(a;b;) c
        opts, add_bracket = [], None
        abc = self.get_for_info(node)   
        if abc[2] is not None:  # 如果有c
            opts.append((abc[2].end_byte, abc[2].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                last_expression_node = abc[3].children[-2]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                last_expression_node = abc[3]
            indent = get_indent(last_expression_node.start_byte, self.code)
            opts.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
            if add_bracket:
                opts.extend(add_bracket)
        self.operations.extend(opts)

class For_Format_AOO_Core(For_Format_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def get_opts(self, node):
        # for(a;;) if b break c
        opts, add_bracket = [], None
        abc = self.get_for_info(node)
        if abc[1] is not None:  # 如果有b
            opts.append((abc[1].end_byte, abc[1].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                first_expression_node = abc[3].children[1]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                first_expression_node = abc[3]
            indent = get_indent(first_expression_node.start_byte, self.code)
            opts.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
        if abc[2] is not None:  # 如果有c
            opts.append((abc[2].end_byte, abc[2].start_byte))
            if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                last_expression_node = abc[3].children[-2]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                last_expression_node = abc[3]
            indent = get_indent(last_expression_node.start_byte, self.code)
            opts.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
        if add_bracket:
            opts.extend(add_bracket)
        self.operations.extend(opts)

class For_Format_OBO_Core(For_Format_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        # a for(;b;) c
        opts, add_bracket = [], None
        abc = self.get_for_info(node)
        if abc[0] is not None:  # 如果有a
            indent = get_indent(node.start_byte, self.code)
            if abc[0].type != self.declaration_mapping[self.lang]:
                opts.append((abc[0].end_byte, abc[0].start_byte))
                opts.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
            else:
                opts.append((abc[0].end_byte - 1, abc[0].start_byte))
                opts.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))  
        if abc[2] is not None:  # 如果有c
            opts.append((abc[2].end_byte, abc[2].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                last_expression_node = abc[3].children[-2]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                last_expression_node = abc[3]
            indent = get_indent(last_expression_node.start_byte, self.code)
            opts.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
        if add_bracket:
            opts.extend(add_bracket)
        self.operations.extend(opts)

class For_Format_OOC_Core(For_Format_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        # a for(;;c) if b break
        opts, add_bracket = [], None
        abc = self.get_for_info(node)
        if abc[0] is not None:  # 如果有a
            indent = get_indent(node.start_byte, self.code)
            if abc[0].type != self.declaration_mapping[self.lang]:
                opts.append((abc[0].end_byte, abc[0].start_byte))
                opts.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
            else:
                opts.append((abc[0].end_byte - 1, abc[0].start_byte))
                opts.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
        if abc[1] is not None:  # 如果有b
            opts.append((abc[1].end_byte, abc[1].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                first_expression_node = abc[3].children[1]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                first_expression_node = abc[3]
            indent = get_indent(first_expression_node.start_byte, self.code)
            opts.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
        if add_bracket:
            opts.extend(add_bracket)
        self.operations.extend(opts)

class For_Format_OOO_Core(For_Format_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def get_opts(self, node):
        # a for(;;;) if break b c
        opts, add_bracket = [], None
        abc = self.get_for_info(node)
        if abc[0] is not None:  # 如果有a
            indent = get_indent(node.start_byte, self.code)
            if abc[0].type != self.declaration_mapping[self.lang]:
                opts.append((abc[0].end_byte, abc[0].start_byte))
                opts.append((node.start_byte, text(abc[0]) + f';\n{indent * " "}'))
            else:
                opts.append((abc[0].end_byte - 1, abc[0].start_byte))
                opts.append((node.start_byte, text(abc[0]) + f'\n{indent * " "}'))
        if abc[1] is not None:  # 如果有b
            opts.append((abc[1].end_byte, abc[1].start_byte))
            if abc[3] is None:
                return
            if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                first_expression_node = abc[3].children[1]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                first_expression_node = abc[3]
            indent = get_indent(first_expression_node.start_byte, self.code)
            opts.append((first_expression_node.start_byte, f"if ({text(abc[1])})\n{(indent + 4) * ' '}break;\n{indent * ' '}"))
        if abc[2] is not None:  # 如果有c
            opts.append((abc[2].end_byte, abc[2].start_byte))
            if abc[3].type == self.block_mapping[self.lang]:     # 复合语句在第一句插入if b break
                last_expression_node = abc[3].children[-2]
            else:       # 如果是单行，后面加上了花括号，在就在expression的开始位置插入
                last_expression_node = abc[3]
            indent = get_indent(last_expression_node.start_byte, self.code)
            opts.append((last_expression_node.end_byte, f"\n{indent * ' '}{text(abc[2])};"))
        if add_bracket:
            opts.extend(add_bracket)
        self.operations.extend(opts)
    