import os
from graphviz import Digraph
from tree_sitter import Parser, Language
import html

def get_for_info(node):
    # 提取for循环的abc信息，for(a;b;c)以及后面接的语句
    i, abc = 0, [None, None, None]
    for child in node.children:
        if child.type in [';', ')', 'declaration']:
            if child.type == 'declaration':
                abc[i] = child
            if child.prev_sibling.type not in ['(', ';']:
                abc[i] = child.prev_sibling
            i += 1
    return abc

#<(RETURN,return 0;,return 0;)<SUB>5</SUB>>
def get_node_info_ast(node, is_leaf=False):
    if node.type == ':':
        info = 'colon' + str(node.start_byte) + ',' + str(node.end_byte)
    elif is_leaf:
        info = node.text.decode('utf-8').replace(':', 'colon') + str(node.start_byte) + ',' + str(node.end_byte)
    else:
        info = str(node.type).replace(':', 'colon') + str(node.start_byte) + ',' + str(node.end_byte)
    return info

def create_ast_tree(dot, node):
    node_info = get_node_info_ast(node)
    dot.node(node_info, shape='rectangle', label=node.type)
    if not node.child_count:
        leaf_info = get_node_info_ast(node, is_leaf=True)
        dot.node(leaf_info, shape='ellipse', label=node.text.decode('utf-8'))
        if node.text.decode('utf-8') != node.type:
            dot.edge(node_info, leaf_info)
        return
    for child in node.children:
        create_ast_tree(dot, child)
        child_info = get_node_info_ast(child)
        dot.edge(node_info, child_info)
    return id
    
def get_call_nodes(root_node, call_nodes):
    # 找到所有的call_expression
    if root_node.type == 'call_expression':
        call_nodes.append(root_node)
    for child in root_node.children:
        get_call_nodes(child, call_nodes)

def get_func_return_nodes(node, return_nodes):
    # 找到func_node函数的所有return语句
    if node.type == 'return_statement':
        return_nodes.append((node, 'R'))
    for child in node.children:
        get_func_return_nodes(child, return_nodes)
    
def find_child_node(node, type):
    # 找到node的第一个type类型的子节点
    if node.type == type:
        return node
    for child in node.children:
        if child.type == type:
            return child
    return None

def get_label_nodes(node, label_nodes):
    # 找到所有的label节点，返回{label: node}的字典
    if node.type == 'labeled_statement':
        label = node.children[0].text.decode('utf-8')
        label_nodes[label] = node
    for child in node.children:
        get_label_nodes(child, label_nodes)

def get_goto_nodes(node, goto_nodes):
    # 找到所有goto语句的节点，返回[(label, node)]的列表
    if node.type == 'goto_statement':
        label = node.children[1].text.decode('utf-8')
        goto_nodes.append((label, node))
    for child in node.children:
        get_goto_nodes(child, goto_nodes)

def get_first_node(node):
    if node.type in ['if_statement', 'while_statement']:
        return node.children[1].children[1]
    elif node.type == 'for_statement':
        abc = get_for_info(node)
        if abc[0]:      # for(a;?;?)
            return abc[0]
        elif abc[1]:    # for(;b;?)
            return abc[1]
        else:           # for(;;?)
            compound_node = find_child_node(node, 'compound_statement')
            if compound_node:   # for(;;?){statements}
                return get_first_node(compound_node.children[1])
            else:               # for(;;?) statement;
                return get_first_node(node.children[-1])
    elif node.type == 'switch_statement':
        return node.chilren[2].children[1].children[1]
    else:
        return node

def get_for_begin_node(node):
    # 找到for循环的开始节点
    abc = get_for_info(node)
    if abc[1]:    # for(;b;?)
        return abc[1]
    else:           # for(;;?)
        compound_node = find_child_node(node, 'compound_statement')
        if compound_node:
            return get_first_node(compound_node.children[1])
        else:               # for(;;?) statement;
            return get_first_node(node.children[-1])

def get_continue_nodes(node):
    # 找到node节点循环中的所有continue节点并返回
    continue_nodes = []
    for child in node.children:
        if child.type == 'continue_statement':
            continue_nodes.append(child)
        elif child.type not in ['for_statement', 'while_statement']:
            continue_nodes.extend(get_continue_nodes(child))
    return continue_nodes

