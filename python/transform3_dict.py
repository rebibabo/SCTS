from utils import replace_from_blob, traverse_rec_func, text

'''==========================匹配========================'''
def rec_InitCallDict(node):
    # 是否是dict()
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'dict':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 2:
                return True

def rec_InitDict(node):
    # 是否是{}
    if node.type == 'dictionary' and len(node.children) == 2:
        return True

def rec_CallDict(node):
    # 是否是dict({...})
    if node.type == 'call':
        func = node.child_by_field_name('function')
        if func.text == b'dict':
            args = node.child_by_field_name('arguments')
            if len(args.children) == 3 and args.children[1].type == 'dictionary':
                return True

def rec_Dict(node):
    # 是否是{...}, 且不是dict({...})  
    # node:{...} node.parent:({...}) node.parent.parent:dict({...}) node.parent.parent:children[0]:dict
    if node.type == 'dictionary' and node.parent.parent.children[0].text != b'dict':  
        return True
        
'''==========================替换========================'''
def cvt_InitDict2InitCallDict(node):
    # {} -> dict()
    # 删除{}                      加上dict()
    return [(node.end_byte, -len(node.text)), (node.end_byte, 'dict()')]
    
def cvt_InitCallDict2InitDict(node):
    # dict() -> {}
    return [(node.end_byte, -len(node.text)), (node.end_byte, '{}')]

def cvt_Dict2CallDict(node):
    # {...} -> dict({...})
    return [(node.start_byte, 'dict('), (node.end_byte, ')')]

def cvt_CallDict2Dict(node):
    # dict({...}) -> {...}
    args = node.child_by_field_name('arguments')
    return [(args.children[1].start_byte, node.start_byte - args.children[1].start_byte),   # 删除dict( 
            (args.children[2].end_byte, -1)]
