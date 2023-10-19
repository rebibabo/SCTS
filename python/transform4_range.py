from utils import replace_from_blob, traverse_rec_func

'''==========================匹配========================'''
def rec_CallRange(node):
    # 是否是range(C)
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'range':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 3:
                return True

def rec_CallRangeWithZero(node):
    # 是否是range(0,C)
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'range':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 5 and args.children[1].type == 'integer' and args.children[1].text == b'0':
                return True

'''==========================替换========================'''
def cvt_CallRange2CallRangeWithZero(node):
    # range(C) -> range(0,C)
    if rec_CallRange(node):
        args = node.child_by_field_name('arguments')
        return [(args.start_byte + 1, '0, ')]
        
def cvt_CallRangeWithZero2CallRange(node):
    # range(0,C) -> range(C)
    if rec_CallRangeWithZero(node):
        args = node.child_by_field_name('arguments')        # 删除第二个参数开始的位置到第一个参数开始的位置
        return [(args.children[3].start_byte, args.start_byte - args.children[3].start_byte + 1)]
