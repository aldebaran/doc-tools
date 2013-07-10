from qiapidoc.mycpp import DefinitionParser
from qiapidoc.data.docparser import DocParser
from qiapidoc.extendedclasses import *

class CPPFunction(DocFuncDefExpr, DocParser):
    def __init__(self, root, objs):
        DocParser.__init__(self, root, objs)
        DocFuncDefExpr.__init__(self)
        self.cur_param, self.param_ways = None, dict()
        self._blacklist = ['static', 'virtual', 'pure_virutal', 'visibility']

    def __str__(self):
        return unicode(self)

    def __cmp__(self, other):
        def sub(obj):
            if obj.rv is None:
                return -1 if '~' in obj.get_name() else -2
            return 0
        self_type, other_type = sub(self), sub(other)
        if (not (self_type or other_type)) or (self_type == other_type):
            return cmp(self.get_name(), other.get_name())
        return (self_type - other_type)

    def parse_attributes(self, element):
        self.refid = element.attrib['id']
        self.visibility = element.attrib['prot']
        self.static = (element.attrib['static'].lower() == 'yes')
        self.virtual = (element.attrib['virt'].lower() != 'non-virtual')
        self.pure_virtual = element.attrib['virt'].startswith('pure')

    # Parameter documentation parsing.
    def _parse_parameterlist(self, element):
        self.parse(element)
        self._replace_text(element, text='')

    def _parse_parameteritem(self, element):
        self.parse(element)

    def _parse_parameternamelist(self, element):
        self.parse(element)

    def _parse_parametername(self, element):
        self.cur_param = self._get_fulltext(element)
        self.param_ways['param_' + self.cur_param] = element.attrib.get('direction', None)

    def _parse_parameterdescription(self, element):
        self.parse(element)
        try:
            for child in element:
                self.brief('param_' + self.cur_param).extend([
                    self._get_fulltext(child), ''
                ])
        except KeyError:
            pass

    # Return value documentation
    def _parse_simplesect(self, element):
        if element.attrib['kind']:
            self.parse(element)
            for child in element:
                self.brief(element.attrib['kind']).extend([
                    self._get_fulltext(child), ''
                ])
        self._replace_text(element, text='')

    # Definition parser.
    def _get_def_function(self):
        return DefinitionParser.parse_function
