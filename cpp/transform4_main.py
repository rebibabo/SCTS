from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

def getMainInfo(node: Node) -> Tuple[Node, Node, Union[Node, None], str, str, Union[str, None]]:
    # 返回返回值节点，参数节点，return节点以及对应的文本
    ret_type_node = node.children[0]
    params_node = node.children[1].children[1]
    ret_node = None
    for each in node.children[2].children:
        if each.type == 'return_statement':
            ret_node = each
    ret_type_text = text(ret_type_node)
    params_text = text(params_node)
    ret_text = text(ret_node) if ret_node else None
    return ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text
    
'''==========================匹配========================'''
def rec_Main(node: Node) -> bool:
    if node.type == 'function_definition':
        if node.children[1].type == 'function_declarator':
            if node.children[1].children[0].text == b'main':
                return True

def match_IntVoidReturn(node: Node) -> bool:
    # int main(void) return 0
    if not rec_Main(node): return False
    _, params_node, ret_node, ret_type_text, params_text, _ = getMainInfo(node)
    if ret_type_text != 'int': return False
    if params_node.child_count != 3 or 'void' not in params_text: return False
    if ret_node is not None:
        if len(node.children[2].children) > 1:
            return True
    return False

def match_IntVoid(node: Node) -> bool:
    # int main(void)
    if not rec_Main(node): return False
    _, params_node, ret_node, ret_type_text, params_text, _ = getMainInfo(node)
    if ret_type_text != 'int': return False
    if params_node.child_count != 3 or 'void' not in params_text: return False
    if ret_node: return False
    return True

def match_IntReturn(node: Node) -> bool:
    # int main() return 0
    if not rec_Main(node): return False
    _, params_node, ret_node, ret_type_text, params_text, _ = getMainInfo(node)
    if ret_type_text != 'int': return False
    if params_node.child_count != 2: return False
    if ret_node is not None:
        if len(node.children[2].children) > 1:
            return True
    return False

def match_Int(node: Node) -> bool:
    # int main()
    if not rec_Main(node): return False
    _, params_node, ret_node, ret_type_text, params_text, _ = getMainInfo(node)
    if ret_type_text != 'int': return False
    if params_node.child_count != 2: return False
    if ret_node: return False
    return True

def match_IntArgReturn(node: Node) -> bool:
    # int main(int argc, char *argv[]) return 0
    if not rec_Main(node): return False
    _, params_node, ret_node, ret_type_text, params_text, _ = getMainInfo(node)
    if ret_type_text != 'int': return False
    if params_node.child_count != 5 or 'arg' not in params_text: return False
    if ret_node is not None:
        if len(node.children[2].children) > 1:
            return True
    return False

def match_IntArg(node: Node) -> bool:
    # int main(int argc, char *argv[])
    if not rec_Main(node): return False
    _, params_node, ret_node, ret_type_text, params_text, _ = getMainInfo(node)
    if ret_type_text != 'int': return False
    if params_node.child_count != 5 or 'arg' not in params_text: return False
    if ret_node: return False
    return True

def match_VoidArg(node: Node) -> bool:
    # void main(int argc, char *argv[])
    if not rec_Main(node): return False
    _, params_node, ret_node, ret_type_text, params_text, _ = getMainInfo(node)
    if ret_type_text != 'void': return False
    if params_node.child_count != 5 or 'arg' not in params_text: return False
    if ret_node: return False
    return True

def match_Void(node: Node) -> bool:
    # void main()
    if not rec_Main(node): return False
    _, params_node, ret_node, ret_type_text, params_text, _ = getMainInfo(node)
    if ret_type_text != 'void': return False
    if params_node.child_count != 2: return False
    if ret_node: return False
    return True
    
