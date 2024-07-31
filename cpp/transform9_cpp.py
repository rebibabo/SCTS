from utils import text
from tree_sitter import Node
from typing import List, Tuple, Union, Dict
from .transform5_array import get_array_dim
from .transform6_declare import contain_id
import re

def find_format_specifiers(format_string: str) -> Tuple[List[str], List[Tuple[int, int]]]:
    # 使用正则表达式查找格式化字符串中的所有%的列表以及对应的位置切片
    format_specifiers = re.findall(r'%[-+]?\d*\.*\d*[cCdiouxXeEfgGsSpn]', format_string)
    format_specifiers_indices = list(re.finditer(r'%[-+]?\d*\.*\d*[cCdiouxXeEfgGsSpn]', format_string))
    indices = [(match.start(), match.end()) for match in format_specifiers_indices]
    return format_specifiers, indices

def get_ids_type(node: Node) -> Dict[str, str]:
    # 返回node代码块中所有变量名的类型
    id_type_dict = {}
    for child in node.children:
        if child.type == 'declaration':
            type = text(child.children[0])
            for id in child.children[1: -1]:
                if id.type == ',':
                    continue
                id_node = id
                if id.type == 'init_declarator':      # 如果是变量名申明和赋值同时进行
                    id_node = id.children[0]    # 则变量名为第一个子节点
                if id_node.type == 'array_declarator':   # 如果是数组型
                    dim = get_array_dim(id_node)
                    id_type_dict[text(id_node)] = type + dim*'*'
                elif id_node.type == 'pointer_declarator':   # 如果是指针类型
                    dim = text(id_node).count('*')
                    id_type_dict[text(id_node)[dim:]] = type + dim*'*'
                else:
                    id_type_dict[text(id_node)] = type
    return id_type_dict

def type2format(type: str) -> str:
    if type in ['int', 'short', 'short int', 'int short', 'unsigned', 'unsigned int', 'unsigned short int']:
        return '%' + ('u' if 'unsigned' in type else '') + 'd'
    if type in ['char', 'unsigned char']:
        return '%' + ('u' if 'unsigned' in type else '') + 'c'
    if type in ['char*', 'string']:
        return '%s'
    if type in ['double', 'float']:
        return '%f'
    if type in ['long', 'unsigned long long']:
        return '%' + ('u' if 'unsigned' in type else '') + 'ld'
    if type in ['long long', 'unsinged long long']:
        return '%' + ('u' if 'unsigned' in type else '') + 'lld'

def get_stream_info(node: Node, stream_type: str) -> Union[Tuple[str, str], None]:
    stream, stream_node = [], []
    n = node.children[0]
    while n:
        stream.insert(0, text(n.children[2]))
        stream_node.insert(0, n.children[2])
        n = n.children[0]
        if text(n) == stream_type:
            break
    ids_type = {}
    while n:
        if n.type == 'compound_statement':
            temp_ids_type = get_ids_type(n)
            ids_type.update(temp_ids_type)
        n = n.parent
    format_str = ""
    params = []
    temp_dict = {}
    for id, type in ids_type.items():
        if '[' in id:   # 如果是a[i]这样的
            dim = id.count('[')
            orig_id = id[:id.find('[')]
            temp_dict[orig_id] = type
        else:
            temp_dict[id] = type
    ids_type = temp_dict
    # input(text(node))
    # input(ids_type)
    type = ''
    for i, each in enumerate(stream):
        if each[0] == '"' and each[-1] == '"':
            format_str += each[1: -1]
        elif each == 'endl':
            format_str += '\\n'
        else:
            id = each
            if each not in ids_type.keys():
                is_return = True
                if stream_node[i].type in ['binary_expression', 'cast_expression']: # 如果是二元表达式，则获取右边的变量的类型
                    ids_name = set()
                    contain_id(stream_node[i], ids_name)
                    if len(ids_name):
                        id = list(ids_name)[0]
                        if id not in ids_type.keys():
                            if '[' in id:   # 如果是a[i]这样的
                                dim = id.count('[')
                                orig_id = id[:id.find('[')]
                                if orig_id in ids_type.keys():
                                    type = ids_type[orig_id][:-dim] # 几维就删掉几颗*
                                    is_return = False
                        else:
                            type = ids_type[id]
                            is_return = False
                if '[' in id:   # 如果是a[i]这样的
                    dim = id.count('[')
                    orig_id = id[:id.find('[')]
                    if orig_id in ids_type.keys():
                        type = ids_type[orig_id][:-dim] # 几维就删掉几颗*
                        is_return = False
                if is_return:
                    return
            else:
                type = ids_type[each]
            format = type2format(type)
            if format is None:
                return
            format_str += format
            if stream_type == 'cin':
                if each in ids_type.keys() and ids_type[each] == 'char*':
                    pass
                else:
                    each = '&' + each
            params.append(each)
    for i, param in enumerate(params):  
        if param in ids_type.keys() and ids_type[param] == 'string': # 如果是string类型，要转换成c的字符串c_str()
            if stream_type == 'cin':
                return
            params[i] += '.c_str()'
    params_str = ', '.join(params)
    if len(params_str) > 0:
        params_str = ', '  + params_str
    return format_str, params_str

