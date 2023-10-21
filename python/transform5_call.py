from utils import replace_from_blob, traverse_rec_func, text
from python.transform1_print import *

'''==========================匹配========================'''
def rec_MagicCall(node):
    # 判断节点node是否使用了__call__: func.__call__()
    if node.type == 'call':
        func = node.child_by_field_name('function')
        attribute = func.child_by_field_name('attribute')
        if attribute and attribute.text == b'__call__':
            return True

def rec_Call(node,):
    # 判断是否调用了函数，且不是print函数
    if node.type == 'call' and not rec_MagicCall(node) and not rec_CallPrintWithoutEnd(node) and not rec_CallPrintWithoutFlush(node):
        return True

'''==========================替换========================'''
def cvt_Call2MagicCall(node):
    # test(args) -> test.__call__(args)
    func = node.child_by_field_name('function')
    return [(func.end_byte, '.__call__')]   # 添加.__call__

def cvt_MagicCall2Call(node):
    # test.__call__(args) -> test(args)
    func = node.child_by_field_name('function') 
    dot_index = func.children[1].start_byte                # dot_index为".__call__"中'.'的索引
    return [(func.end_byte, dot_index - func.end_byte)]    # 删除.__call__