def get_node_info(node):
    # 获得节点的信息作为节点的唯一标志
    return str(node.start_point) + str(node.end_point)

def get_node_type(node, types):
    if node.child_count == 0:
        types.append(node.type)
    for child in node.children:
        get_node_type(child, types)

def get_node_label(node):
    # 获得节点的标签名称
    if node.type == 'function_definition':
        func_name = node.children[1].children[0].text.decode('utf-8')
        return f"<(FUNC | {func_name})<SUB>{node.start_point[0]}</SUB>>"
    elif node.type == 'return_statement':
        text = html.escape(node.text.decode('utf-8'))
        return f"<(RETURN | {text})<SUB>{node.start_point[0]}</SUB>>"
    else:
        text = html.escape(node.text.decode('utf-8'))
        node_types = []
        get_node_type(node, node_types)
        types = html.escape(str(node_types))
        # types = node.type
        return f"<({types} | {text})<SUB>{node.start_point[0]}</SUB>>"

def connect_in_nodes(dot, in_nodes, node):
    # 连接in_nodes中的节点到node
    for in_node in in_nodes:
        if in_node[1] == 'O':
            dot.edge(get_node_info(in_node[0]), get_node_info(node))
        elif in_node[1] == 'Y':
            dot.edge(get_node_info(in_node[0]), get_node_info(node), label='Y')
        elif in_node[1] == 'N':
            dot.edge(get_node_info(in_node[0]), get_node_info(node), label='N')
        elif in_node[1] == 'R':
            dot.edge(get_node_info(in_node[0]), get_node_info(node), label='return')

def function_cfg(dot, node):
    # 画函数的CFG
    compound_node = find_child_node(node, 'compound_statement')    # 找到函数的复合语句
    dot.node(get_node_info(node), label=get_node_label(node))   # 画函数节点
    in_nodes = [(node, 'O')]    # 'O'表示没有信息，'Y'表示边的标签为Yes，'N'表示边的标签为No
    out_nodes = compound_statement_cfg(dot, compound_node, in_nodes)   # 画复合语句的CFG
    # 处理goto语句
    label_nodes = {}
    get_label_nodes(node, label_nodes)
    goto_labels = []
    get_goto_nodes(node, goto_labels)
    for label, goto_node in goto_labels:
        dot.edge(get_node_info(goto_node), get_node_info(label_nodes[label]))
    return out_nodes

def compound_statement_cfg(dot, node, in_nodes):
    # 画复合语句的CFG
    for statememt in node.children[1: -1]:
        out_nodes = statement_cfg(dot, statememt, in_nodes)
        in_nodes = out_nodes
    return in_nodes

def statement_cfg(dot, node, in_nodes):
    # 画语句的CFG
    if in_nodes == []:  # 如果不加上会出现悬浮节点
        return []
    if node.type not in ['if_statement', 'while_statement', 'for_statement', 'switch_statement']:
        return expression_cfg(dot, node, in_nodes)
    elif node.type == 'if_statement':
        return if_cfg(dot, node, in_nodes)
    elif node.type == 'while_statement':
        return while_cfg(dot, node, in_nodes)
    elif node.type == 'for_statement':
        return for_cfg(dot, node, in_nodes)
    elif node.type == 'switch_statement':
        return switch_case_cfg(dot, node, in_nodes)

def expression_cfg(dot, node, in_nodes):
    # 画普通表达式的CFG
    first_node = get_first_node(node)
    dot.node(get_node_info(first_node), shape='rectangle', label=get_node_label(first_node))
    connect_in_nodes(dot, in_nodes, first_node)
    if node.children[0].text in [b'break', b'return', b'continue', b'goto']:   # 如果是break语句
        return []
    else:
        return [(node, 'O')]

