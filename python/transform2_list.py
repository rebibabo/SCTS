from utils import replace_from_blob, traverse_rec_func, text

'''==========================匹配========================'''
def rec_InitCallList(node):
    # 是否是list()
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'list':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 2:
                return True

def rec_InitList(node):
    # 是否是[]
    if node.type == 'list' and len(node.children) == 2:
        return True

def rec_CallList(node):
    # 是否是list([...])
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'list':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 3 and args.children[1].type == 'list':
                return True

def rec_List(node):
    # 是否是[...], 且不是list([...])  
    # node:[...] node.parent:([...]) node.parent.parent:list([...]) node.parent.parent:children[0]:list
    if node.type == 'list' and node.parent.parent.children[0].text != b'list':  
        return True

'''==========================替换========================'''
def cvt_InitList2InitCallList(node):
    # [] -> list()
    # 删除[]                      加上list()
    return [(node.end_byte, -len(node.text)), (node.end_byte, 'list()')]
        
def cvt_InitCallList2InitList(node):
    # list() -> []
    return [(node.end_byte, -len(node.text)), (node.end_byte, '[]')]

def cvt_List2CallList(node):
    # [...] -> list([...])
    return [(node.start_byte, 'list('), (node.end_byte, ')')]

def cvt_CallList2List(node):
    # list([...]) -> [...]
    args = node.child_by_field_name('arguments')
    return [(args.children[1].start_byte, node.start_byte - args.children[1].start_byte),   # 删除list( 
            (args.children[2].end_byte, -1)]            # 删除)
