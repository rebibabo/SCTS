from .transform0_var import *
from .transform1_print import *
from .transform2_list import *
from .transform3_dict import *
from .transform4_range import *
from .transform5_call import *
from .transform6_string import *
from .transform7_op import *
from .transform8_for import *
from .transform9_declare import *
from .transform10_return import *

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
    'print': {
        'add_flush': (rec_CallPrintWithoutFlush, cvt_CallPrint2CallPrintWithFlush),
        'del_flush': (rec_CallPrintWithFlush, cvt_CallPrintWithFlush2CallPrint),
        'add_end': (rec_CallPrintWithoutEnd, cvt_CallPrint2CallPrintWithEnd),
        'del_end': (rec_CallPrintWithEndn, cvt_CallPrintWithEndn2CallPrint),
    },
    'list': {
        'init_call_list': (rec_InitList, cvt_InitList2InitCallList),
        'init_list': (rec_InitCallList, cvt_InitCallList2InitList),
        'call_list': (rec_List, cvt_List2CallList),
        'list': (rec_CallList, cvt_CallList2List),
    },
    'dict': {
        'init_call_dict': (rec_InitDict, cvt_InitDict2InitCallDict),
        'init_dict': (rec_InitCallDict, cvt_InitCallDict2InitDict),
        'call_dict': (rec_Dict, cvt_Dict2CallDict),
        'dict': (rec_CallDict, cvt_CallDict2Dict)
    },
    'range': {
        'add_zero': (rec_CallRange, cvt_CallRange2CallRangeWithZero),
        'del_zero': (rec_CallRangeWithZero, cvt_CallRangeWithZero2CallRange),
        'add_slice_index': (rec_SubscriptSlice, cvt_AddSliceIndex),
        'del_slice_index': (rec_SubscriptSlice, cvt_DelSliceIndex),
        'add_index': (rec_ListIndex, cvt_AddIndex)
    },
    'call': {
        'add_magic_call': (rec_Call, cvt_Call2MagicCall),
        'del_magic_call': (rec_MagicCall, cvt_MagicCall2Call),
    },
    'string': {
        'single': (rec_string, cvt_single_quotation),
        'double': (rec_string, cvt_double_quotation),
        'add_f': (rec_not_format_string, cvt_add_f),
        'right_format': (rec_format_string_left, cvt_LeftF2RightFormat),
        'left_f': (rec_format_string_right, cvt_RightFormat2LeftF)
    },
    'op': {
        'augmented_assignment': (rec_AugmentedAssignment, cvt_AugmentedAssignment2Assignment),
        'assignment': (rec_Assignment, cvt_Assignment2AugmentedAssignment),
        'test_left_const': (rec_CmpRightConst, cvt_RightConst2LeftConst),
        'smaller': (rec_CmpOptBigger, cvt_Bigger2Smaller),
        'bigger': (rec_CmpOptSmaller, cvt_Smaller2Bigger),
    },
    'for': {
        'add_enumerate': (rec_ForIter, cvt_AddEnumerate),
        'while': (rec_ForRange, cvt_ForRange2While),
        'for': (rec_ListComprehension, cvt_ListComprehension2For)
    },
    'declare': {
        'split': (rec_AssignmentMerge, cvt_Merge2Split),
        'merge_simple': (rec_AssignmentMergeSame, cvt_Merge2MergeSimple),
        'merge': (rec_MultiAssignment, cvt_Split2Merge)
    },
    'return': {
        'add_bracket': (rec_MultiReturnNotTuple, cvt_ReturnTuple),
        'del_bracket': (rec_MultiReturnWithTuple, cvt_ReturnWithoutTuple),
        'add_None': (rec_MultiReturnWithoutNone, cvt_AddNone),
        'del_None': (rec_MultiReturnWithNone, cvt_DelNone)
    },
}

