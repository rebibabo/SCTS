from networkx.algorithms.richclub import rich_club_coefficient
from utils import text
import networkx as nx
from tree_sitter import Node
from typing import List, Tuple, Union

def op_chain(edges: List[Tuple[str, str, str]]) -> Tuple[List[str], str]:
    # 输入小于号左右两边的变量构成的边的集合，输出最长的链
    G = nx.DiGraph()
    for edge in edges:
        G.add_edge(edge[0],edge[1],label=edge[2])
    starts = [x for x in G.nodes() if G.in_degree(x) == 0]
    ends = [x for x in G.nodes() if G.out_degree(x) == 0]
    paths = []
    for start in starts:
        for path in nx.all_simple_paths(G, start, ends):
            paths.append(path)
    paths = sorted(paths, key=lambda x: len(x), reverse=True)
    path = paths[0]
    str = ''
    for i in range(len(path) - 1):
        op = G.get_edge_data(path[i],path[i+1])['label']
        str += f'{path[i]} {op} '
    str += path[-1]
    return path, str

'''==========================匹配========================'''
def rec_AugmentedAssignment(node: Node) -> bool:
    # a ?= b
    if node.type == 'augmented_assignment':
        return True

def rec_Assignment(node: Node) -> bool:
    # a = a ? b
    if node.type == 'assignment':
        left_id = text(node.child_by_field_name('left'))
        right = node.child_by_field_name('right')
        if right and right.type == 'binary_operator' and text(right.child_by_field_name('left')) == left_id:
            return True

def rec_CmpRightConst(node: Node) -> bool:
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) in ['<', '>', '<=', '>=', '==', '!='] \
            and node.children[2].type in ['integer', 'string', 'list', 'set', 'dictionary', 'float', 'tuple']:
        return True

def rec_CmpOptBigger(node: Node) -> bool:
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) in ['>', '>=']:
        return True

def rec_CmpOptSmaller(node: Node) -> bool:
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) in ['<', '<=']:
        return True

def rec_Cmp(node: Node) -> bool:  # tx
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) in ['>', '>=', '<', '<=', '==', '!=']:
        return True

def match_Equal(node: Node) -> bool:
    # a == b
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) == '==':
        return True

def match_NotEqual(node: Node) -> bool:
    # a != b
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) == '!=':
        return True

def match_LeftConst(node: Node) -> bool:
    # const op a
    if node.type == 'comparison_operator' and node.children[1].text != b'in'\
            and text(node.children[1]) in ['<', '>', '<=', '>=', '==', '!='] \
            and node.children[0].type in ['integer', 'string', 'list', 'set', 'dictionary', 'float', 'tuple']:
        return True

def rec_CmpSplit(node: Node) -> bool:
    # a>0 and a<5 and b>a and b<5
    nodes, edges = set(), []
    reverse_op_dict = {'>=':'<=', '>':'<'}
    if node.type == 'boolean_operator' and node.parent.type != 'boolean_operator':
        while node:
            if node.type != 'boolean_operator': break
            left = node.child_by_field_name('left')
            right = node.child_by_field_name('right')
            if right.type != 'comparison_operator': return False
            [l, op, r] = [text(x) for x in right.children]
            if op not in ['<', '>', '<=', '>=']:    return False
            nodes.add(l)
            nodes.add(r)
            if op in ['>', '>=']:
                edges.append((r, l, reverse_op_dict[op]))
            else:
                edges.append((l, r, op))
            node = left
        [l, op, r] = [text(x) for x in node.children]
        if op not in ['<', '>', '<=', '>=']:    return False
        nodes.add(l)
        nodes.add(r)
        if op in ['>', '>=']:
            edges.append((r, l, reverse_op_dict[op]))
        else:
            edges.append((l, r, op))
        chain, _ = op_chain(edges)
        return len(chain) == len(nodes) and len(chain) > 2       
    
def match_CmpChain(node: Node) -> bool:
    if node.type == 'comparison_operator':
        id_num = 0
        for child in node.children:
            if child.type == 'identifier':
                id_num += 1
            if id_num > 2:
                return True

