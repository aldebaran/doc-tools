import os
import sys

import qiapidoc.data.rootparser
import qiapidoc.data.types

from xml.etree import ElementTree as etree

class IndexParser(qiapidoc.data.rootparser.RootParser):
    def parse_index(self):
        path = self._filepath('index.xml')
        if not os.path.exists(path):
            print >> sys.stderr, 'Index file not found:', path
            return
        tree = etree.parse(path)
        self.parse(tree.getroot())

    def _parse_compound(self, element):
        obj = qiapidoc.data.types.parse_type(self._root, self.objs, element)
        if obj is None:
            return
        self._set_objs(obj)
