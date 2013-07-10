import qiapidoc.data.types

from qiapidoc.data.cppfunction import CPPFunction
from qiapidoc.data.cppvariable import CPPVariable
from qiapidoc.data.docparser import DocParser
from qiapidoc.extendedclasses import *
from qiapidoc.mycpp import DefinitionParser

class CPPClassInheritanceRelationship:
    def __init__(self, refid, name, visibility='public'):
        self.refid, self.name, self.visibility = refid, name, visibility

    def __cmp__(self, other):
        return cmp(self.name, other.name)

class CPPClass(DocClassDefExpr, DocParser):
    def __init__(self, root, objs):
        DocParser.__init__(self, root, objs)
        DocClassDefExpr.__init__(self)
        self.basecls, self.inhecls, self.include_name = dict(), dict(), ''
        self.sorting_type = 'class'

    def __cmp__(self, other):
        return cmp(self.get_name(), other.get_name())

    def parse_attributes(self, element):
        self.refid = element.attrib['refid']

    def get_obj(self):
        return True

    def _parse_name(self, element):
        self.name = NameDefExpr(element.text)

    def _parse_compounddef(self, element):
        self.parse(element)

    def _parse_sectiondef(self, element):
        #self.status = element.attrib['kind'][:-len('-func')]
        self.parse(element)

    def _parse_memberdef(self, element):
        obj = qiapidoc.data.types.parse_type(self._root, self.objs, element)
        if obj is None:
            return
        self._set_objs(obj)

    # Inheritance parsing
    def _parse_basecompoundref(self, element):
        self.basecls[element.text] = CPPClassInheritanceRelationship(
            element.attrib.get('refid'), element.text, element.attrib['prot'],
        )

    def _parse_derivedcompoundref(self, element):
        self.inhecls[element.text] = CPPClassInheritanceRelationship(
            element.attrib.get('refid'), element.text, element.attrib['prot'],
        )

    def _parse_includename(self, element):
        self.include_name = element.text
        self._replace_text(element, text='')
        self._contains_includename = True

    def _parse_inheritancegraph(self, element):
        self.parse(element)

    def _parse_node(self, element):
        self.parse(element)

    def _parse_label(self, element):
        label = element.text.split('::')[-1]
        if label in self.basecls:
            self.basecls[label].name = element.text
        if label in self.inhecls:
            self.basecls[label].name = element.text

    # Used to render complete documentation
    def _is_public(self, obj, public):
        return (obj.visibility == 'public' if public else
                obj.visibility != 'public')

    def filter_by_id(self, id):
        FUNC_MAP = {
            'types': CPPClass.group_types,
            'functions': CPPClass.group_functions,
            'static-functions': CPPClass.group_static_functions,
            'members': CPPClass.group_members,
            'all-functions': CPPClass.group_all_functions,
        }
        res = []
        if id.startswith('public-'):
            id_map = id[7:]
        elif id.startswith('private-'):
            id_map = id[8:]
        else:
            id_map = id
        if id_map in FUNC_MAP:
            FUNC_MAP[id_map](self, res, public=(not id.startswith('private-')))
        return res

    def _group_filter(self, res, filter_func):
        for obj in self.objs.values():
            if filter_func(obj):
                res.append(obj)

    def group_types(self, res, public=True):
        pass

    def group_functions(self, res, public=True, static=False):
        def filter_func(obj):
            return (isinstance(obj, CPPFunction) and obj.static == static and
                    self._is_public(obj, public))
        tmp = []
        self._group_filter(tmp, filter_func)
        res.extend(sorted(tmp))

    def group_static_functions(self, res, public=True):
        return self.group_functions(res, static=True, public=public)

    def group_all_functions(self, res, public=True):
        tmp = []
        self.group_static_functions(tmp)
        self.group_functions(tmp)
        res.extend(sorted(tmp))

    def group_members(self, res, public=True):
        def filter_func(obj):
            return (isinstance(obj, CPPVariable) and
                    self._is_public(obj, public))
        tmp = []
        self._group_filter(tmp, filter_func)
        res.extend(sorted(tmp))