'''==========================替换========================'''
def cvt_AugmentedAssignment2Assignment(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a ?= b -> a = a ? b
    if rec_AugmentedAssignment(node):
        if len(node.children) == 3:
            [a, op, b] = [text(x) for x in node.children]
            new_str = f'{a} = {a} {op[:-1]} {b}'
            return [(node.end_byte, -len(text(node))),
                    (node.start_byte, new_str)] 

def cvt_Assignment2AugmentedAssignment(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a = a ? b -> a ?= b
    a = text(node.child_by_field_name('left'))
    op = text(node.children[2].children[1])
    if len(node.children[2].children) < 3:
        return 
    b = text(node.children[2].children[2])
    new_str = f'{a} {op}= {b}'
    return [(node.end_byte, node.start_byte),
            (node.start_byte, new_str)] 

def cvt_RightConst2LeftConst(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a op const -> const po a
    if len(node.children) == 3:
        [a, op, const] = [text(x) for x in node.children]
        reverse_op_dict = {'<':'>', '>=':'<=', '<=':'>=', '>':'<', '==':'==', '!=':'!='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{const} {reverse_op_dict[op]} {a}')]

def cvt_Bigger2Smaller(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a > b -> b < a
    if len(node.children) == 3:
        [a, op, b] = [text(x) for x in node.children]
        reverse_op_dict = {'>':'<', '>=':'<='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{b} {reverse_op_dict[op]} {a}')]

def cvt_Smaller2Bigger(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a <= b -> b >= a
    if len(node.children) == 3:
        [a, op, b] = [text(x) for x in node.children]
        reverse_op_dict = {'<':'>', '<=':'>='}
        return [(node.end_byte, node.start_byte), 
                (node.start_byte, f'{b} {reverse_op_dict[op]} {a}')]

def cvt_Equal(node: Node) -> List[Tuple[int, Union[int, str]]]:    # tx
    if len(node.children) == 3:
        [a, op, b] = [text(x) for x in node.children]
        if op in ['==']: return
        if op in ['<=']:
            # a < b || a == b
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'{a} < {b} || {a} == {b}')]
        if op in ['<']:
            # !(b < a || a == b)
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'!({b} < {a} || {a} == {b})')]
        if op in ['>=']:
            # a > b || a == b
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'{a} > {b} || {a} == {b}')]
        if op in ['>']:
            # !(b > a || a == b)
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'!({b} > {a} || {a} == {b})')]
        if op in ['!=']:
            # !(a == b)
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'!({a} == {b})')]

def cvt_NotEqual(node: Node) -> List[Tuple[int, Union[int, str]]]:    # tx
    if len(node.children) == 3:
        [a, op, b] = [text(x) for x in node.children]
        if op in ['!=']: return
        if op in ['<=']:
            # !(b < a && a != b)
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'!({b} < {a} && {a} != {b})')]
        if op in ['<']:
            # (a < b && a != b)
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'{a} < {b} && {a} != {b}')]
        if op in ['>=']:
            # !(b > a && a != b)
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'!({b} > {a} && {a} != {b})')]
        if op in ['>']:
            # a < b && a != b
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'{a} < {b} && {a} != {b}')]
        if op in ['==']:
            # a != b
            return [(node.end_byte, node.start_byte), 
                    (node.start_byte, f'{a} != {b}')]

def cvt_CmpSplit2Chain(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # a>0 and a<5 and b>a and b<=5 -> 0<a<b<=5
    ori_node = node
    edges = []
    reverse_op_dict = {'>=':'<=', '>':'<'}
    if node.type == 'boolean_operator' and node.parent.type != 'boolean_operator':
        while node:
            if node.type != 'boolean_operator': break
            left = node.child_by_field_name('left')
            right = node.child_by_field_name('right')
            [l, op, r] = [text(x) for x in right.children]
            if op in ['>', '>=']:
                edges.append((r, l, reverse_op_dict[op]))
            else:
                edges.append((l, r, op))
            node = left
        [l, op, r] = [text(x) for x in node.children]
        if op in ['>', '>=']:
            edges.append((r, l, reverse_op_dict[op]))
        else:
            edges.append((l, r, op))
        _, new_str = op_chain(edges)
        return [(ori_node.end_byte, ori_node.start_byte), (ori_node.start_byte, new_str)]