'''==========================匹配========================'''
def rec_Include(node: Node) -> bool:
    # 没有include<bits/stdc++.h>
    if node.type == 'translation_unit':
        for child in node.children:
            if child.type == 'preproc_include':
                if text(child.children[1]).replace(' ', '') == '<bits/stdc++.h>':
                    return
        return True

def match_Include(node: Node) -> bool:
    # 有include<bits/stdc++.h>
    if node.type == 'translation_unit':
        for child in node.children:
            if child.type == 'preproc_include':
                if text(child.children[1]).replace(' ', '') == '<bits/stdc++.h>':
                    return True

def rec_NameSpaceStd(node: Node) -> bool:
    # 没有using namespace std;
    if node.type == 'translation_unit':
        for child in node.children:
            if child.type == 'using_declaration':
                if text(child).replace(' ', '') == 'usingnamespacestd;':
                    return
        return True

def match_NameSpaceStd(node: Node) -> bool:
    # 有using namespace std;
    if node.type == 'translation_unit':
        for child in node.children:
            if child.type == 'using_declaration':
                if text(child).replace(' ', '') == 'usingnamespacestd;':
                    return True

def rec_MainWithoutSync(node: Node) -> bool:
    # 没有ios::sync_with_stdio(false);
    if node.type == 'function_definition':
        func_name = text(node.child_by_field_name('declarator').children[0])
        if func_name == 'main':
            body = node.child_by_field_name('body')
            for child in body.children:
                if child.type == 'expression_statement':
                    if child.children[0].type == 'call_expression':
                        if text(child.children[0].children[0]) == 'ios::sync_with_stdio':
                            return
            return True

def match_MainWithSync(node: Node) -> bool:
    # 有ios::sync_with_stdio(false);
    if node.type == 'function_definition':
        func_name = text(node.child_by_field_name('declarator').children[0])
        if func_name == 'main':
            body = node.child_by_field_name('body')
            for child in body.children:
                if child.type == 'expression_statement':
                    if child.children[0].type == 'call_expression':
                        if text(child.children[0].children[0]) == 'ios::sync_with_stdio':
                            return True

def rec_StructDeclare(node: Node) -> bool:
    # struct node a;
    if node.type == 'declaration':
        if node.children[0].type == 'struct_specifier' and not node.children[0].child_by_field_name('body'):
            return True

def match_StructDeclare(node: Node) -> bool:
    # node a;
    if node.type == 'declaration':
        if node.children[0].type == 'type_identifier':
            return True

