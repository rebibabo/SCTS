import re
from tree_sitter import Parser, Language
import inspect
text = lambda x: x.text.decode('utf-8')

def get_parameter_count(func):
    signature = inspect.signature(func)
    params = signature.parameters
    return len(params)

def replace_from_blob(operation, blob):
    diff = 0        # 插入删除产生的长度差
    # 按照第一个元素，及修改的位置从小到大排序，如果有同一个位置删除和插入，先删除再插入
    operation = sorted(operation, key=lambda x: (x[0], 1 if type(x[1]) is int else 0, -len(x[1]) if type(x[1]) is not int else 0)) # 第一个key是index，第二个key是先做删除操作，第三个key是先插入字符串少的
    for op in operation:
        if type(op[1]) is int:  # 如果第二个元素是一个数字
            if op[1] < 0:      # 如果小于0，则从op[0]往左删除到op[1]个元素
                del_num = op[1]
            else:       # 则从op[0]往左删除到op[1]个元素
                del_num = op[1] - op[0]
            blob = blob[:op[0] + diff + del_num] + blob[op[0] + diff:]
            diff += del_num
        else:                   # 如果第二个元素是字符串，则从op[0]往右插入该字符串，diff+=len(op[1])
            blob = blob[:op[0] + diff] + op[1] + blob[op[0] + diff:]
            diff += len(op[1])
    return blob


def traverse_all_children(node, results):
    if node.is_named:
        results.append(node)
    if not node.children:
        return
    for n in node.children:
        traverse_all_children(n, results)


def traverse_type(node, results, kind):
    if node.type == kind:
        results.append(node)
    if not node.children:
        return
    for n in node.children:
        traverse_type(n, results, kind)


def traverse_rec_func(node, results, func, code=None):
    # 遍历整个AST树，返回符合func的节点列表results
    if get_parameter_count(func) == 1:
        if func(node):
            results.append(node)
    else:
        if func(node, code):
            results.append(node)
    if not node.children:
        return
    for n in node.children:
        traverse_rec_func(n, results, func)
    

def traverse_cvt_func(node, results, func):
    cvted = func(node)
    if cvted:
        results.append(cvted)
    if not node.children:
        return
    for n in node.children:
        traverse_cvt_func(n, results, func)