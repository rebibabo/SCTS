from .transform0_var import *
from .transform1_op import *
from .transform2_update import *
from .transform3_string import *
from .transform4_bool import *
from .transform5_loop import *
from .transform6_array import *

transformation_operators = {
    'var': {
        'camel': (rec_identifier, cvt_camel),
        'initcap': (rec_identifier, cvt_initcap),
        'underscore': (rec_identifier, cvt_underscore),
        'init_underscore': (rec_identifier, cvt_init_underscore),
        'init_dollar': (rec_identifier, cvt_init_dollar),
        'upper': (rec_identifier, cvt_upper),
        'lower': (rec_identifier, cvt_lower),
        'invichar': (rec_identifier, cvt_insertInviChar),
    },
    'op': {
        'augmented_assignment': (rec_AugmentedAssignment, cvt_AugmentedAssignment2Assignment),
        'assignment': (rec_Assignment, cvt_Assignment2AugmentedAssignment),
        'test_left_const': (rec_CmpRightConst, cvt_RightConst2LeftConst),
        'smaller': (rec_CmpOptBigger, cvt_Bigger2Smaller),
        'bigger': (rec_CmpOptSmaller, cvt_Smaller2Bigger),
    },
    'update': {
        'left': (rec_ToLeft, cvt_ToLeft),
        'right': (rec_ToRight, cvt_ToRight),
        'augment': (rec_ToAugment, cvt_ToAugment),
        'assignment': (rec_ToAssignment, cvt_ToAssignment)
    },
    'string': {
        'new_string': (rec_String, cvt_ToNewString),
        'string': (rec_NewString, cvt_ToString),
        'add': (rec_StringConcat, cvt_Concat2Add),
    },
    'bool': {
        'not_equal': (rec_EqualBool, cvt_Equal2NotEqual),
        'equal': (rec_NotEqualBool, cvt_NotEqual2Equal),
        'single': (rec_Bool, cvt_Binary2Single)
    },
    'loop': {
        'obc': (rec_For, cvt_OBC),
        'aoc': (rec_For, cvt_AOC),
        'abo': (rec_For, cvt_ABO),
        'aoo': (rec_For, cvt_AOO),
        'obo': (rec_For, cvt_OBO),
        'ooc': (rec_For, cvt_OOC),
        'ooo': (rec_For, cvt_OOO),
        'for': (rec_while, cvt_for),
        'while': (rec_For, cvt_while),
    },
    'array': {
        'index_zero': (rec_IndexOf, cvt_AddZero),
        'index': (rec_IndexOfStart, cvt_DelZero),
        'size': (rec_IsEmpty, cvt_IsEmpty2SizeEqZero),
        'is_empty': (rec_SizeEqZero, cvt_SizeEqZero2IsEmpty),
    },
}