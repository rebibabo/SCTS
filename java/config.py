
from .cvt_ruleset import *
from .rec_ruleset import *

transformation_operators = {
    'if_else_return': {
        'rec': rec_IfElseReturn,
        'rec_eq': rec_ReturnTernaryExpression,
        'cvt': cvt_IfElseReturn2ReturnTernaryExpression,
    },
    'is_empty': {
        'rec': rec_IsEmpty,
        'rec_eq': rec_SizeEqZero,
        'cvt': cvt_IsEmpty2SizeEqZero,
        'cvt_eq': cvt_SizeEqZero2IsEmpty,
    },
    'self_add': {
        'rec': rec_AssignmentSelfAdd,
        'rec_eq': rec_AssignmentAdd,
        'cvt': cvt_AssignmentSelfAdd2AssignmentAdd,
        'cvt_eq': cvt_AssignmentAdd2AssignmentSelfAdd,
    },
    'unequal_null': {
        'rec': rec_UnequalNull,
        'rec_eq': rec_NullUnequal,
        'cvt': cvt_UnequalNull2NullUnequal,
        'cvt_eq': cvt_NullUnequal2UnequalNull,
    },
    'init_string': {
        'rec': rec_InitString,
        'rec_eq': rec_InitNewString,
        'cvt': cvt_InitString2InitNewString,
        'cvt_eq': cvt_InitNewString2InitString,
    },
    'index_of': {
        'rec': rec_IndexOf,
        'rec_eq': rec_IndexOfStart,
        'cvt': cvt_IndexOf2IndexOfStart,
        'cvt_eq': cvt_IndexOfStart2IndexOf,
    },
    'not': {
        'rec': rec_Not,
        'rec_eq': rec_EqualFalse,
        'cvt': cvt_Not2EqualFalse,
        'cvt_eq': cvt_EqualFalse2Not,
    },
    'equal_false': {
        'rec': rec_EqualFalse,
        'rec_eq': rec_UnequalTrue,
        'cvt': cvt_EqualFalse2UnequalTrue,
        'cvt_eq': cvt_UnequalTrue2EqualFalse,
    }
}

