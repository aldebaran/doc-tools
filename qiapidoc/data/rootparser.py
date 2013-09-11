import os
import sys

from xml.etree import ElementTree as etree

class RootParser:
    def __init__(self, xml_roots, objs=None):
        self._all_objs, self.objs, self._members = objs, dict(), dict()
        self._xml_roots, self._backtrace, self.refid = xml_roots, [], None

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
            pathes = self._filepathes(self.refid + '.xml')
        except (NameError, TypeError) as e:
            return
        for path in pathes:
            tree = etree.parse(path)
            self._backtrace.append("FILE " + self.refid)
            self.parse(tree.getroot())
            self._backtrace.pop()

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

    def _filepathes(self, *args):
        '''Find all matchs for file in doxygen output path.'''
        res = []
        for f in self._xml_roots:
            p = os.path.join(f, *args)
            if os.path.exists(p):
                res.append(p)
        return res