def if_cfg(dot, node, in_nodes):
    # 画if语句的CFG
    first_node = get_first_node(node)  # 第一个节点为for的条件
    dot.node(get_node_info(first_node), shape='diamond', label=get_node_label(first_node))
    connect_in_nodes(dot, in_nodes, first_node)    # 将in_nodes和第一个节点连接
    compound_node = find_child_node(node, 'compound_statement')    # 找到if的复合语句
    out_nodes = []
    if compound_node is None:   # if语句没有花括号
        in_nodes = [(first_node, 'Y')]
        out_nodes = statement_cfg(dot, node.children[2], in_nodes)   # 画if语句的下一个语句的CFG
    else:
        in_nodes = [(first_node, 'Y')]  # if的条件为真，in_nodes中的节点到if的复合语句的边的标签为Y
        out_nodes = compound_statement_cfg(dot, compound_node, in_nodes)
    if node.child_count >= 4:   # 如果有else或者else if语句
        in_nodes = [(first_node, 'N')]  # if的条件为假，in_nodes中的节点到else或else if的复合语句的边的标签为N
        out_nodes.extend(else_cfg(dot, node, in_nodes))
    else:   # 如果没有else或者else if语句，则将if的条件语句连接到if语句的下一个语句，边的标签为N
        out_nodes.append((first_node, 'N'))
    return out_nodes

def else_cfg(dot, node, in_nodes):
    # 画else语句的CFG
    node = node.children[3] # node的第四个节点类型一定是else_clause
    if node.type == 'else_clause':
        node = node.children[1]
        if node.type == 'compound_statement':   # 如果是else语句
            out_nodes = compound_statement_cfg(dot, node, in_nodes)
        elif node.type == 'if_statement':       # 如果是else if语句
            out_nodes = if_cfg(dot, node, in_nodes)
        else:   # 如果else语句没有花括号
            out_nodes = statement_cfg(dot, node, in_nodes)
        return out_nodes

def break_cfg(node):
    # 找到node节点循环中的所有break节点并返回
    break_nodes = []
    for child in node.children:
        if child.type == 'break_statement':
            break_nodes.append((child, 'O'))
        elif child.type not in ['for_statement', 'while_statement']:
            break_nodes.extend(break_cfg(child))
    return break_nodes

def while_cfg(dot, node, in_nodes):
    # 画while语句的CFG
    first_node = get_first_node(node)   # 第一个节点为while的条件
    dot.node(get_node_info(first_node), shape='diamond', label=get_node_label(first_node))
    connect_in_nodes(dot, in_nodes, first_node)    # 将in_nodes和第一个节点连接
    compound_node = find_child_node(node, 'compound_statement')    # 找到while的复合语句
    out_nodes = []
    if compound_node is None:   # while语句没有花括号
        in_nodes = [(first_node, 'Y')]
        out_nodes = statement_cfg(dot, node.children[2], in_nodes)   # 画while语句的下一个语句的CFG
        connect_in_nodes(dot, out_nodes, first_node)    # 将while的复合语句和while的条件连接
    else:
        in_nodes = [(first_node, 'Y')]  # while的条件为真，in_nodes中的节点到if的复合语句的边的标签为Y
        out_nodes = compound_statement_cfg(dot, compound_node, in_nodes)
        connect_in_nodes(dot, out_nodes, first_node)    # 将while的复合语句和while的条件连接
    continue_nodes = get_continue_nodes(node)
    for continue_node in continue_nodes:
        dot.edge(get_node_info(continue_node), get_node_info(first_node))
    return [(first_node, 'N')] + break_cfg(node)   # break语句也是while语句的出口
    
def for_cfg(dot, node, in_nodes):
    # 画for语句的CFG
    first_node = get_first_node(node)  # 第一个节点为for的条件
    abc = get_for_info(node)
    if abc[0] or abc[1]:
        connect_in_nodes(dot, in_nodes, first_node)    # 将in_nodes和第一个节点连接
    if abc[0]:
        dot.node(get_node_info(abc[0]), shape='rectangle', label=get_node_label(abc[0]))
        if abc[1]:
            dot.edge(get_node_info(abc[0]), get_node_info(abc[1]))
        else:
            in_nodes = [(abc[0], 'O')]
    if abc[1]:
        dot.node(get_node_info(abc[1]), shape='diamond', label=get_node_label(abc[1]))
        in_nodes = [(abc[1], 'Y')]
    compound_node = find_child_node(node, 'compound_statement')    # 找到for的复合语句
    if compound_node is None:   # for语句没有花括号
        out_nodes = statement_cfg(dot, node.children[-1], in_nodes)   # 画for语句的下一个语句的CFG
    else:
        out_nodes = compound_statement_cfg(dot, compound_node, in_nodes)
    begin_node = get_for_begin_node(node)
    if out_nodes != []:
        if abc[2]:  # 如果有c
            dot.node(get_node_info(abc[2]), shape='rectangle', label=get_node_label(abc[2]))
            connect_in_nodes(dot, out_nodes, abc[2])
            dot.edge(get_node_info(abc[2]), get_node_info(begin_node))
        else:   
            connect_in_nodes(dot, out_nodes, begin_node)
    continue_nodes = get_continue_nodes(node)
    for continue_node in continue_nodes:
        dot.edge(get_node_info(continue_node), get_node_info(begin_node))
    if abc[1]:
        return break_cfg(node) + [(abc[1], 'N')]
    else:
        return break_cfg(node)

