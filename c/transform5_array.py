from utils import replace_from_blob, traverse_rec_func, text

def get_indent(start_byte, code):
    indent = 0
    i = start_byte
    while i >= 0 and code[i] != '\n':
        if code[i] == ' ':
            indent += 1
        elif code[i] == '\t':
            indent += 8
        i -= 1
    return indent
    
def get_array_dim(node):
    # a[i], a[i][j]
    dim = 0
    temp_node = node
    while temp_node.child_count:
        temp_node = temp_node.children[0]
        dim += 1
    return dim

def get_pointer_dim(node):
    # *(*a + 0) = 0, *(*(a + m) + n) = 0, *(*(*(a + m) + n) + l)
    dim = 0
    is_match = True
    while node and is_match:
        is_match = False
        if node.type == 'pointer_expression':
            if node.children[1].type == 'parenthesized_expression':
                if node.children[1].children[1].type == 'binary_expression':
                    dim += 1
                    node = node.children[1].children[1].children[0]
                    is_match = True
    return dim

'''==========================匹配========================'''
def rec_StaticMem(node):
    # type a[n],最多两维就够了
    if node.type == 'declaration':
        for child in node.children:
            if child.type == 'array_declarator':
                dim = get_array_dim(child)
                if dim < 3:
                    return True

def rec_DynMemOneLine(node):
    # type *a = (type *)malloc(sizeof(type) * n)
    if node.type == 'declaration':
        if node.children[1].type == 'init_declarator':
            if node.children[1].child_count == 3 and node.children[1].children[2].type == 'cast_expression':
                temp_node = node.children[1].children[2]
                if temp_node.child_count == 4 and temp_node.children[3].child_count and temp_node.children[3].children[0].text == b'malloc':
                    param_node = temp_node.children[3].children[1].children[1]
                    for child in param_node.children:
                        if child.type in ['number_literal', 'identifier']:
                            return True
                    
def rec_DynMemTwoLine(node):
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
                            if child.type in ['number_literal', 'identifier']:
                                is_find = True
                        if is_find:
                            break
    if is_find:     # 找到了malloc,接着找是否有定义
        for child in node.children:
            if child.type == 'declaration':
                if child.child_count > 1 and child.children[1].child_count > 1:
                    if child.children[1].children[1].text == id:
                        return True

def rec_DynMem(node):
    return rec_DynMemOneLine(node) or rec_DynMemTwoLine(node)

def rec_Array(node):
    # a[n] or a[m][n] or a[m][n][l]
    if node.type == 'subscript_expression' and node.parent.type != 'subscript_expression':
        dim = get_array_dim(node)
        return dim < 4

def rec_Pointer(node):
    # *(*a + 0) = 0 or *(*(a + m) + n) = 0;
    if node.type == 'assignment_expression' and node.children[0].type == 'pointer_expression':
        # for each in node.children[0].children[1].children[1].children[0].children:
        dim = get_pointer_dim(node.children[0])
        return dim < 4

'''==========================替换========================'''
def cvt_Static2Dyn(node, code):
    # type a[n] -> type *a = (type *)malloc(sizeof(type) * n)
    type = text(node.children[0])
    indent = get_indent(node.start_byte, code)
    is_delete_line = True   # 整行是否都要删除，如果所有的元素都是array，例如int a[10], b[10]
    for i, child in enumerate(node.children):
        if child.type != 'array_declarator' and i % 2:
            is_delete_line = False
    for child in node.children:
        if child.type == 'array_declarator':
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
                return [(node.end_byte, node.start_byte - node.end_byte),
                        (node.start_byte, str)]
            else:   # 例如int a, b[10];只删除b[10]，并在下一行转换成malloc
                start_byte, end_byte = 0, 0
                if child.next_sibling and child.next_sibling.text == b',':
                    end_byte = child.next_sibling.end_byte
                else:
                    end_byte = child.end_byte
                if child.prev_sibling and child.prev_sibling.text == b',':
                    start_byte = child.prev_sibling.end_byte
                else:
                    start_byte = child.start_byte
                return [(end_byte, start_byte - end_byte),
                        (node.end_byte, f'\n{indent * " "}' + str)]
            return [(node.end_byte, node.start_byte - node.end_byte),
                    (node.start_byte, str)]
        
