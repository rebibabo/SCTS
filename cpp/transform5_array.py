from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union

def get_indent(start_byte: int, code: str) -> int:
    indent = 0
    i = start_byte
    while i >= 0 and code[i] != '\n':
        if code[i] == ' ':
            indent += 1
        elif code[i] == '\t':
            indent += 8
        i -= 1
    return indent
    
def get_array_dim(node: Node) -> int:
    # a[i], a[i][j]
    dim = 0
    temp_node = node
    while temp_node.child_count:
        if type(temp_node) == 'subscript_expression':
            return 10
        temp_node = temp_node.children[0]
        dim += 1
    return dim

def get_pointer_dim(node: Node) -> int:
    # *(a + 0), *(*(a + m) + n), *(*(*(a + m) + n) + l)
    pointer = []
    def traverse(node, pointer):
        if node.type == 'pointer_expression':
            pointer.append(node)
        for child in node.children:
            traverse(child, pointer)
    traverse(node, pointer)
    return len(pointer)

def get_size(param_node: Node) -> str:
    if param_node.type == 'sizeof_expression':   # sizeof(type) * n 或 sizeof(type) * (n + m)
        expression = param_node.child_by_field_name('value') # (type) * n
        value = expression.child_by_field_name('value') # * n
        if value:
            size = value.child_by_field_name('argument') # n
        else:
            size = expression.child_by_field_name('left') # (unknown) * (n + m)
    elif param_node.type == 'binary_expression':   # s * sizeof(type)
        size = param_node.child_by_field_name('left')   # s
    elif param_node.type == 'number_literal':   # n
        size = param_node
    return text(size)

def is_nest_array(node: Node) -> bool:
    # a[b[i]]
    stack = []
    for c in text(node):
        if c == '[':
            if stack:
                return True
            stack.append(c)
        elif c == ']':
            stack.pop()
    return False

def get_left_id(node: Node) -> Union[Node, None]:
    while node:
        if node.type == 'binary_expression':
            node = node.child_by_field_name('left')
        elif node.type == 'identifier':
            return node
        else:
            return

'''==========================匹配========================'''
def rec_StaticMem(node: Node) -> bool:
    # type a[n],最多两维就够了
    if node.type == 'declaration':
        for child in node.children:
            if child.type == 'array_declarator':
                dim = get_array_dim(child)
                if dim < 3:
                    return True

def rec_DynMemOneLine(node: Node) -> bool:
    # type *a = (type *)malloc(sizeof(type) * n)
    if node.type == 'declaration':
        if node.children[1].type == 'init_declarator':
            if node.children[1].child_count == 3 and node.children[1].children[2].type == 'cast_expression':
                temp_node = node.children[1].children[2]
                if temp_node.child_count == 4 and temp_node.children[3].child_count and temp_node.children[3].children[0].text == b'malloc':
                    param_node = temp_node.children[3].children[1].children[1]
                    for child in param_node.children:
                        if child.type in ['number_literal', 'cast_expression', 'identifier']:
                            return True
                    
def rec_DynMemTwoLine(node: Node) -> bool:
    #int *p;   p = (type *)malloc(sizeof(type) * n)
    #declaration   expression_statement
    is_find = False
    for child in node.children:
        if child.type == 'expression_statement':
            if child.children[0].type == 'assignment_expression':
                id = child.children[0].children[0].text
                if child.children[0].children[2].type == 'cast_expression':
                    temp_node = child.children[0].children[2]
                    if temp_node.child_count == 4 and temp_node.children[3].child_count and temp_node.children[3].children[0].text == b'malloc':
                        param_node = temp_node.children[3].children[1].children[1]
                        for child in param_node.children:
                            if child.type in ['number_literal', 'cast_expression', 'identifier']:
                                is_find = True
                        if is_find:
                            break
    if is_find:     # 找到了malloc,接着找是否有定义
        for child in node.children:
            if child.type == 'declaration':
                if child.child_count > 1 and child.children[1].child_count > 1:
                    if child.children[1].children[1].text == id:
                        return True

def rec_DynMem(node: Node) -> bool:
    return rec_DynMemOneLine(node) or rec_DynMemTwoLine(node)

def rec_Array(node: Node) -> bool:
    # a[n] or a[m][n] or a[m][n][l]
    if node.type == 'subscript_expression' \
            and node.parent.type not in ['subscript_expression', 'pointer_expression', 'comma_expression'] \
            and node.children[0].type not in ['call_expression', 'field_expression', 'parenthesized_expression']:     # char *(a)[n] a[b[i]] &a[n] x.a[i]不处理
        if not is_nest_array(node): # 忽略嵌套的数组，例如a[b[i]]
            dim = get_array_dim(node)
            return dim < 4

