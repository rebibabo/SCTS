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