def rec_Printf(node: Node) -> bool:
    if node.type == 'call_expression':
        if node.child_by_field_name('function'):
            func_name = text(node.child_by_field_name('function'))
            if func_name == 'printf':
                return True

def rec_Cout(node: Node) -> bool:
    # 判断是否是cout
    if node.type == 'expression_statement':
        node = node.children[0]
        while node:
            if node.type == 'binary_expression':
                node = node.children[0]
            elif text(node) == 'cout' and node.next_sibling.type == '<<':
                return True
            else:
                return

def match_CoutEndl(node: Node) -> bool:
    # 判断是否是cout << endl
    if rec_Cout(node):
        if 'endl' in text(node):
            return True

def match_CoutNoEndl(node: Node) -> bool:
    # 判断是否是cout << str
    if rec_Cout(node):
        if 'endl' not in text(node):
            return True

def rec_Scanf(node: Node) -> bool:
    if node.type == 'call_expression':
        if node.child_by_field_name('function'):
            func_name = text(node.child_by_field_name('function'))
            if func_name == 'scanf':
                return True

def rec_Cin(node: Node) -> bool:
    # 判断是否是cin
    if node.type == 'expression_statement':
        node = node.children[0]
        while node:
            if node.type == 'binary_expression':
                node = node.children[0]
            elif text(node) == 'cin' and node.next_sibling.type == '>>':
                return True
            else:
                return

'''==========================替换========================'''
def cvt_AddBitsStd(node: Node) -> List[Tuple[int, Union[int, str]]]:
    return [(0, '#include<bits/stdc++.h>\n')]

def cvt_AddStd(node: Node) -> List[Tuple[int, Union[int, str]]]:
    insert_index = 0
    for child in node.children:
        if child.type == 'function_definition':
            if len(child.children[1].children) == 0:
                return 
            if child.children[1].children[0].text == b'main':
                insert_index = child.start_byte
    return [(insert_index, f"using namespace std;\n")]

def cvt_AddSyncWithFalse(node: Node) -> List[Tuple[int, Union[int, str]]]:
    body = node.child_by_field_name('body')
    return [(body.children[1].start_byte, "ios::sync_with_stdio(false);\n    ")]

def cvt_DelStruct(node: Node) -> List[Tuple[int, Union[int, str]]]:
    struct_node = node.children[0].children[0]
    id_node = node.children[0].children[1]
    return [(id_node.start_byte, struct_node.start_byte)]

