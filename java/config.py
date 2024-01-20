from .transform0_var import *
from .transform1_op import *
from .transform2_update import *
from .transform3_string import *
from .transform4_bool import *
from .transform5_loop import *
from .transform6_array import *
from .transform7_if import *

transformation_operators = {
    'var': {
        'camel': (rec_identifier, cvt_camel, match_camel),
        'initcap': (rec_identifier, cvt_initcap, match_initcap),
        'underscore': (rec_identifier, cvt_underscore, match_underscore),
        'init_underscore': (rec_identifier, cvt_init_underscore, match_init_underscore),
        'init_dollar': (rec_identifier, cvt_init_dollar, match_init_dollar),
        'upper': (rec_identifier, cvt_upper, match_upper),
        'lower': (rec_identifier, cvt_lower, match_lower),
        'invichar': (rec_identifier, cvt_insertInviChar, match_inviChar),
        'hungarian': (rec_identifier, cvt_hungarian, match_hungarian),
    },
    'op': {
        'assignment': (rec_AugmentedAssignment, cvt_AugmentedAssignment2Assignment, rec_Assignment),
        'augmented_assignment': (rec_Assignment, cvt_Assignment2AugmentedAssignment, rec_AugmentedAssignment),
        'test_left_const': (rec_CmpRightConst, cvt_RightConst2LeftConst, match_LeftConst),
        'smaller': (rec_CmpOptBigger, cvt_Bigger2Smaller, rec_CmpOptSmaller),
        'bigger': (rec_CmpOptSmaller, cvt_Smaller2Bigger, rec_CmpOptBigger),
        'equal': (rec_Cmp, cvt_Equal, match_Equal),
        'not_equal': (rec_Cmp, cvt_NotEqual, match_NotEqual),
    },
    'update': {
        'left': (rec_ToLeft, cvt_ToLeft, rec_LeftUpdate),
        'right': (rec_ToRight, cvt_ToRight, rec_RightUpdate),
        'augment': (rec_ToAugment, cvt_ToAugment, rec_AugmentedCrement),
        'assignment': (rec_ToAssignment, cvt_ToAssignment, rec_Assignment)
    },
    'string': {
        'new_string': (rec_String, cvt_ToNewString, rec_NewString),
        'string': (rec_NewString, cvt_ToString, rec_String),
        'add': (rec_StringConcat, cvt_Concat2Add, match_StringAdd),
    },
    'bool': {
        'not_equal': (rec_EqualBool, cvt_Equal2NotEqual, rec_NotEqualBool),
        'equal': (rec_NotEqualBool, cvt_NotEqual2Equal, rec_EqualBool),
        'single': (rec_Bool, cvt_Binary2Single, match_Bool)
    },
    'loop': {
        'obc': (rec_For, cvt_OBC, match_ForOBC),
        'aoc': (rec_For, cvt_AOC, match_ForAOC),
        'abo': (rec_For, cvt_ABO, match_ForABO),
        'aoo': (rec_For, cvt_AOO, match_ForAOO),
        'obo': (rec_For, cvt_OBO, match_ForOBO),
        'ooc': (rec_For, cvt_OOC, match_ForOOC),
        'ooo': (rec_For, cvt_OOO, match_ForOOO),
        'for': (rec_loop, cvt_for, rec_For),
        'while': (rec_loop, cvt_while, match_While),
        'do_while': (rec_loop, cvt_do_while, match_DoWhile)
    },
    'array': {
        'index_zero': (rec_IndexOf, cvt_AddZero, rec_IndexOfStart),
        'index': (rec_IndexOfStart, cvt_DelZero, rec_IndexOf),
        'size': (rec_IsEmpty, cvt_IsEmpty2SizeEqZero, rec_SizeEqZero),
        'is_empty': (rec_SizeEqZero, cvt_SizeEqZero2IsEmpty, rec_IsEmpty),
    },
    'if': {
        'merge': (rec_IfMerge, cvt_IfSplit, rec_IfSplit),
        'switch': (rec_If, cvt_if2switch, rec_Switch),
        'if': (rec_Switch, cvt_switch2if, rec_If),
    },
}