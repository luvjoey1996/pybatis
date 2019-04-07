import functools
import operator
from collections import namedtuple
from typing import Iterable, List

from .Error import GetValueError, ParseTestStringError


class QueryStringTree:

    def __init__(self, **kwargs):
        self.child_node = []
        self.kwargs = kwargs


class TextNode:

    def __init__(self, string):
        self.string = string

    def generate(self, context):
        return self.string


def get_value_from_string(string: str):
    if string == 'None':
        return lambda: None
    elif "'" in string or '"' in string:
        return lambda: string[1:-1]
    elif string.isdecimal():
        if '.' in string:
            return lambda context: float(string)
        else:
            return lambda context: int(string)
    else:
        val_trace = [operator.itemgetter(i) if '()' not in i else lambda x: operator.itemgetter(i[:-2])(x)() for i in
                     string.split('.')]
        return functools.partial(get_value, val_trace=val_trace)


def get_value(context: dict = None, val_trace: list = None):
    if len(val_trace) == 0:
        raise
    for getter in val_trace:
        try:
            context = getter(context)
        except (TypeError, AttributeError) as e:
            raise GetValueError(f"can't get value from context {getter}")
    return context


class ItemNode:

    def __init__(self, val_string, val_type):
        if not val_string:
            raise GetValueError("Item Node val can't be empty string")
        self.get_value = get_value_from_string(val_string)
        self.val_type = val_type

    def generate(self, context):
        return self.get_value(context)


TestItem = namedtuple('TestItem', ('get_value1', 'get_value2', 'op'))

op_dict = {
    '>=': operator.ge,
    '<=': operator.le,
    '!=': operator.ne,
    '>': operator.gt,
    '<': operator.lt,
    '=': operator.eq
}


class IfNode:

    def __init__(self, test):
        self.child_node = []
        self.parse_test(test)
        self.operator = None
        self.test_units: List[TestItem] = []

    def parse_test(self, test: str):
        if 'or' in test:
            separator = 'or'
            self.operator = any
        else:
            separator = 'and'
            self.operator = all
        self.test_units = [self.parse_test_unit(test_unit_string.strip()) for test_unit_string in test.split(separator)]

    def parse_test_unit(self, test_unit_string: str) -> TestItem:
        eq_index: int = test_unit_string.find('=')
        gt_index: int = test_unit_string.find('>')
        lt_index: int = test_unit_string.find('<')
        # test string should't contains both > and <
        if gt_index != -1 and lt_index != -1:
            raise ParseTestStringError(f'test string contains both "<" and ">" comparator: "{test_unit_string}"')
        # when test string contains no =, it should contain either < or >
        if eq_index == -1:
            if gt_index != -1 and gt_index != 0:
                # when test string contains only >
                value1_string, value2_string = test_unit_string.split('>')
                return TestItem(
                    get_value1=get_value_from_string(value1_string.strip()),
                    get_value2=get_value_from_string(value2_string.strip()),
                    op=operator.gt
                )
            if lt_index != -1 and lt_index != 0:
                # when test string contains only <
                value1_string, value2_string = test_unit_string.split('<')
                return TestItem(
                    get_value1=get_value_from_string(value1_string.strip()),
                    get_value2=get_value_from_string(value2_string.strip()),
                    op=operator.lt
                )
            raise ParseTestStringError(f'no comparator in test string: "{test_unit_string}"')
        else:
            if gt_index != -1 and gt_index != 0:
                if gt_index + 1 != eq_index:
                    raise ParseTestStringError(f"""test string seems no comparator: "{test_unit_string}" """)
                else:
                    value1_string, value2_string = test_unit_string.split('>=')
                    return TestItem(
                        get_value1=get_value_from_string(value1_string.strip()),
                        get_value2=get_value_from_string(value2_string.strip()),
                        op=operator.gt
                    )
            if lt_index != -1 and lt_index != 0:
                if lt_index + 1 != eq_index:
                    raise ParseTestStringError(f"""test string seems no comparator: "{test_unit_string}" """)
                else:
                    value1_string, value2_string = test_unit_string.split("<=")
                    return TestItem(
                        get_value1=get_value_from_string(value1_string.strip()),
                        get_value2=get_value_from_string(value2_string.strip()),
                        op=operator.lt
                    )
            raise ParseTestStringError(f"""test string parse error: "{test_unit_string}" """)

    def generate(self, context):
        if self.compare():
            return ' '.join([child.generate(context) for child in self.child_node])
        else:
            return ''

    def compare(self):
        return self.operator(self.test_units)


class IfSet:

    def __init__(self):
        self.child_node: List[IfNode] = []

    def generate(self, context):
        for i in self.child_node:
            if i.compare():
                return i.generate(context)


class ForEachNode:

    def __init__(self, container: Iterable, item: str, index: str, _open: str, close: str, separator: str):
        self.container = container
        self.item = item
        self.index = index
        self.open = _open
        self.close = close
        self.separator = separator
        self.child_node = []

    def generate(self, context: dict) -> str:
        container = context[self.container]
        result = []
        for idx in range(len(container)):
            context[self.item] = container[idx]
            context[self.index] = idx
            temp_list = []
            for child in self.child_node:
                temp_list.append(child.generate(context))
            result.append(''.join(temp_list))
        del context[self.item]
        del context[self.index]
        return self.open + self.separator.join(result) + self.close


class TrimNode:

    def __init__(self, prefix: str = None, suffix: str = None, prefix_overrides: str = None,
                 suffix_overrides: str = None):
        self.prefix = prefix
        self.suffix = suffix
        self.prefix_overrides = self.overrides_parser(prefix_overrides)
        self.suffix_overrides = self.overrides_parser(suffix_overrides)

    def overrides_parser(self, overrides) -> List[str]:
        if overrides is not None:
            return list(map(str.strip, overrides.split('|')))

    def generate(self, context: dict) -> str:
        pass


class WhereNode(TrimNode):

    def __init__(self):
        super(WhereNode, self).__init__(prefix='Where', prefix_overrides='AND|OR')


class SetNode(TrimNode):
    def __init__(self):
        super(SetNode, self).__init__(prefix='SET', suffix_overrides=',')