'''==========================替换========================'''
def cvt_IntVoidReturn(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # int main(void) return 0
    ret = []
    ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text = getMainInfo(node)
    if ret_type_text != 'int':
        ret.append((ret_type_node.end_byte, ret_type_node.start_byte))
        ret.append((ret_type_node.start_byte, 'int'))
    if params_node.child_count != 3 or 'void' not in params_text:
        ret.append((params_node.end_byte, params_node.start_byte))
        ret.append((params_node.start_byte, '(void)'))
    if ret_node is None:
        if len(node.children[2].children) > 1:
            ret.append((node.children[2].children[-2].end_byte, f'\n    return 0;'))
    return ret
        
def cvt_IntVoid(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # int main(void)
    ret = []
    ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text = getMainInfo(node)
    if ret_type_text != 'int':
        ret.append((ret_type_node.end_byte, ret_type_node.start_byte))
        ret.append((ret_type_node.start_byte, 'int'))
    if params_node.child_count != 3 or 'void' not in params_text:
        ret.append((params_node.end_byte, params_node.start_byte))
        ret.append((params_node.start_byte, '(void)'))
    if ret_node:
        ret.append((ret_node.end_byte, ret_node.start_byte))
    return ret 

def cvt_IntReturn(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # int main() return 0
    ret = []
    ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text = getMainInfo(node)
    if ret_type_text != 'int':
        ret.append((ret_type_node.end_byte, ret_type_node.start_byte))
        ret.append((ret_type_node.start_byte, 'int'))
    if params_node.child_count != 2:
        ret.append((params_node.end_byte, params_node.start_byte))
        ret.append((params_node.start_byte, '()'))
    if ret_node is None:
        if len(node.children[2].children) > 1:
            ret.append((node.children[2].children[-2].end_byte, f'\n    return 0;'))
    return ret 

def cvt_Int(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # int main()
    ret = []
    ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text = getMainInfo(node)
    if ret_type_text != 'int':
        ret.append((ret_type_node.end_byte, ret_type_node.start_byte))
        ret.append((ret_type_node.start_byte, 'int'))
    if params_node.child_count != 2:
        ret.append((params_node.end_byte, params_node.start_byte))
        ret.append((params_node.start_byte, '()'))
    if ret_node:
        ret.append((ret_node.end_byte, ret_node.start_byte))
    return ret 

def cvt_IntArgReturn(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # int main(int argc, char *argv[]) return 0
    ret = []
    ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text = getMainInfo(node)
    if ret_type_text != 'int':
        ret.append((ret_type_node.end_byte, ret_type_node.start_byte))
        ret.append((ret_type_node.start_byte, 'int'))
    if params_node.child_count != 5 or 'arg' not in params_text:
        ret.append((params_node.end_byte, params_node.start_byte))
        ret.append((params_node.start_byte, '(int argc, char *argv[])'))
    if ret_node is None:
        if len(node.children[2].children) > 1:
            ret.append((node.children[2].children[-2].end_byte, f'\n    return 0;'))
    return ret

def cvt_IntArg(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # int main(int argc, char *argv[])
    ret = []
    ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text = getMainInfo(node)
    if ret_type_text != 'int':
        ret.append((ret_type_node.end_byte, ret_type_node.start_byte))
        ret.append((ret_type_node.start_byte, 'int'))
    if params_node.child_count != 5 or 'arg' not in params_text:
        ret.append((params_node.end_byte, params_node.start_byte))
        ret.append((params_node.start_byte, '(int argc, char *argv[])'))
    if ret_node:
        ret.append((ret_node.end_byte, ret_node.start_byte))
    return ret 

def cvt_VoidArg(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # void main(int argc, char *argv[])
    ret = []
    ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text = getMainInfo(node)
    if ret_type_text != 'void':
        ret.append((ret_type_node.end_byte, ret_type_node.start_byte))
        ret.append((ret_type_node.start_byte, 'void'))
    if params_node.child_count != 5 or 'arg' not in params_text:
        ret.append((params_node.end_byte, params_node.start_byte))
        ret.append((params_node.start_byte, '(int argc, char *argv[])'))
    if ret_node:
        ret.append((ret_node.end_byte, ret_node.start_byte))
    return ret 

def cvt_Void(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # void main()
    ret = []
    ret_type_node, params_node, ret_node, ret_type_text, params_text, ret_text = getMainInfo(node)
    if ret_type_text != 'void':
        ret.append((ret_type_node.end_byte, ret_type_node.start_byte))
        ret.append((ret_type_node.start_byte, 'void'))
    if params_node.child_count != 2:
        ret.append((params_node.end_byte, params_node.start_byte))
        ret.append((params_node.start_byte, '()'))
    if ret_node:
        ret.append((ret_node.end_byte, ret_node.start_byte))
    return ret 