def case_cfg(dot, node, in_nodes, test_text):
    # 画case语句的CFG
    val_node = node.children[1]     # case val_node:
    case_or_default = node.children[0].text.decode('utf-8') 
    if case_or_default == 'case':
        label = f"<(['case', '{val_node.type}'] | {test_text} == {val_node.text.decode('utf-8')})<SUB>{val_node.start_point[0]}</SUB>>"
        dot.node(get_node_info(val_node), shape='diamond', label=label)   # 画case节点
        connect_in_nodes(dot, in_nodes, val_node)
        in_nodes = [(val_node, 'Y')]    # 满足case条件
        for child in node.children[3:]:
            out_nodes = statement_cfg(dot, child, in_nodes)
            in_nodes = out_nodes
        return [(val_node, 'N')] + in_nodes  
    else:   # 如果是default
        for child in node.children[2:]:
            out_nodes = statement_cfg(dot, child, in_nodes)
            in_nodes = out_nodes
        return in_nodes

def switch_case_cfg(dot, node, in_nodes):
    # 画switch case语句的CFG
    test_node = node.children[1].children[1]    # switch(test_node)
    test_text = test_node.text.decode('utf-8')
    compound_node = find_child_node(node, 'compound_statement')    # 找到switch的复合语句
    for case in compound_node.children[1:-1]:   # case: case_statement
        out_nodes = case_cfg(dot, case, in_nodes, test_text)
        in_nodes = out_nodes
    break_nodes = break_cfg(node)
    return break_nodes + in_nodes

class SCTS:
    def __init__(self, language):
        self.language = language
        if not os.path.exists(f'./build/{language}-languages.so'):
            if not os.path.exists(f'./tree-sitter-{language}'):
                os.system(f'git clone https://github.com/tree-sitter/tree-sitter-{language}')
            Language.build_library(
                f'./build/{language}-languages.so',
                [
                    f'./tree-sitter-{language}',
                ]
            )
        LANGUAGE = Language(f'./build/{language}-languages.so', language)
        parser = Parser()
        parser.set_language(LANGUAGE)
        self.parser = parser

    def see_tree(self, code):
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        dot = Digraph(comment='AST Tree', strict=True)
        create_ast_tree(dot, root_node)
        dot.render('ast_tree', view=True)

    def CFG(self, code):
        # 画代码code的CFG
        tree = self.parser.parse(bytes(code, 'utf8'))
        root_node = tree.root_node
        dot = Digraph(comment='CFG')
        func_name_node = {}
        for each in root_node.children:
            if each.type == 'function_definition':
                out_nodes = function_cfg(dot, each) # 画函数的CFG
                return_nodes = []
                get_func_return_nodes(each, return_nodes)
                out_nodes += return_nodes
                func_name_node[each.children[1].children[0].text.decode('utf-8')] = (each, out_nodes)
        # 处理函数调用
        call_nodes = []        
        get_call_nodes(root_node, call_nodes)
        for call_node in call_nodes:
            func_name = call_node.children[0].text.decode('utf-8')
            if func_name in func_name_node:
                func_node, out_nodes = func_name_node[func_name]
                dot.edge(get_node_info(call_node), get_node_info(func_node), label='call')
                connect_in_nodes(dot, out_nodes, call_node)
        dot.render('ast_tree', view=True)

if __name__ == '__main__':
    code = '''
    int main() {
        int a = 1;
        if (cmp(a, b))
            a = b;
        else if(cmp(a, b)){
            a = c;
            if (cmp(a, d)) {
                a = d;
            } 
        }
        else {
            a += c;
        }
        return 0;
    }

    int cmp(int a, int b){
        if (a < b)
            return a;
        else
            return b;
    }
    '''
    scts = SCTS('c')
    # scts.see_tree(code)
    scts.CFG(code)


