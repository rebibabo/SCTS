from utils import replace_from_blob, traverse_rec_func, text

'''==========================匹配========================'''
def rec_CallPrintWithFlush(node):
    # 是否是print(args, flush=True)
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'print':
            args = node.child_by_field_name('arguments')
            for arg in args.children:
                keyword = arg.child_by_field_name('name')
                if keyword and keyword.text== b'flush':
                    value = arg.child_by_field_name('value')
                    if value.text == b'True':     
                        return True

def rec_CallPrintWithoutFlush(node):
    # 是否是print()且不是print(args, flush=True)
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'print':
            args = node.child_by_field_name('arguments')
            for arg in args.children:
                keyword = arg.child_by_field_name('name')
                if keyword and keyword.text== b'flush':
                    value = arg.child_by_field_name('value')
                    if value.text == b'True':     
                        return
            return True

def rec_CallPrintWithEndn(node):
    # 是否是print(args, end='\n')
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'print':
            args = node.child_by_field_name('arguments')
            for arg in args.children:
                keyword = arg.child_by_field_name('name')
                if keyword and keyword.text== b'end':
                    value = arg.child_by_field_name('value')
                    if value.text == b'"\\n"' or value.text == b"'\\n'":
                        return True

def rec_CallPrintWithoutEnd(node):
    # 是否是print()且不是print(args, end='\n')
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'print':
            args = node.child_by_field_name('arguments')
            for arg in args.children:
                keyword = arg.child_by_field_name('name')
                if keyword and keyword.text== b'end':
                    return
            return True

'''==========================替换========================'''
def cvt_CallPrint2CallPrintWithFlush(node):
    # print(args) -> print(args, flush=True)
    args = node.child_by_field_name('arguments')
    if len(args.children) == 2:
        return [(args.end_byte - 1, 'flush=True')]
    else:
        return [(args.end_byte - 1, ', flush=True')]

def cvt_CallPrintWithFlush2CallPrint(node):
    # print(args, flush=True) -> print(args)
    args = node.child_by_field_name('arguments')    # text为(flush=True)
    if len(args.children) == 3:
        return [(args.end_byte - 1, 2 - len(args.text))]    # 删掉flush=True
    else:
        last_comma_index = 0    # 最后一个逗号的索引
        for a in args.children:
            if a.type == ',':
                last_comma_index = a.end_byte    
            keyword = a.child_by_field_name('name')
            if keyword and keyword.text == b'flush':
                return [(a.end_byte, last_comma_index - a.end_byte - 1)]

def cvt_CallPrint2CallPrintWithEnd(node):
    # print(args) -> print(args, end='\n')
    args = node.child_by_field_name('arguments')
    if len(args.children) == 2:
        return [(args.end_byte - 1, "end='\\n'")]
    else:
        return [(args.end_byte - 1, ", end='\\n'")]

def cvt_CallPrintWithEndn2CallPrint(node):
    # print(args, end='\n') -> print(args)
    args = node.child_by_field_name('arguments')    # text为(flush=True)
    if len(args.children) == 3:
        return [(args.end_byte - 1, 2 - len(args.text))]    # 删掉flush=True
    else:
        last_comma_index = 0    # 最后一个逗号的索引
        for a in args.children:
            if a.type == ',':
                last_comma_index = a.end_byte    
            keyword = a.child_by_field_name('name')
            if keyword and keyword.text == b'end':
                return [(a.end_byte, last_comma_index - a.end_byte - 1)]
