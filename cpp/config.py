from .transform0_var import *
from .transform1_blank import *
from .transform2_op import *
from .transform3_update import *
from .transform4_main import *
from .transform5_array import *
from .transform6_declare import *
from .transform7_loop import *
from .transform8_if import *
from .transform9_cpp import *

transformation_operators = {
    'var': {
        'camel': (rec_identifier, cvt_camel, match_camel),
        'initcap': (rec_identifier, cvt_initcap, match_initcap),
        'underscore': (rec_identifier, cvt_underscore, match_underscore),
        'init_underscore': (rec_identifier, cvt_init_underscore, match_init_underscore),
        'init_dollar': (rec_identifier, cvt_init_dollar, match_init_dollar),
        'upper': (rec_identifier, cvt_upper, match_upper),
        'lower': (rec_identifier, cvt_lower, match_lower),
        'hungarian': (rec_identifier, cvt_hungarian, match_hungarian),
    },
    'blank': {
        'bracket_1': (rec_BracketSameLine, cvt_BracketSame2NextLine, rec_BracketNextLine),
        'bracket_2': (rec_BracketNextLine, cvt_BracketNext2SameLine, rec_BracketSameLine),
        'add_blank': (rec_OperatorOrSpliter, cvt_AddBlankSpace, rec_OperatorOrSpliter),
        'add_bracket': (rec_IfForWhileNoBracket, cvt_AddIfForWhileBracket, rec_IfForWhileHasBracket),
        'del_bracket': (rec_IfForWhileHasBracket, cvt_DelIfForWhileBracket, rec_IfForWhileNoBracket),
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
    'main': {
        'int_void_return': (rec_Main, cvt_IntVoidReturn, match_IntVoidReturn),
        'int_void': (rec_Main, cvt_IntVoid, match_IntVoid),
        'int_return': (rec_Main, cvt_IntReturn, match_IntReturn),
        'int': (rec_Main, cvt_Int, match_Int),
        'int_arg_return': (rec_Main, cvt_IntArgReturn, match_IntArgReturn),
        'int_arg': (rec_Main, cvt_IntArg, match_IntArg),
        'void_arg': (rec_Main, cvt_VoidArg, match_VoidArg),
        'void': (rec_Main, cvt_Void, match_Void),
    },
    'array': {
        'dyn_mem': (rec_StaticMem, cvt_Static2Dyn, rec_DynMem),
        'static_mem': (rec_DynMem, cvt_Dyn2Static, rec_StaticMem),
        'pointer': (rec_Array, cvt_Array2Pointer, rec_Pointer),
        'array': (rec_Pointer, cvt_Pointer2Array, rec_Array),
    },
    'declare': {
        'split': (rec_DeclareMerge, cvt_DeclareMerge2Split, rec_DeclareSplit),
        'merge': (rec_DeclareSplit, cvt_DeclareSplit2Merge, rec_DeclareMerge),
        'first': (rec_DeclareNotFirst, cvt_DeclareFirst, rec_DeclareNotTemp),
        'temp': (rec_DeclareNotTemp, cvt_DeclareTemp, rec_DeclareNotFirst),
        'assign_split': (rec_DeclareAssign, cvt_DeclareAssignSplit, match_AssignSplit)
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
    'if': {
        'merge': (rec_IfMerge, cvt_IfSplit, rec_IfSplit),
        'switch': (rec_If, cvt_if2switch, rec_Switch),
        'if': (rec_Switch, cvt_switch2if, rec_If),
    },
    'cpp': {
        'stdc++': (rec_Include, cvt_AddBitsStd, match_Include),
        'namespace': (rec_NameSpaceStd, cvt_AddStd, match_NameSpaceStd),
        'sync_with_false': (rec_MainWithoutSync, cvt_AddSyncWithFalse, match_MainWithSync),
        'struct': (rec_StructDeclare, cvt_DelStruct, match_StructDeclare),
        'coutendl': (rec_Printf, cvt_Printf2CoutEndl, match_CoutEndl),
        'cout': (rec_Printf, cvt_Printf2Cout, rec_Cout),
        'del_endl': (rec_Cout, cvt_DelEndl, match_CoutNoEndl),
        'printf': (rec_Cout, cvt_Cout2Printf, rec_Printf),
        'cin': (rec_Scanf, cvt_Scanf2Cin, rec_Cin),
        'scanf': (rec_Cin, cvt_Cin2Scanf, rec_Scanf),
    },
}