def rec_Pointer(node: Node) -> bool:
    # *(*a + 0) or *(*(a + m) + n);
    if node.type == 'pointer_expression' and '&' not in text(node):
        dim = get_pointer_dim(node)
        while node.parent:
            if node.parent.type == 'pointer_expression':
                return False
            node = node.parent
        return dim < 4

'''==========================替换========================'''
def cvt_Static2Dyn(node: Node, code: str) -> List[Tuple[int, Union[int, str]]]:
    # type a[n] -> type *a = (type *)malloc(sizeof(type) * n)
    type = text(node.child_by_field_name('type'))
    indent = get_indent(node.start_byte, code)
    is_delete_line = True   # 整行是否都要删除，如果所有的元素都是array，例如int a[10], b[10];
    for i, child in enumerate(node.children):
        if child.type == 'struct_specifier':
            body = child.child_by_field_name('body')
            if body:    # 如果存在struct A {} a[10];这种情况，不处理
                return
        if child.type not in [',', ';', 'storage_class_specifier', 'primitive_type', 'struct_specifier']:
            if child.type != 'array_declarator':
                is_delete_line = False
    for child in node.children:
        if child.type == 'array_declarator':
            if child.children[0].type != 'identifier':
                return
            dim = get_array_dim(child)
            if dim == 1:
                id = text(child.children[0])
                size = text(child.children[2])
                str = f"{type} *{id} = ({type} *)malloc(sizeof({type}) * {size});"
            elif dim == 2:
                # type a[size_1][size_2]  -> 
                # type** a = (type**)malloc(size_1 * sizeof(type*));
                # for (int i = 0; i < size_1; i++) {
                #     a[i] = (type*)malloc(size_2 * sizeof(type));
                # }
                id = text(child.children[0].children[0])
                size_1 = text(child.children[0].children[2])
                size_2 = text(child.children[2])
                str = f"{type} **{id} = ({type} **)malloc(sizeof({type}*) * {size_1});\n" + \
                    f"{indent * ' '}for (int i = 0; i < {size_1}; i++) {{\n" + \
                    f"{(indent + 4) * ' '} {id}[i] = ({type}*)malloc(sizeof({type}) * {size_2});\n" + \
                    f"{indent * ' '}}}"
            else:
                return 
            if is_delete_line:  # 删除整行
                return [(node.end_byte, node.start_byte),
                        (node.start_byte, str)]
            else:   # 例如int a, b[10];只删除b[10]，并在下一行转换成malloc
                start_byte, end_byte = 0, 0
                flag = True
                if child.next_sibling and child.next_sibling.text == b',': 
                    flag = False
                    end_byte = child.next_sibling.end_byte
                else:
                    end_byte = child.end_byte
                if child.prev_sibling and child.prev_sibling.text == b',' and flag:
                    start_byte = child.prev_sibling.start_byte
                else:
                    start_byte = child.start_byte
                return [(end_byte, start_byte - end_byte),
                        (node.end_byte, f'\n{indent * " "}' + str)]
            return [(node.end_byte, node.start_byte),
                    (node.start_byte, str)]
        
def cvt_Dyn2Static(node: Node) -> List[Tuple[int, Union[int, str]]]:
    if rec_DynMemOneLine(node):
        # type *a = (type *)malloc(sizeof(type) * n) -> type a[n]
        type = text(node.children[0])
        id = text(node.children[1].children[0].children[1])
        param_node = node.children[1].children[2].children[3].children[1].children[1]   # sizeof(type) * n
        size = get_size(param_node)
        return [(node.end_byte, node.start_byte),
                (node.start_byte, f"{type} {id}[{size}];")]
    if rec_DynMemTwoLine(node):
        # int *p;   p = (type *)malloc(sizeof(type) * n) -> type a[n]
        ret = []
        for child in node.children:
            if child.type == 'expression_statement':
                if child.children[0].type == 'assignment_expression':
                    id = text(child.children[0].children[0])
                    if child.children[0].children[2].type == 'cast_expression':
                        temp_node = child.children[0].children[2]
                        type = text(temp_node.children[1].children[0])
                        param_node = temp_node.children[3].children[1].children[1]
                        size = get_size(param_node)
                        ret.append((child.end_byte, child.start_byte))
                        ret.append((child.start_byte, f"{type} {id}[{size}];"))
                        break
        for child in node.children:
            if child.type == 'declaration':
                if child.child_count > 1 and child.children[1].child_count > 1:
                    if text(child.children[1].children[1]) == id:
                        ret.append((child.end_byte, child.start_byte))
        return ret

