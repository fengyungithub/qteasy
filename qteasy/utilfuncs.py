# coding=utf-8
# utilfuncs.py

# ======================================
# This file contains all functions that
# might be shared among different files
# in qteasy.
# ======================================

import numpy as np


TIME_FREQ_STRINGS = ['TICK',
                     'T',
                     'MIN',
                     'H',
                     'D', '5D', '10D', '20D',
                     'W',
                     'M',
                     'Q',
                     'Y']


def mask_to_signal(lst):
    """将持仓蒙板转化为交易信号.

        转换的规则为比较前后两个交易时间点的持仓比率，如果持仓比率提高，
        则产生相应的补仓买入信号；如果持仓比率降低，则产生相应的卖出信号将仓位降低到目标水平。
        生成的信号范围在(-1, 1)之间，负数代表卖出，正数代表买入，且具体的买卖信号signal意义如下：
        signal > 0时，表示用总资产的 signal * 100% 买入该资产， 如0.35表示用当期总资产的35%买入该投资产品，如果
            现金总额不足，则按比例调降买入比率，直到用尽现金。
        signal < 0时，表示卖出本期持有的该资产的 signal * 100% 份额，如-0.75表示当期应卖出持有该资产的75%份额。
        signal = 0时，表示不进行任何操作



    input:
        :param lst，ndarray，持仓蒙板
    return: =====
        op，ndarray，交易信号矩阵
    """

    # 比较本期交易时间点和上期之间的持仓比率差额，差额大于0者可以直接作为补仓买入信号，如上期为0.35，
    # 本期0.7，买入信号为0.35，即使用总资金的35%买入该股，加仓到70%
    op = (lst - np.roll(lst, shift=1, axis=0))
    # 差额小于0者需要计算差额与上期持仓数之比，作为卖出信号的强度，如上期为0.7，本期为0.35，差额为-0.35，则卖出信号强度
    # 为 (0.7 - 0.35) / 0.35 = 0.5即卖出50%的持仓数额，从70%仓位减仓到35%
    op = np.where(op < 0, (op / np.roll(lst, shift=1, axis=0)), op)
    # 补齐因为计算差额导致的第一行数据为NaN值的问题
    # print(f'creating operation signals, first signal is {lst[0]}')
    op[0] = lst[0]
    return op.clip(-1, 1)


def unify(arr):
    """调整输入矩阵每一行的元素，通过等比例缩小（或放大）后使得所有元素的和为1

    example:
    unify([[3.0, 2.0, 5.0], [2.0, 3.0, 5.0]])
    =
    [[0.3, 0.2, 0.5], [0.2, 0.3, 0.5]]

    :param arr: type: np.ndarray
    :return: ndarray
    """
    assert isinstance(arr, np.ndarray), f'InputError: Input should be ndarray! got {type(arr)}'
    s = arr.sum(1)
    shape = (s.shape[0], 1)
    return arr / s.reshape(shape)


def time_str_format(t: float, estimation: bool = False, short_form: bool = False):
    """ 将int或float形式的时间(秒数)转化为便于打印的字符串格式

    :param t:  输入时间，单位为秒
    :param estimation:
    :param short_form: 时间输出形式，默认为False，输出格式为"XX hour XX day XX min XXsec", 为True时输出"XXD XXH XX'XX".XXX"
    :return:
    """
    assert isinstance(t, float), f'TypeError: t should be a float number, got {type(t)}'
    assert t >= 0, f'ValueError, t should be greater than 0, got minus number'
    # debug
    # print(f'time input is {t}')
    str_element = []
    enough_accuracy = False
    if t >= 86400 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        days = t // 86400
        t = t - days * 86400
        str_element.append(str(int(days)))
        if short_form:
            str_element.append('D')
        else:
            str_element.append('days ')
    if t >= 3600 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        hours = t // 3600
        t = t - hours * 3600
        str_element.append(str(int(hours)))
        if short_form:
            str_element.append('H')
        else:
            str_element.append('hrs ')
    if t >= 60 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        minutes = t // 60
        t = t - minutes * 60
        str_element.append(str(int(minutes)))
        if short_form:
            str_element.append('\'')
        else:
            str_element.append('min ')
    if t >= 1 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        seconds = np.floor(t)
        t = t - seconds
        str_element.append(str(int(seconds)))
        if short_form:
            str_element.append('\"')
        else:
            str_element.append('s ')
    if not enough_accuracy:
        milliseconds = np.round(t * 1000, 1)
        if short_form:
            str_element.append(f'{int(np.round(milliseconds)):03d}')
        else:
            str_element.append(str(milliseconds))
            str_element.append('ms')

    return ''.join(str_element)


