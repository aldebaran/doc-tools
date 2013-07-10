import os
import sys

from xml.etree import ElementTree as etree

class RootParser:
    def __init__(self, root, objs=None):
        self._all_objs, self.objs, self._members = objs, dict(), dict()
        self._root, self._backtrace, self.refid = root, [], None

    def __str__(self):
        try:
            res = '{}: {}'.format(self.refid, self.name)
        except NameError:
            res = '{}'.format(self.__class__)
        return res

    def parse(self, root):
        self._backtrace.append(root.tag)
        for child in root:
            method_name = '_parse_{tagname}'.format(tagname = child.tag)
            try:
                method = getattr(self.__class__, method_name)
            except (AttributeError, TypeError) as err:
                self._parse_unknown_element(child, err)
                continue
            method(self, child)
        for obj in self.objs.values():
            obj.subparse()
        self._backtrace.pop()

    def subparse(self):
        try:
            path = self._filepath(self.refid + '.xml')
        except (NameError, TypeError) as e:
            return
        if os.path.exists(path):
            tree = etree.parse(path)
            self.parse(tree.getroot())

    def parse_attributes(self, element):
        pass

    def doc_obj(self):
        return None

    def _parse_unknown_element(self, child, err):
        # Uncomment to debug: print >> sys.stderr, 'Unknown node', child.tag
        pass

    def _set_objs(self, obj):
        if obj.refid not in self.objs:
            self.objs[obj.refid] = obj
        if self._all_objs is not None:
            if obj.refid not in self._all_objs:
                self._all_objs[obj.refid] = obj
            else:
                print >> sys.stderr, 'REFID already known, check if complete...'

    def _filepath(self, *args):
        '''Returns a path from the root of doxygen XML output.'''
        return os.path.join(self._root, *args)
