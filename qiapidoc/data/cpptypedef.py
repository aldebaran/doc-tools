from qiapidoc.data.docparser import DocParser
from qiapidoc.extendedclasses import CPPDocumentedObject

class CPPTypedef(DocParser, CPPDocumentedObject):
    def __init__(self, root, objs):
        DocParser.__init__(self, root, objs)
        CPPDocumentedObject.__init__(self)
        self.name = ''

    def parse_attributes(self, element):
        self.refid = element.attrib['id']

    def _parse_name(self, element):
        self.name = element.text

    def get_name(self):
        return self.name

    def get_obj(self):
        return True
