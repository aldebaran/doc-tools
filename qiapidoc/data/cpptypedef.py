from qiapidoc.data.docparser import DocParser
from qiapidoc.extendedclasses import CPPDocumentedObject

class CPPTypedef(DocParser, CPPDocumentedObject):
    def __init__(self, root, objs):
        DocParser.__init__(self, root, objs)
        CPPDocumentedObject.__init__(self)
        self.name, rawname = '', ''
        self._type, self._args = '', ''
        self._ref = ''
        self._desc = ''

    def __cmp__(self, other):
        return cmp(self.get_name(), other.get_name())

    def parse_attributes(self, element):
        self.refid = element.attrib['id']

    def _parse_type(self, element):
        self._type = self._get_fulltext(element)
        self.parse(element)

    def _parse_ref(self, element):
        if 'refid' in element.attrib and self._type.strip() is element.text:
            self._ref = element.attrib['refid']

    def _parse_argsstring(self, element):
        if element.text is not None:
            self._args = element.text

    def _parse_name(self, element):
        self.name = element.text
        self.rawname = element.text

    def _parse_detaileddescription(self, element):
        self._desc = self._desc + '\n' + self._get_fulltext(element)

    def _parse_briefdescription(self, element):
        self._desc = self._desc + '\n' + self._get_fulltext(element)

    def get_name(self):
        return self.name

    def get_obj(self):
        return True

    def get_id(self):
        return ('TPD_' + self.name)

    def set_namespace(self, namespace):
        if namespace.endswith('::'):
            self.name = namespace + self.name
        else:
            self.name = namespace + '::' + self.name
