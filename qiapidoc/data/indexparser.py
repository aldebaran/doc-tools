import os
import sys

import qiapidoc.data.rootparser
import qiapidoc.data.types

from xml.etree import ElementTree as etree

class IndexParser(qiapidoc.data.rootparser.RootParser):
    def parse_index(self):
        final_objs = dict()
        for p in self._xml_roots:
            f = os.path.join(p, 'index.xml')
            if os.path.exists(f):
                tree = etree.parse(f)
                self.parse(tree.getroot())
                final_objs = dict(final_objs.items() + self.objs.items())
                self.objs = dict()
        self.objs = final_objs

    def _parse_compound(self, element):
        obj = qiapidoc.data.types.parse_type(self._xml_roots, self.objs, element)
        if obj is None:
            return
        self._set_objs(obj)
