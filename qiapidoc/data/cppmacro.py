from qiapidoc.extendedclasses import CPPDocumentedObject
from qiapidoc.data.docparser import DocParser

class CPPMacro(DocParser, CPPDocumentedObject):
    def __init__(self, root, objs):
        DocParser.__init__(self, root, objs)
        CPPDocumentedObject.__init__(self)
        self.params = []

    def parse_attributes(self, element):
        self.refid = element.attrib['id']

    def _parse_name(self, element):
        self.name = element.text

    def _parse_param(self, element):
        self.parse(element)

    def _parse_defname(self, element):
        self.params.append(element.text)

    def __unicode__(self):
        params = u''
        if self.params:
            params = u'(' + u', '.join(self.params) + u')'
        return u'{name}{params}'.format(
            name = self.name,
            params = params,
        )

    def get_obj(self):
        return True

    def get_name(self):
        return self.name

    def get_id(self):
        return self.get_name()

    # FIXME: When generated, the detailed documentation of a macro doesn't get
    #        an anchor. I overload this function to avoid creating a link to
    #        nowhere, but it is not a solution. Must find why in sphinx code.
    def get_uri(self, builder, fromdocname):
        return None
