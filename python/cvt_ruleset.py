from .rec_ruleset import *
from ..utils import match_from_bytes
# 输入原始node和代码，输出修改之后的字符串final_str

def cvt_List2CallList(node, blob):
    # [...] -> list([...])
    if rec_List(node, blob):
        final_str = 'list({})'.format(match_from_bytes(node, blob))
        return final_str

def cvt_InitList2InitCallList(node, blob):
    # [] -> list()
    if rec_InitList(node, blob):
        # 删除[]                      加上list()
        return [(node.end_byte, -len(node.text)), (node.end_byte, 'list()')]

def cvt_CallList2List(node, blob):
    # list([...]) -> [...]
    if rec_CallList(node, blob):
        args = node.child_by_field_name('arguments')
        final_str = match_from_bytes(args.children[1], blob)
        return final_str

def cvt_InitCallList2InitList(node, blob):
    # list() -> []
    if rec_InitCallList(node, blob):
        return [(node.end_byte, -len(node.text)), (node.end_byte, '[]')]

def cvt_CallRange2CallRangeWithZero(node, blob):
    # range(C) -> range(0,C)
    if rec_CallRange(node, blob):
        args = node.child_by_field_name('arguments')
        return [(args.start_byte + 1, '0, ')]
        
def cvt_CallRangeWithZero2CallRange(node, blob):
    # range(0,C) -> range(C)
    if rec_CallRangeWithZero(node, blob):
        args = node.child_by_field_name('arguments')        # 删除第二个参数开始的位置到第一个参数开始的位置
        return [(args.children[3].start_byte, args.start_byte - args.children[3].start_byte + 1)]

def cvt_CallPrint2CallPrintWithFlush(node, blob):
    # print(args) -> print(args, flush=True)
    if rec_CallPrint(node, blob):
        args = node.child_by_field_name('arguments')
        if len(args.children) == 2:
            return [(args.end_byte - 1, 'flush=True')]
        else:
            return [(args.end_byte - 1, ', flush=True')]

def cvt_CallPrintWithFlush2CallPrint(node, blob):
    # print(args, flush=True) -> print(args)
    if rec_CallPrintWithFlush(node, blob):
        args = node.child_by_field_name('arguments')    # text为(flush=True)
        if len(args.children) == 3:
            return [(args.end_byte - 1, 2 - len(args.text))]    # 删掉flush=True
        else:
            last_comma_index = 0    # 最后一个逗号的索引
            for a in args.children:
                if a.type == ',':
                    last_comma_index = a.end_byte    
                keyword = a.child_by_field_name('name')
                if keyword and match_from_bytes(keyword, blob) == 'flush':
                    break
            return [(args.end_byte - 1, last_comma_index - args.end_byte)]

def cvt_CallItems2CallZipKeysAndValues(node, blob):
    if rec_CallItems(node, blob):
        func = node.child_by_field_name('function')
        dict_node = func.child_by_field_name('object')
        dict_str = match_from_bytes(dict_node, blob)
        final_str = 'zip({}.keys(), {}.values())'.format(dict_str, dict_str)
        return final_str

def cvt_CallZipKeysAndValues2CallItems(node, blob):
    if rec_CallZipKeysAndValues(node, blob):
        args = node.child_by_field_name('arguments')
        obj_node = args.children[1].child_by_field_name('function').child_by_field_name('object')
        final_str = '{}.items()'.format(match_from_bytes(obj_node, blob))
        return final_str

def cvt_Call2MagicCall(node, blob):
    # test(args) -> test.__call__(args)
    if rec_Call(node, blob):
        func = node.child_by_field_name('function')
        return [(func.end_byte, '.__call__')]   # 添加.__call__

def cvt_MagicCall2Call(node,blob):
    # test.__call__(args) -> test(args)
    if rec_MagicCall(node, blob):
        func = node.child_by_field_name('function') 
        dot_index = func.children[1].start_byte                # dot_index为".__call__"中'.'的索引
        return [(func.end_byte, dot_index - func.end_byte)]    # 删除.__call__