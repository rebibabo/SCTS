from .rec_ruleset import *
from ..utils import match_from_bytes


def cvt_IfElseReturn2ReturnTernaryExpression(node, blob):
    if rec_IfElseReturn(node, blob):
        condition_node = node.child_by_field_name('condition').children[1]
        condition_str = match_from_bytes(condition_node, blob)
        consequence_node = node.child_by_field_name('consequence').children[1].children[1]
        consequence_str = match_from_bytes(consequence_node, blob)
        alternative_node = node.child_by_field_name('alternative').children[1].children[1]
        alternative_str = match_from_bytes(alternative_node,blob)

        final_str = "return {} ? {} : {};".format(condition_str, consequence_str, alternative_str)
        return final_str
        # return replace_from_blob(node, return_ternary, blob, parent_node=node)

def cvt_IsEmpty2SizeEqZero(node, blob):
    if rec_IsEmpty(node, blob):
        obj = node.child_by_field_name('object')
        obj_str = match_from_bytes(obj, blob)
        final_str = "{}.size() == 0".format(obj_str)
        return final_str

def cvt_SizeEqZero2IsEmpty(node, blob):
    # a.size() == 0 => a.isEmpty()
    if rec_SizeEqZero(node, blob):
        obj = node.child_by_field_name('left').child_by_field_name('object')
        obj_str = match_from_bytes(obj, blob)
        final_str = "{}.isEmpty()".format(obj_str)
        return final_str


def cvt_UpdateExpressionAdd2AssignmentExpression(node, blob):
    if rec_UpdateExpressionAdd(node, blob):
        identifier_str = match_from_bytes(node.children[0], blob)
        final_str = "{} = {} + 1".format(identifier_str, identifier_str)
        return final_str

def cvt_AssignmentSelfAdd2AssignmentAdd(node, blob):
    if rec_AssignmentSelfAdd(node, blob):
        identifier_str = match_from_bytes(node.children[0], blob)
        target_str = match_from_bytes(node.children[2], blob)
        final_str = "{} = {} + {}".format(identifier_str, identifier_str, target_str)
        return final_str 

def cvt_AssignmentAdd2AssignmentSelfAdd(node, blob):
    # a = a + 1; => a += 1;
    if rec_AssignmentAdd(node, blob):
        identifier_str = match_from_bytes(node.children[0], blob)
        target_str = match_from_bytes(node.children[2].children[-1], blob)
        final_str = "{} += {}".format(identifier_str, target_str)
        return final_str

def cvt_UnequalNull2NullUnequal(node, blob):
    if rec_UnequalNull(node, blob):
        left_str = match_from_bytes(node.children[0], blob)
        final_str = "null != {}".format(left_str)
        return final_str

def cvt_NullUnequal2UnequalNull(node, blob):
    if rec_NullUnequal(node, blob):
        right_str = match_from_bytes(node.children[2], blob)
        final_str = "{} != null".format(right_str)
        return final_str

def cvt_InitString2InitNewString(node, blob):
    if rec_InitString(node, blob):
        strings = match_from_bytes(node, blob)
        final_str = f'new String({strings})'
        return final_str

def cvt_InitNewString2InitString(node, blob):
    if rec_InitNewString(node, blob):
        args = node.children[2]
        strings = match_from_bytes(args.children[1], blob)
        final_str = f"{strings}"
        return final_str

def cvt_IndexOf2IndexOfStart(node, blob):
    if rec_IndexOf(node, blob):
        obj = node.child_by_field_name('object')
        args = node.child_by_field_name('arguments')
        obj_str = match_from_bytes(obj, blob)
        arg_str = match_from_bytes(args.children[1], blob)
        final_str = f"{obj_str}.indexOf({arg_str}, 0)"
        return final_str

def cvt_IndexOfStart2IndexOf(node, blob):
    if rec_IndexOfStart(node, blob):
        obj = node.child_by_field_name('object')
        args = node.child_by_field_name('arguments')
        obj_str = match_from_bytes(obj, blob)
        arg_str = match_from_bytes(args.children[1], blob)
        final_str = f"{obj_str}.indexOf({arg_str})"
        return final_str

def cvt_EqualFalse2Not(node, blob):
    if rec_EqualFalse(node, blob):
        obj = node.children[0]
        obj_str = match_from_bytes(obj, blob)
        final_str = f"!{obj_str}"
        return final_str

def cvt_Not2EqualFalse(node, blob):
    if rec_Not(node, blob):
        obj = node.children[1]
        obj_str = match_from_bytes(obj, blob)
        final_str = f"{obj_str} == false"
        return final_str


def cvt_EqualFalse2UnequalTrue(node, blob):
    if rec_EqualFalse(node, blob):
        obj = node.children[0]
        obj_str = match_from_bytes(obj, blob)
        final_str = f"{obj_str} != true"
        return final_str

def cvt_UnequalTrue2EqualFalse(node, blob):
    if rec_UnequalTrue(node, blob):
        obj = node.children[0]
        obj_str = match_from_bytes(obj, blob)
        final_str = f"{obj_str} == false"
        return final_str


if __name__ == '__main__':
    test = Tester()
  
