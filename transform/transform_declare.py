from transform.Core import Core
from ist_utils import text, print_children, get_indent

class Decalare_Core(Core):
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
        self.block_mapping = {
            'c': 'compound_statement',
            'java': 'block'}
    
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
        if node.type == 'identifier':
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

class Decalare_Position_Core(Decalare_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check_nfirst(self, node):
        # 定义变量没有集中在前几行
        is_first_dec = True
        if node.type == self.block_mapping[self.lang]:
            for child in node.children[1: -1]:
                if child.type != self.variable_declaration_mapping[self.lang]:
                    if is_first_dec == True:
                        is_first_dec = False
                if child.type == self.variable_declaration_mapping[self.lang] and is_first_dec == False:
                    return True
        return False

    def check_ntemp(self, node):
        # 定义变量没有在第一次使用的上一行
        if node.type == self.block_mapping[self.lang]:
            first_declare, first_use = self.get_id_first_line(node)
            for id, dec in first_declare.items():
                if id in first_use and first_use[id] != dec + 1:
                    return True
        return False

class Decalare_Position_Temp(Decalare_Position_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check(self, u):
        return self.check_ntemp(u)

    def get_opts(self, node):
        # 将变量名声明的位置放在第一次使用该变量名的前一行
        first_declare, first_use = self.get_id_first_line(node)
        declare_node, temp_id = [], []
        for id, dec in first_declare.items():
            if id in first_use and first_use[id] != dec + 1:
                temp_id.append(id)
        id_type_dict = {}
        for child in node.children:
            if child.type == self.variable_declaration_mapping[self.lang]:
                type = text(child.children[0])
                for each in child.children[1: -1]:
                    if each.type not in [',', ';']:
                        id_type_dict[text(each)] = type
                        if text(each) in temp_id and child not in declare_node:
                            declare_node.append(child)
        opts = []
        for each in declare_node:
            # 先判断node里面的所有id是否都在temp_id，如果是，则要删除整行，否则只删除部分id
            temp_id_node = []
            delete_all_line = True
            type = text(each.children[0])
            for ch in each.children[1: -1]:
                if ch.type not in [',', ';']:
                    if text(ch) not in temp_id:
                        delete_all_line = False
                    else:
                        temp_id_node.append(ch)
            # 先删除不在最开始使用该id前一行声明的ids
            if delete_all_line == False:
                # 删除该declare中的id
                for id_node in temp_id_node:
                    if id_node.next_sibling.next_sibling:  # 如果是int a, b, c;这里的a,b不是最后一个元素
                        next_node = id_node.next_sibling.next_sibling
                        opts.append((next_node.start_byte, id_node.start_byte))
                    elif id_node.next_sibling and id_node.next_sibling.type == ';':   # 如果是c这样的最后一个元素
                        prev_node = id_node.prev_sibling
                        opts.append((id_node.end_byte, prev_node.start_byte))
            else:   # 删除一整行
                prev_node = each.prev_sibling
                opts.append((each.end_byte, prev_node.end_byte))
        # 再在temp_id的所有第一次使用前的一行插入
        line_type_id_dict = {}  # 行号， 类型， 变量名
        for id in temp_id:
            if id in id_type_dict.keys():
                type = id_type_dict[id]
                line = first_use[id]
                line_type_id_dict.setdefault(line, {})
                line_type_id_dict[line].setdefault(type, [])
                line_type_id_dict[line][type].append(id)
        for line in line_type_id_dict:
            for type in line_type_id_dict[line]:
                ids = line_type_id_dict[line][type]
                # 找到line的对应行的位置
                for child in node.children:
                    if child.start_point[0] == line:
                        indent = get_indent(child.start_byte, self.code)
                        if len(ids) == 1:   # 如果改行改类型变量插入的只有一个
                            dec_str = f"{type} {ids[0]};\n{indent * ' '}"
                        else:       # 如果有多个
                            dec_str = f"{type} {', '.join(ids)};\n{indent * ' '}"
                        opts.append((child.start_byte, dec_str))
        self.operations.extend(opts)

    def count(self):
        check_func = self.check
        self.check = self.check_nfirst
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Decalare_Position_First(Decalare_Position_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check(self, u):
        return self.check_nfirst(u)
    
    def get_opts(self, node):
        print(text(node))
        # 把变量名声明的位置都放在最前面
        opts = []
        type_ids_dict, type_dec_node = self.get_declare_info(node)
        indent = get_indent(node.children[1].start_byte, self.code)
        start_byte = len(self.code)
        for type, node in type_dec_node.items():
            for each in node:
                opts.append((each.end_byte, each.start_byte))
                start_byte = min(start_byte, each.start_byte)
        declare_list = []
        for i, (type, ids) in enumerate(type_ids_dict.items()):
            if i == 0:
                declare_list.append(f"{type} {', '.join(ids)};")
            else:
                declare_list.append(f"{indent * ' '}{type} {', '.join(ids)};")
        opts.append((start_byte, '\n'.join(declare_list)))
        self.operations.extend(opts)
    
    def count(self):
        check_func = self.check
        self.check = self.check_ntemp
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)
    
class Decalare_Line_Core(Decalare_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

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

class Decalare_Assign_Core(Decalare_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
        self.declaration_mapping = {
            'c': 'declaration',
            'java': 'local_variable_declaration',
            'c_sharp': 'local_declaration_statement'
        }
        self.init_declarator_mapping = {
            'c': 'init_declarator',
            'java': 'variable_declarator',
            'c_sharp': 'variable_declaration'
        }

    def check_assign_merge(self, node):
        if node.type == self.declaration_mapping[self.lang]:
                for child in node.children:
                    if child.type == self.init_declarator_mapping[self.lang]:
                        return True
        return False
    
    def check_assign_split(self, node):
        if node.type == self.declaration_mapping[self.lang]:
                for child in node.children:
                    if child.type == self.init_declarator_mapping[self.lang] and len(child.children) == 3:
                        return False
                return True
        return False
    
class Decalare_Assign_Split_Core(Decalare_Assign_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)
    
    def check(self, node):
        return self.check_assign_merge(node)

    def get_opts(self, node):
        opts = []
        if self.lang == 'c':
            for child in node.children:
                if child.type == self.init_declarator_mapping[self.lang]:
                    declarator = child.child_by_field_name('declarator')
                    value = child.child_by_field_name('value')
                    indent = get_indent(node.start_byte, self.code)
                    opts.append((value.end_byte, declarator.end_byte))
                    opts.append((node.end_byte, f"\n{indent*' '}{text(declarator)} = {text(value)};"))
        
        elif self.lang == 'c_sharp':
            for child in node.children:
                if child.type == self.init_declarator_mapping[self.lang]:
                    for u in child.children:
                        if u.type == 'variable_declarator':
                            declarator = u.children[0]
                            if len(u.children) < 2: return
                            if len(u.children[1].children) < 2: return
                            value = u.children[1].children[1]
                            indent = get_indent(node.start_byte, self.code)
                            opts.append((value.end_byte, declarator.end_byte))
                            opts.append((node.end_byte, f"\n{indent*' '}{text(declarator)} = {text(value)};"))
        
        elif self.lang == 'java':
            for v in node.children:
                if v.type == self.init_declarator_mapping[self.lang] and v.child_count >= 3:
                    declarator = v.children[0]
                    value = v.children[2]
                    indent = get_indent(node.start_byte, self.code)
                    opts.append((value.end_byte, declarator.end_byte))
                    opts.append((node.end_byte, f"\n{indent*' '}{text(declarator)} = {text(value)};"))

        self.operations.extend(opts)

    def count(self):
        check_func = self.check
        self.check = self.check_assign_split
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)

class Decalare_Assign_Merge_Core(Decalare_Assign_Core):
    def __init__(self, root, lang):
        super().__init__(root, lang)

    def check(self, node):
        return self.check_assign_split(node)

    def get_opts(self, node):
        # int i; i = 0; -> int i = 0;
        type_node = node.children[0]
        var_node = node.children[1]
        assign_nodes = []

        def find_val_node(u):
            if len(assign_nodes) >= 1:
                return
            if u.type == 'assignment_expression' and text(u.children[0]) == text(var_node):
                assign_nodes.append(u)
                return
            for v in u.children:
                find_val_node(v)
        find_val_node(node.parent)
        
        if len(assign_nodes) == 0:
            return
        assign_node = assign_nodes[0]
        val_node = assign_node.children[2]

        res =  [(node.end_byte, node.start_byte),
                (assign_node.end_byte+1, assign_node.start_byte),
                (node.start_byte, f"{text(type_node)} {text(var_node)} = {text(val_node)};")]

        self.operations.extend(res)

    def count(self):
        check_func = self.check
        self.check = self.check_assign_merge
        self.match_nodes = []
        self.match(self.root)
        self.check = check_func
        return len(self.match_nodes)