def cvt_Printf2CoutEndl(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # printf("format_str", params); -> cout << str << param_1 << str << param2 << endl;
    params = text(node.children[1])[1: -1]
    format_str = params.split(',')[0][1: -1]    # "format_str"
    params = [x.replace(' ','') for x in params.split(',')[1:]] # params
    format_specifiers, indices = find_format_specifiers(format_str)
    if len(indices) != len(params): # 如果参数和%个数不一样
        return
    if len(indices) > 0:    # 有格式化字符串
        split_index = [(0, indices[0][0])]  # 用来切分%x前后的字符串
        for i in range(1, len(indices)):
            split_index.append((indices[i-1][1], indices[i][0]))
        split_index.append((indices[-1][1], len(format_str)))
    else:
        split_index = [(0, len(format_str))]
    cout_stream = ['cout']  # 输出流
    for i, each in enumerate(split_index):
        if each != (0, 0) and each[0] != len(format_str):
            if '?' in format_str[each[0]: each[1]]:   # 如果有三目运算符
                return
            cout_stream.append(f'"{format_str[each[0]: each[1]]}"')
        if i < len(params):
            if '?' in params[i]:   # 如果有三目运算符
                return
            cout_stream.append(params[i])
    cout_stream = [x for x in cout_stream if x not in ["''", '""']]
    # input(cout_stream)
    if cout_stream[-1][-3:] == '\\n"':    # 如果输出流最后一个是字符串并且输出了\n，则改为endl
        if cout_stream[-1][:-3] == '"':     # 如果删除完\n之后变成空字符串了
            del cout_stream[-1]
        else:
            cout_stream[-1] = cout_stream[-1][:-3] + '"'
        cout_stream.append('endl')
    # input(cout_stream)
    return [(node.end_byte, node.start_byte),
            (node.start_byte, ' << '.join(cout_stream))]

def cvt_Printf2Cout(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # printf("format_str", params); -> cout << str << param_1 << str << param2 << '\n';
    params = text(node.children[1])[1: -1]
    format_str = params.split(',')[0][1: -1]    # "format_str"
    params = [x.replace(' ','') for x in params.split(',')[1:]] # params
    format_specifiers, indices = find_format_specifiers(format_str)
    if len(indices) != len(params): # 如果参数和%个数不一样
        return
    if len(indices) > 0:    # 有格式化字符串
        split_index = [(0, indices[0][0])]  # 用来切分%x前后的字符串
        for i in range(1, len(indices)):
            split_index.append((indices[i-1][1], indices[i][0]))
        split_index.append((indices[-1][1], len(format_str)))
    else:
        split_index = [(0, len(format_str))]
    cout_stream = ['cout']  # 输出流
    for i, each in enumerate(split_index):
        if each != (0, 0) and each[0] != len(format_str):
            if '?' in format_str[each[0]: each[1]]:
                return
            cout_stream.append(f'"{format_str[each[0]: each[1]]}"')
        if i < len(params):
            if '?' in params[i]:
                return
            cout_stream.append(params[i])
    cout_stream = [x for x in cout_stream if x not in ["''", '""']]
    return [(node.end_byte, node.start_byte),
            (node.start_byte, ' << '.join(cout_stream))]

def cvt_DelEndl(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # cout << "str" << endl -> cout << "str\n" or cout << endl -> cout << '\n';
    cout_stream = []
    n = node.children[0]
    while n:
        cout_stream.insert(0, n.children[2])
        n = n.children[0]
        if text(n) == 'cout':
            break
    if text(cout_stream[-1]) == 'endl':
        if text(cout_stream[-1])[-1] == '"':
            # 如果最后一个输出的是字符串，则在字符串后面加上\n
            return [(cout_stream[-2].end_byte - 1, '\\n'),
                    (cout_stream[-1].end_byte, cout_stream[-2].end_byte)]
        else:
            # 否则将endl改为'\n'
            return [(cout_stream[-1].end_byte, cout_stream[-1].start_byte),
                    (cout_stream[-1].start_byte, "'\\n'")]

def cvt_Cout2Printf(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # 将cout转为printf
    info = get_stream_info(node, 'cout')
    if info:
        format_str, params_str = info
        printf_str = f'printf("{format_str}"{params_str});'
        return [(node.end_byte, node.start_byte),
                (node.start_byte, printf_str)]

def cvt_Scanf2Cin(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # scanf("%s", str) -> cin >> str;
    params = text(node.children[1])[1: -1]
    if '"' in params:
        num = params.count('"')
        index = params.find('"', num)
        params = params[index + 1:]
        index = params.find(',')
        params = params[index + 1:]
    params = [x.replace(' ','') for x in params.split(',')] # params
    cin_stream = ['cin']  # 输出流
    for param in params:
        cin_stream.append(param.replace('&',''))
    cin_stream = [x for x in cin_stream if x not in ['"']]
    return [(node.end_byte, node.start_byte),
            (node.start_byte, ' >> '.join(cin_stream))]

def cvt_Cin2Scanf(node: Node) -> List[Tuple[int, Union[int, str]]]:
    # cin >> str; -> scanf("%s", str)
    info = get_stream_info(node, 'cin')
    if info:
        format_str, params_str = info
        scanf_str = f'scanf("{format_str}"{params_str});'
        return [(node.end_byte, node.start_byte),
                (node.start_byte, scanf_str)]