import qiapidoc.data.types

from qiapidoc.data.docparser import DocParser
from qiapidoc.extendedclasses import CPPDocumentedObject

class InnerClassOrNamespace:
    def __init__(self, name, refid):
        self.name, self.refid = name, refid

    def get_name(self):
        return self.name

    def __unicode__(self):
        return self.name

    def __cmp__(self, other):
        return cmp(self.get_name().lower(), other.get_name().lower())

class HPPFile(DocParser, CPPDocumentedObject):
    def __init__(self, root, objs):
        DocParser.__init__(self, root, objs)
        CPPDocumentedObject.__init__(self)
        self.name, self.innerclasses, self.innernamespaces = '', [], []
        self.macros, self.functions, self.enums, self.typedefs = [], [], [], []
        self.sorting_type = 'header'

    def parse_attributes(self, element):
        refid = element.attrib['refid']
        if refid.endswith('hpp'):
            self.refid = refid

    def _parse_compounddef(self, element):
        self.parse(element)

    def _parse_sectiondef(self, element):
        self.parse(element)

    def _parse_innerclass(self, element):
        self.innerclasses.append(
            InnerClassOrNamespace(element.text, element.attrib['refid']))

    def _parse_innernamespace(self, element):
        self.innernamespaces.append(
            InnerClassOrNamespace(element.text, element.attrib['refid']))

    def _parse_memberdef(self, element):
        obj = qiapidoc.data.types.parse_type(self._xml_roots, self.objs, element)
        if obj is None or not obj.get_obj():
            return
        if element.attrib['kind'] == 'define':
            self.macros.append(obj)
        elif element.attrib['kind'] == 'function':
            self.functions.append(obj)
        elif element.attrib['kind'] == 'enum':
            self.on_elem_instanciated(obj)
            self.enums.append(obj)
        elif element.attrib['kind'] == 'typedef':
            self.on_elem_instanciated(obj)
            self.typedefs.append(obj)
        self._set_objs(obj)

    def _parse_name(self, element):
        self.name = element.text

    def get_name(self):
        return self.name

    def get_obj(self):
        return True

    def on_elem_instanciated(self, element):
        return
