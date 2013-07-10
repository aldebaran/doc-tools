import re

from qiapidoc.data.docparser import DocParser
from qiapidoc.extendedclasses import CPPDocumentedObject

_VALUE_BEGIN = re.compile(r'^\s*=\s*')

class CPPEnumValue(DocParser, CPPDocumentedObject):
    def __init__(self, root, objs):
        DocParser.__init__(self, root, objs)
        CPPDocumentedObject.__init__(self)
        self.name, self.value = '', None

    def __cmp__(self, other):
        return cmp((self.value, self.name), (other.value, other.name))

    def _parse_initializer(self, element):
        self.value = _VALUE_BEGIN.sub('', element.text)
        try:
            self.value = eval(self.value, {'__builtins__': None}, {})
        except:
            pass

    def _parse_name(self, element):
        self.name = element.text


class CPPEnum(DocParser, CPPDocumentedObject):
    def __init__(self, root, objs):
        DocParser.__init__(self, root, objs)
        CPPDocumentedObject.__init__(self)
        self.name, self.values = '', list()

    def parse_attributes(self, element):
        self.refid = element.attrib['id']

    def _parse_name(self, element):
        self.name = element.text

    def _parse_enumvalue(self, element):
        obj = CPPEnumValue(self._root, self.objs)
        obj.parse(element)
        self.values.append(obj)

    def get_name(self):
        return self.name

    def get_obj(self):
        return True

    def get_id(self):
        return ('E_' + self.name)
