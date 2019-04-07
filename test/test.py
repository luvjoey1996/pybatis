import unittest

from pybatis.Error import GetValueError
from pybatis.Node import ItemNode


class ItemNodeTest(unittest.TestCase):

    def test(self):
        self.assertRaises(GetValueError, ItemNode, '', 'str')
        node = ItemNode('name.first_name()', 'str')
        self.assertEqual(node.generate({'name': {'first_name': lambda: 'lue', 'last_name': 'smith'}}), 'lue')
        self.assertRaises(GetValueError, node.generate, {'name': ''})