def list_or_slice(unknown_input: [slice, int, str, list], str_int_dict):
    """ 将输入的item转化为slice或数字列表的形式,用于生成HistoryPanel的数据切片：

    1，当输入item为slice时，直接返回slice
    2 输入数据为string, 根据string的分隔符类型确定选择的切片：
        2.1, 当字符串不包含分隔符时，直接输出对应的单片数据, 如'close'输出为[0]
        2.2, 当字符串以逗号分隔时，输出每个字段对应的切片，如'close,open', 输出[0, 2]
        2.3, 当字符串以冒号分割时，输出第一个字段起第二个字段止的切片，如'close:open',输出[0:2] -> [0,1,2]
    3 输入数据为列表时，检查列表元素的类型（不支持混合数据类型的列表如['close', 1, True]）：
        3.1 如果列表元素为string，输出每个字段名对应的列表编号，如['close','open'] 输出为 [0,2]
        3.2 如果列表元素为int时，输出对应的列表编号，如[0,1,3] 输出[0,1,3]
        3.3 如果列表元素为boolean时，输出True对应的切片编号，如[True, True, False, False] 输出为[0,1]
    4 输入数据为int型时，输出相应的切片，如输入0的输出为[0]

    :param unknown_input: slice or int/str or list of int/string
    :param str_int_dict: a dictionary that contains strings as keys and integer as values
    :return:
        a list of slice/list that can be used to slice the Historical Data Object
    """
    if isinstance(unknown_input, slice):
        return unknown_input  # slice object can be directly used
    elif isinstance(unknown_input, int):  # number should be converted to a list containing itself
        return np.array([unknown_input])
    elif isinstance(unknown_input, str):  # string should be converted to numbers
        string_input = unknown_input
        if string_input.find(',') > 0:
            string_list = str_to_list(input_string=string_input, sep_char=',')
            res = [str_int_dict[string] for string in string_list]
            return np.array(res)
        elif string_input.find(':') > 0:
            start_end_strings = str_to_list(input_string=string_input, sep_char=':')
            start = str_int_dict[start_end_strings[0]]
            end = str_int_dict[start_end_strings[1]]
            if start > end:
                start, end = end, start
            return np.arange(start, end + 1)
        else:
            # debug
            # print(str_int_dict)
            return [str_int_dict[string_input]]
    elif isinstance(unknown_input, list):
        is_list_of_str = isinstance(unknown_input[0], str)
        is_list_of_int = isinstance(unknown_input[0], int)
        is_list_of_bool = isinstance(unknown_input[0], bool)
        if is_list_of_bool:
            return np.array(list(str_int_dict.values()))[unknown_input]
        else:
            # convert all items into a number:
            if is_list_of_str:
                res = [str_int_dict[list_item] for list_item in unknown_input]
            elif is_list_of_int:
                res = [list_item for list_item in unknown_input]
            else:
                return None
            return np.array(res)
    else:
        return None


def labels_to_dict(input_labels: [list, str], target_list: [list, range]) -> dict:
    """ 给target_list中的元素打上标签，建立标签-元素序号映射以方便通过标签访问元素

    根据输入的参数生成一个字典序列，这个字典的键为input_labels中的内容，值为一个[0~N]的range，且N=target_list中的元素的数量
    这个函数生成的字典可以生成一个适合快速访问的label与target_list中的元素映射，使得可以快速地通过label访问列表中的元素
    例如，列表target_list 中含有三个元素，分别是[100, 130, 170]
    现在输入一个label清单，作为列表中三个元素的标签，分别为：['first', 'second', 'third']
    使用labels_to_dict函数生成一个字典ID如下：
    ID:  {'first' : 0
          'second': 1
          'third' : 2}
    通过这个字典，可以容易且快速地使用标签访问target_list中的元素：
    target_list[ID['first']] == target_list[0] == 100

    本函数对输入的input_labels进行合法性检查，确保input_labels中没有重复的标签，且标签的数量与target_list相同
    :param input_labels: 输入标签，可以接受两种形式的输入：
                                    字符串形式: 如:     'first,second,third'
                                    列表形式，如:      ['first', 'second', 'third']
    :param target_list: 需要进行映射的目标列表
    :return:
    """
    if isinstance(input_labels, str):
        input_labels = str_to_list(input_string=input_labels)
    unique_count = len(set(input_labels))
    assert len(input_labels) == unique_count, \
        f'InputError, label duplicated, count of target list is {len(target_list)},' \
        f' got {unique_count} unique labels only.'
    assert unique_count == len(target_list), \
        f'InputError, length of input labels does not equal to that of target list, expect ' \
        f'{len(target_list)}, got {unique_count} unique labels instead.'
    return dict(zip(input_labels, range(len(target_list))))


def str_to_list(input_string, sep_char: str = ','):
    """将逗号或其他分割字符分隔的字符串序列去除多余的空格后分割成字符串列表，分割字符可自定义"""
    assert isinstance(input_string, str), f'InputError, input is not a string!, got {type(input_string)}'
    res = input_string.replace(' ', '').split(sep_char)
    return res


# TODO: this function can be merged with str_to_list() in history.py
def input_to_list(pars: [str, int, list], dim: int, padder=None):
    """将输入的参数转化为List，同时确保输出的List对象中元素的数量至少为dim，不足dim的用padder补足

    input:
        :param pars，需要转化为list对象的输出对象
        :param dim，需要生成的目标list的元素数量
        :param padder，当元素数量不足的时候用来补充的元素
    return: =====
        pars, list 转化好的元素清单
    """
    if isinstance(pars, (str, int, np.int64)):  # 处理字符串类型的输入
        # print 'type of types', type(pars)
        pars = [pars] * dim
    else:
        pars = list(pars)  # 正常处理，输入转化为列表类型
    par_dim = len(pars)
    # 当给出的两个输入参数长度不一致时，用padder补齐type输入，或者忽略多余的部分
    if par_dim < dim:
        pars.extend([padder] * (dim - par_dim))
    return pars