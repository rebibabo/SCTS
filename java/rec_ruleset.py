def match_from_bytes(node, blob):
    return blob[node.start_byte:node.end_byte]

def rec_ReturnTernaryExpression(node, blob):
    if node.type == 'return_statement':
        if len(node.children) == 3 and node.children[1].type == 'ternary_expression':
            return True


def rec_IfElseReturn(node, blob):
    if node.type == 'if_statement':
        consequence = node.child_by_field_name('consequence')
        alternative = node.child_by_field_name('alternative')
        if consequence.type == 'block' and alternative and alternative.type == 'block' and len(consequence.children) == 3 and len(alternative.children) == 3:
            if alternative.children[1].type == 'return_statement' and consequence.children[1].type == 'return_statement':
                return True

def rec_IsEmpty(node, blob):
    if node.type == 'method_invocation' and node.child_by_field_name('object'):
        identifier = node.child_by_field_name('name')
        if match_from_bytes(identifier,blob) == 'isEmpty':
            return True

def rec_SizeEqZero(node, blob):
    if node.type == 'binary_expression':
        if node.child_by_field_name('operator').type == '==':
            left_node = node.child_by_field_name('left')
            right_node = node.child_by_field_name('right')
            if left_node.type == 'method_invocation' and right_node.type == 'decimal_integer_literal':
                left_identifier = left_node.child_by_field_name('name')
                if left_node.child_by_field_name('object') and match_from_bytes(left_identifier,blob) == 'size' and match_from_bytes(right_node,blob) == '0':
                    return True

def rec_UpdateExpressionAdd(node, blob):
    if node.type == 'update_expression':
        if node.parent.type == 'expression_statement' and len(node.children) == 2 and node.children[1].type == '++':
            return True

def rec_AssignmentSelfAdd(node, blob):
    # a += b;
    if node.type == 'assignment_expression' and len(node.children) == 3:
        if node.children[1].type == '+=':
            return True

def rec_AssignmentAdd(node, blob):
    # a = a + b;
    if node.type == 'assignment_expression' and len(node.children) == 3:
        left = node.child_by_field_name('left')
        right = node.child_by_field_name('right')
        if left is not None and right is not None and len(right.children) == 3:
            if right.children[1].type == '+' and left.type == right.children[0].type and match_from_bytes(left,blob) == match_from_bytes(right.children[0],blob):
                return True

def rec_UnequalNull(node, blob):
    if node.type == 'binary_expression':
        if len(node.children) == 3 and node.children[1].type == '!=' and node.children[2].type == 'null_literal':
            return True

def rec_NullUnequal(node, blob):
    if node.type == 'binary_expression':
        if len(node.children) == 3 and node.children[1].type == '!=' and node.children[0].type == 'null_literal':
            return True

def rec_InitString(node, blob):
    if node.type == 'string_literal':
        return True

def rec_InitNewString(node, blob):
    if node.type == 'object_creation_expression' and len(node.children) == 3 and node.children[1].type == 'type_identifier' and match_from_bytes(node.children[1],blob) == 'String' and len(node.children[2].children) == 3:
        return True

def rec_IndexOf(node, blob):
    if node.type == 'method_invocation' and node.child_by_field_name('object'):
        identifier = node.child_by_field_name('name')
        args = node.child_by_field_name('arguments')
        if match_from_bytes(identifier,blob) == 'indexOf' and args and len(args.children) == 3:
                return True

def rec_IndexOfStart(node, blob):
    if node.type == 'method_invocation' and node.child_by_field_name('object'):
        identifier = node.child_by_field_name('name')
        args = node.child_by_field_name('arguments')
        if match_from_bytes(identifier,blob) == 'indexOf' and args and len(args.children) == 5:
            if args.children[3].type == 'decimal_integer_literal' and match_from_bytes(args.children[3],blob) == '0':
                return True

def rec_EqualFalse(node, blob):
    if node.type == 'binary_expression':
        if len(node.children) == 3 and node.children[1].type == '==' and node.children[2].type == 'false':
            return True

def rec_UnequalTrue(node, blob):
    if node.type == 'binary_expression':
        if len(node.children) == 3 and node.children[1].type == '!=' and node.children[2].type == 'true':
            return True 

def rec_Not(node, blob):
    if node.type == 'unary_expression':
        if len(node.children) == 2 and node.children[0].type == '!':
            return True

        