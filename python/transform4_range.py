from utils import replace_from_blob, traverse_rec_func, text

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

def rec_SubscriptSlice(node):
    # a[1:2]
    if node.type == 'subscript':
        if node.children[2].type == 'slice':
            return True

def rec_ListIndex(node):
    # a[1]
    if node.type == 'subscript':
        if node.children[2].type == 'integer' and node.children[2].text != b'-1':
            return True

'''==========================替换========================'''
def cvt_CallRange2CallRangeWithZero(node):
    # range(C) -> range(0,C)
    args = node.child_by_field_name('arguments')
    return [(args.start_byte + 1, '0, ')]
        
def cvt_CallRangeWithZero2CallRange(node):
    # range(0,C) -> range(C)
    args = node.child_by_field_name('arguments')        # 删除第二个参数开始的位置到第一个参数开始的位置
    return [(args.children[3].start_byte, args.start_byte - args.children[3].start_byte + 1)]

def cvt_AddSliceIndex(node):
    # a[:n] -> a[0:n] or a[:-n] -> a[:len(a)-n]
    id = text(node.children[0])
    slice = text(node.children[2])
    if slice.count(':') == 1:
        left, right = slice.split(':')
        ret = []
        if left == '':
            ret.append((node.children[2].start_byte, '0'))
        if right.startswith('-'):
            ret.append((node.children[2].start_byte + slice.find(':') + 1, f'len({id})'))
        return ret

def cvt_DelSliceIndex(node):
    # a[0:n] -> a[:n] or a[:len(a)-n] -> a[:-n]
    id = text(node.children[0])
    slice = text(node.children[2])
    if slice.count(':') == 1:
        left, right = slice.split(':')
        ret = []
        if left == '0':
            ret.append((node.children[2].start_byte + slice.find(':'), -1))
        if f'len({id})-' in right.replace(' ', ''):
            ret.append((node.children[2].start_byte + slice.find('-'), slice.find(':') - slice.find('-') + 1))
        return ret

def cvt_AddIndex(node):
    # a[1] -> a[1:2]
    index_node = node.children[2]
    index = int(text(index_node))
    return [(index_node.end_byte, f':{index + 1}')]
