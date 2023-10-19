from .transform0_var import *
from .transform1_print import *
from .transform2_list import *
from .transform3_dict import *
from .transform4_range import *
from .transform5_call import *

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
        'list': (rec_CallList, cvt_CallList2List)
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
    },
    'call': {
        'add_magic_call': (rec_Call, cvt_Call2MagicCall),
        'del_magic_call': (rec_MagicCall, cvt_MagicCall2Call),
    },
}

