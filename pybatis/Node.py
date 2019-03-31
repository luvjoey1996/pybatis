from typing import Iterable, List


class QueryStringTree:

    def __init__(self, **kwargs):
        self.child_node = []
        self.kwargs = kwargs


class TextNode:

    def __init__(self, string):
        self.string = string

    def __str__(self):
        return self.string

    def __repr__(self):
        return self.__str__()


class ItemNode:

    def __init__(self, val, string, val_type):
        self.val = val
        self.string = string
        self.val_type = val_type

    def generate(self, context):
        pass


class IfNode:

    def __init__(self, test):
        self.child_node = []
        self.parse_test(test)

    def parse_test(self, test):
        pass

    def generate(self, context):
        if self.compare():
            pass
        else:
            return ''

    def compare(self):
        pass


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
                 suffix_override: str = None):
        self.prefix = prefix
        self.suffix = suffix
        self.prefix_overrides = self.overrides_parser(prefix_overrides)
        self.suffix_overrides = self.overrides_parser(suffix_override)

    def overrides_parser(self, overrides) -> List[str]:
        if overrides is not None:
            return list(map(str.strip, overrides.split('|')))

    def generate(self, context: dict) -> str:
        pass


class WhereNode(TrimNode):

    def __init__(self):
        super(WhereNode, self).__init__(prefix='Where', prefix_overrides='AND|OR')