def cvt_Dyn2Static(node):
    if rec_DynMemOneLine(node):
        # type *a = (type *)malloc(sizeof(type) * n) -> type a[n]
        type = text(node.children[0])
        id = text(node.children[1].children[0].children[1])
        param_node = node.children[1].children[2].children[3].children[1].children[1]
        for child in param_node.children:
            if child.type in ['number_literal', 'identifier']:
                size = text(child)
        return [(node.end_byte, node.start_byte - node.end_byte),
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
                        size = text(param_node)
                        for ch in param_node.children:
                            if ch.type in ['number_literal', 'identifier']:
                                size = text(ch)
                        ret.append((child.end_byte, child.start_byte - child.end_byte))
                        ret.append((child.start_byte, f"{type} {id}[{size}];"))
                        break
        for child in node.children:
            if child.type == 'declaration':
                if child.child_count > 1 and child.children[1].child_count > 1:
                    if text(child.children[1].children[1]) == id:
                        ret.append((child.end_byte, child.start_byte - child.end_byte))
        return ret

def cvt_Array2Pointer(node):
    dim = get_array_dim(node)
    if dim == 1:
        # a[i] -> *(*a + i)
        id = text(node.children[0])
        index = text(node.children[2])
        return [(node.end_byte, node.start_byte - node.end_byte),
                (node.start_byte, f"*(*{id} + {index})")]
    elif dim == 2:
        # a[i][j] -> *(*(a + i) + j);
        id = text(node.children[0].children[0])
        if len(node.children[0].children) < 3 or len(node.children) < 3:
            return
        index_1 = text(node.children[0].children[2])
        index_2 = text(node.children[2])
        return [(node.end_byte, node.start_byte - node.end_byte),
                (node.start_byte, f"*(*({id} + {index_1}) + {index_2})")]
    elif dim == 3:
        # a[i][j][k] -> *(*(*(a + i) + j) + k)
        id = text(node.children[0].children[0].children[0])
        if len(node.children[0].children[0].children) < 3 or len(node.children[0].children) < 3 or len(node.children) < 3:
            return
        index_1 = text(node.children[0].children[0].children[2])
        index_2 = text(node.children[0].children[2])
        index_3 = text(node.children[2])
        return [(node.end_byte, node.start_byte - node.end_byte),
                (node.start_byte, f"*(*(*({id} + {index_1}) + {index_2}) + {index_3})")]

def cvt_Pointer2Array(node):
    dim = get_pointer_dim(node.children[0])
    if dim == 1:
        temp_node = node.children[0].children[1].children[1]
        if temp_node.children[0].child_count < 2:
            return
        id = text(temp_node.children[0].children[1])
        index = text(temp_node.children[2])
        return [(node.children[0].end_byte, node.children[0].start_byte - node.children[0].end_byte),
                (node.start_byte, f"{id}[{index}]")]
    elif dim == 2:
        temp_node = node.children[0].children[1].children[1]
        index_2 = text(temp_node.children[2])
        temp_node = temp_node.children[0].children[1].children[1]
        index_1 = text(temp_node.children[2])
        id = text(temp_node.children[0])
        return [(node.children[0].end_byte, node.children[0].start_byte - node.children[0].end_byte),
                (node.start_byte, f"{id}[{index_1}][{index_2}]")]
    elif dim == 3:
        temp_node = node.children[0].children[1].children[1]
        index_3 = text(temp_node.children[2])
        temp_node = temp_node.children[0].children[1].children[1]
        index_2 = text(temp_node.children[2])
        temp_node = temp_node.children[0].children[1].children[1]
        index_1 = text(temp_node.children[2])
        id = text(temp_node.children[0])
        return [(node.children[0].end_byte, node.children[0].start_byte - node.children[0].end_byte),
                (node.start_byte, f"{id}[{index_1}][{index_2}][{index_3}]")]