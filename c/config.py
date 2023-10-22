from .transform0_var import *
from .transform1_blank import *
from .transform2_op import *
from .transform3_update import *
from .transform4_main import *
from .transform5_array import *
from .transform6_declare import *
from .transform7_loop import *

transformation_operators = {
    'var': {
        'camel': (rec_identifier, cvt_camel),
        'initcap': (rec_identifier, cvt_initcap),
        'underscore': (rec_identifier, cvt_underscore),
        'init_underscore': (rec_identifier, cvt_init_underscore),
        'init_dollar': (rec_identifier, cvt_init_dollar),
        'upper': (rec_identifier, cvt_upper),
        'lower': (rec_identifier, cvt_lower),
    },
    'blank': {
        'bracket_1': (rec_BracketSameLine, cvt_BracketSame2NextLine),
        'bracket_2': (rec_BracketNextLine, cvt_BracketNext2SameLine),
        'add_blank': (rec_OperatorOrSpliter, cvt_AddBlankSpace),
        'add_bracket': (rec_IfForWhileNoBracket, cvt_AddIfForWhileBracket),
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
    'main': {
        'int_void_return': (rec_Main, cvt_IntVoidReturn),
        'int_void': (rec_Main, cvt_IntVoid),
        'int_return': (rec_Main, cvt_IntReturn),
        'int': (rec_Main, cvt_Int),
        'int_arg_return': (rec_Main, cvt_IntArgReturn),
        'int_arg': (rec_Main, cvt_IntArg),
        'void_arg': (rec_Main, cvt_VoidArg),
        'void': (rec_Main, cvt_Void),
    },
    'array': {
        'dyn_mem': (rec_StaticMem, cvt_Static2Dyn),
        'static_mem': (rec_DynMem, cvt_Dyn2Static),
        'pointer': (rec_Array, cvt_Array2Pointer),
        'array': (rec_Pointer, cvt_Pointer2Array)
    },
    'declare': {
        'split': (rec_DeclareMerge, cvt_DeclareMerge2Split),
        'merge': (rec_DeclareSplit, cvt_DeclareSplit2Merge),
        'first': (rec_DeclareNotFirst, cvt_DeclareFirst),
        'temp': (rec_DeclareNotTemp, cvt_DeclareTemp)
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
        'while': (rec_For, cvt_while)
    },
}