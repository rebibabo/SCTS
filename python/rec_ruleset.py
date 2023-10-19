from ..utils import match_from_bytes
# 判断node是否为指定修改的片段，blob为原始代码

def rec_List(node, blob):
    if node.type == 'list':
        return True

def rec_InitList(node, blob):
    # 判断是否为list且为初始化列表[]
    if node.type == 'list' and len(node.children) == 2:
        return True

def rec_CallList(node, blob):
    # 是否是list([...])
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if match_from_bytes(func,blob) == 'list':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 3 and args.children[1].type == 'list':
                return True

def rec_InitCallList(node, blob):
    # 是否是list([])
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if match_from_bytes(func,blob) == 'list':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 2:
                return True

def rec_CallRange(node, blob):
    # 是否是range(C)
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if match_from_bytes(func,blob) == 'range':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 3:
                return True

def rec_CallRangeWithZero(node, blob):
    # 是否是range(0,C)
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if match_from_bytes(func,blob) == 'range':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 5 and args.children[1].type == 'integer' and match_from_bytes(args.children[1], blob) == '0':
                return True

def rec_CallPrint(node, blob):
    # 是否是print()且不是print(args, flush=True)
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if match_from_bytes(func,blob) == 'print':
            args = node.child_by_field_name('arguments')
            for arg in args.children:
                keyword = arg.child_by_field_name('name')
                if keyword and match_from_bytes(keyword, blob) == 'flush':
                    value = arg.child_by_field_name('value')
                    if match_from_bytes(value, blob) == 'True':     
                        return
            return True
            
def rec_CallPrintWithFlush(node, blob):
    # 是否是print(args, flush=True)
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if match_from_bytes(func,blob) == 'print':
            args = node.child_by_field_name('arguments')
            for arg in args.children:
                keyword = arg.child_by_field_name('name')
                if keyword and match_from_bytes(keyword, blob) == 'flush':
                    value = arg.child_by_field_name('value')
                    if match_from_bytes(value, blob) == 'True':
                        return True

def rec_CallItems(node, blob):
    if node.type == 'call':
        func = node.child_by_field_name('function')
        attribute = func.child_by_field_name('attribute')
        if attribute and match_from_bytes(attribute, blob) == 'items':
            return True

def rec_CallZipKeysAndValues(node, blob):
    if node.type == 'call':
        func = node.child_by_field_name('function')
        args = node.child_by_field_name('arguments')
        if match_from_bytes(func,blob) == 'zip' and args:
            if len(args.children) == 5:
                first_arg = args.children[1]
                second_arg = args.children[3]
                if first_arg.type == 'call' and second_arg.type == 'call':
                    first_arg_func = first_arg.child_by_field_name('function')
                    first_arg_attr = first_arg_func.child_by_field_name('attribute')
                    second_arg_func = second_arg.child_by_field_name('function')
                    second_arg_attr = second_arg_func.child_by_field_name('attribute')

                    if first_arg_attr and second_arg_attr:
                        if match_from_bytes(first_arg_attr, blob) == 'keys' and match_from_bytes(second_arg_attr, blob) == 'values':
                            return True
                        if match_from_bytes(first_arg_attr, blob) == 'values' and match_from_bytes(second_arg_attr, blob) == 'keys':
                            return True


def rec_MagicCall(node, blob):
    # 判断节点node是否使用了__call__: func.__call__()
    if node.type == 'call':
        func = node.child_by_field_name('function')
        attribute = func.child_by_field_name('attribute')
        if attribute and match_from_bytes(attribute, blob) == '__call__':
            return True

def rec_Call(node, blob):
    if node.type == 'call' and not rec_MagicCall(node, blob) and not rec_CallPrint(node,blob) and not rec_CallPrintWithFlush(node, blob):
        return True