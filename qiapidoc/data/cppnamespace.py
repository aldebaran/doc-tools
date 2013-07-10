from qiapidoc.data.hppfile import HPPFile
from qiapidoc.extendedclasses import CPPDocumentedObject

class CPPNamespace(HPPFile, CPPDocumentedObject):
    def __init__(self, root, objs):
        HPPFile.__init__(self, root, objs)
        CPPDocumentedObject.__init__(self)
        self.sorting_type = 'namespace'

    def parse_attributes(self, element):
        self.refid = element.attrib['refid']

    def get_id(self):
        return self.name

    def __unicode__(self):
        return self.name
