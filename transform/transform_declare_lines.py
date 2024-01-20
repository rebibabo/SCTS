from transform.Core import Core
from ist_utils import text, print_children, get_indent

class Decalare_Line_Core(Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
        self.variable_declaration_mapping = {
            'c': 'declaration', 
            'java': 'local_variable_declaration'
        }
        self.init_declarator_mapping = {
            'c': 'init_declarator',
            'java': 'variable_declarator'
        }
    
    def get_declare_info(self, node):
        # 返回node代码块中所有类型的变量名以及节点字典
        type_ids_dict, type_dec_node = {}, {}
        for child in node.children:
            if child.type == self.variable_declaration_mapping[self.lang]:
                type = text(child.children[0])
                type_ids_dict.setdefault(type, [])
                type_dec_node.setdefault(type, [])
                type_dec_node[type].append(child)
                for each in child.children[1: -1]:
                    if each.type == ',':
                        continue
                    type_ids_dict[type].append(text(each))
        return type_ids_dict, type_dec_node

    def contain_id(self, node, contain):
        # 返回node节点子树中的所有变量名
        if node.child_by_field_name('index'):   # a[i] < 2中的index：i
            contain.add(text(node.child_by_field_name('index')))
        if node.type == 'identifier' and \
            (node.parent.type in self.variable_declaration_mapping[self.lang] or \
             node.parent.type in self.init_declarator_mapping[self.lang]):
            contain.add(text(node))
        for n in node.children:
            self.contain_id(n, contain)

    def get_id_first_line(self, node):
        # 获取所有变量在该node代码块第一次声明和使用的行号
        first_declare, first_use = {}, {}
        for child in node.children:
            if child.type == 'declaration':
                dec_id = set()
                self.contain_id(child, dec_id)
                for each in dec_id:
                    if each not in first_declare.keys():
                        first_declare[each] = child.start_point[0]
            # elif child.type not in ['if_statement', 'for_statement', 'else_clause', 'while_statement']: # 不考虑复合语句里面的临时变量名
            else:
                use_id = set()
                self.contain_id(child, use_id)
                for each in use_id:
                    if each not in first_use.keys():
                        first_use[each] = child.start_point[0]
        return first_declare, first_use

    def check_match_lines_merge(self, node):
        # int a, b=0;
        if node.type == self.variable_declaration_mapping[self.lang]:
            ids = set()
            self.contain_id(node, ids)
            return len(ids) > 1
        return False

    def check_match_lines_split(self, node):
        # int a; \n int b=0;
        type_list = set()
        for child in node.children:
            if child.type == self.variable_declaration_mapping[self.lang]:
                type = text(child.children[0])
                if type in type_list:
                    return True
                type_list.add(type)
        return False

class Decalare_Line_Merge_Core(Decalare_Line_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, u):
        return self.check_match_lines_split(u)

    def get_opts(self, node):
        # int a; int b; -> int a, b;
        opts = []
        indent = get_indent(node.children[1].start_byte, self.code)
        type_ids_dict, type_dec_node = self.get_declare_info(node)
        for type, ids in type_ids_dict.items():
            if len(ids) > 1:
                start_byte = type_dec_node[type][0].start_byte
                for node in type_dec_node[type]:
                    opts.append((node.end_byte, node.start_byte))
                str = f"{type} {', '.join(type_ids_dict[type])};"
                opts.append((start_byte, str))
        self.operations.extend(opts)
    
    def count(self):
        check_func = self.check
        self.check = self.check_match_lines_merge
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Decalare_Line_Split_Core(Decalare_Line_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check(self, u):
        return self.check_match_lines_merge(u)

    def get_opts(self, node):
        # int a, b; -> int a; int b;
        type = text(node.children[0])
        opts = [(node.end_byte, node.start_byte)]
        indent = get_indent(node.start_byte, self.code)
        for i, child in enumerate(node.children[1: -1]):
            if child.type == ',':
                continue
            opts.append((node.start_byte, f"\n{indent * ' '}{type} {text(child)};"))
        self.operations.extend(opts)
    
    def count(self):
        check_func = self.check
        self.check = self.check_match_lines_split
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)