def cvt_Array2Pointer(node: Node) -> List[Tuple[int, Union[int, str]]]:
    dim = get_array_dim(node)
    if dim == 1:
        # a[i] -> *(a + i)
        id = text(node.children[0])
        index = text(node.child_by_field_name('index'))
        return [(node.end_byte, node.start_byte),
                (node.start_byte, f"*({id} + {index})")]
    elif dim == 2:
        # a[i][j] -> *(*(a + i) + j);
        id = text(node.children[0].children[0])
        try:
            index_1 = text(node.children[0].children[1].children[1])
            index_2 = text(node.children[1].children[1])
            return [(node.end_byte, node.start_byte),
                    (node.start_byte, f"*(*({id} + {index_1}) + {index_2})")]
        except:
            return
    elif dim == 3:
        # a[i][j][k] -> *(*(*(a + i) + j) + k)
        id = text(node.children[0].children[0].children[0])
        try:
            index_1 = text(node.children[0].children[0].children[1].children[1])
            index_2 = text(node.children[0].children[1].children[1])
            index_3 = text(node.children[1].children[1])
            return [(node.end_byte, node.start_byte),
                    (node.start_byte, f"*(*(*({id} + {index_1}) + {index_2}) + {index_3})")]
        except:
            return

def cvt_Pointer2Array(node: Node, code: str) -> List[Tuple[int, Union[int, str]]]:
    dim = get_pointer_dim(node)
    try:
        if dim == 1:
            # *(a + i) -> a[i]
            argument = node.child_by_field_name('argument')
            if argument.child_count == 0:   # *p
                id = argument
                index = 0
            else:
                binary_expression = argument.children[1]
                id = get_left_id(binary_expression)
                if not id or not id.next_sibling:
                    return
                index = code[id.next_sibling.end_byte:binary_expression.end_byte]
            return [(node.end_byte, node.start_byte - node.end_byte),
                    (node.start_byte, f"{text(id)}[{index}]")]
        elif dim == 2:
            # *(*a + 0) -> a[i][j]
            binary_expression = node.child_by_field_name('argument').children[1]
            left = binary_expression.child_by_field_name('left')
            right = binary_expression.child_by_field_name('right')
            if not left or not right:
                return
            if left.type == 'pointer_expression':
                binary_expression = left.child_by_field_name('argument').children[1]
                if right and right.type in ['number_literal', 'identifier']:
                    index_2 = text(right) 
                else:   # *(*(a + i))
                    index_2 = 0
            elif right.type == 'pointer_expression' and left.type in ['number_literal', 'identifier']:
                binary_expression = right.child_by_field_name('argument').children[1]
                index_2 = text(left)
            else:
                return
            id = get_left_id(binary_expression)
            index_1 = code[id.next_sibling.end_byte:binary_expression.end_byte]
            return [(node.end_byte, node.start_byte - node.end_byte),
                    (node.start_byte, f"{text(id)}[{index_1}][{index_2}]")]
        elif dim == 3:
            # *(*(*(a + m) + n) + l) -> a[i][j][k]
            binary_expression = node.child_by_field_name('argument').children[1]
            left = binary_expression.child_by_field_name('left')
            right = binary_expression.child_by_field_name('right')
            if not left or not right:
                return
            if left.type == 'pointer_expression':
                binary_expression = left.child_by_field_name('argument').children[1]
                if right and right.type in ['number_literal', 'identifier']:
                    index_3 = text(right) 
                else:
                    index_3 = 0
            elif right.type == 'pointer_expression' and left.type in ['number_literal', 'identifier']:
                binary_expression = right.child_by_field_name('argument').children[1]
                index_3 = text(left)
            else:
                return
            left = binary_expression.child_by_field_name('left')
            right = binary_expression.child_by_field_name('right')
            if not left or not right:
                return
            if left.type == 'pointer_expression':
                binary_expression = left.child_by_field_name('argument').children[1]
                if right and right.type in ['number_literal', 'identifier']:
                    index_2 = text(right) 
                else:
                    index_2 = 0
            elif right.type == 'pointer_expression' and left.type in ['number_literal', 'identifier']:
                binary_expression = right.child_by_field_name('argument').children[1]
                index_2 = text(left)
            else:
                return
            index_1 = text(binary_expression.child_by_field_name('right'))
            id = text(binary_expression.child_by_field_name('left'))
            return [(node.end_byte, node.start_byte - node.end_byte),
                    (node.start_byte, f"{id}[{index_1}][{index_2}][{index_3}]")]
    except:
        return