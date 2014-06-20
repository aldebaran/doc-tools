from qiapidoc.data.hppfile import HPPFile
from qiapidoc.extendedclasses import CPPDocumentedObject

class CPPNamespace(HPPFile, CPPDocumentedObject):
    def __init__(self, root, objs):
        HPPFile.__init__(self, root, objs)
        CPPDocumentedObject.__init__(self)
        self.sorting_type = 'namespace'
        self.compoundname = ''

    def parse_attributes(self, element):
        self.refid = element.attrib['refid']

    def _parse_compoundname(self, element):
        self.compoundname = element.text

    def get_id(self):
        return self.name

    def __unicode__(self):
        return self.name

    def on_elem_instanciated(self, element):
        element.set_namespace(self.compoundname)
