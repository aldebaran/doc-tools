import sys

from qiapidoc.data.docparser import DocParser
from qiapidoc.extendedclasses import DocMemberObjDefExpr
from qiapidoc.mycpp import NameDefExpr, DefinitionParser

class CPPVariable(DocMemberObjDefExpr, DocParser):
    def __init__(self, root, objs, is_member=False):
        DocParser.__init__(self, root, objs)
        DocMemberObjDefExpr.__init__(self)
        self._blacklist = ['visibility']

    def __cmp__(self, other):
        return cmp(self.get_name(), other.get_name())

    def parse_attributes(self, element):
        self.refid = element.attrib['id']
        self.visibility = element.attrib['prot']

    def _get_def_function(self):
        return DefinitionParser.parse_member_object

    def get_obj(self):
        try:
            return DocParser.get_obj(self)
        except Exception as e:
            print >> sys.stderr, 'Failed to parse variable, could be an enum',\
                                 'value or an actual error.'
            return False
