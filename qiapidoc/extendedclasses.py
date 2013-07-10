import string

from mycpp import *

_SELF_ELEMENT_NAME = 'self'
_SLUG_CHARS = string.ascii_lowercase + string.digits + '-'
_SLUG_SIZE = 50

class CPPDocumentedObject:
    def __init__(self):
        self.doc, self.docname, self._blacklist = dict(), None, []
        self.new_subdoc(_SELF_ELEMENT_NAME)

    def new_subdoc(self, element):
        if element not in self.doc:
            self.doc[element] = dict()
            self.doc[element]['brief'] = []
            self.doc[element]['details'] = []

    def brief(self, element=_SELF_ELEMENT_NAME):
        if element not in self.doc:
            self.new_subdoc(element)
        return self.doc[element]['brief']

    def details(self, element=_SELF_ELEMENT_NAME):
        if element not in self.doc:
            self.new_subdoc(element)
        return self.doc[element]['details']

    def get_id(self):
        raise NotImplementedError('must be implemented by other class.')

    def get_uri(self, builder, fromdocname):
        link = builder.get_relative_uri(fromdocname, self.docname)
        return '{}#{}'.format(link, self.get_id())

    def copy_obj(self, obj):
        members = [it for it in  dir(obj) if not it.startswith('_')]
        for member in members:
            attr = getattr(obj, member)
            if not hasattr(attr, '__call__') and member not in self._blacklist:
                setattr(self, member, attr)

    def is_documented(self):
        for doc in self.doc.values():
            if doc['brief'] or doc['details']:
                return True
        return False

    def is_detailed(self):
        for doc in self.doc.values():
            if doc['details']:
                return True
        return False

    def __cmp__(self, other):
        return cmp(self.get_name(), other.get_name())

    def rst_name(self):
        slug = unicode(self.get_name()).lower().replace(' ', '-')
        slug = ''.join(c for c in slug if c in _SLUG_CHARS)
        return slug[:_SLUG_SIZE] + u'.rst'

# TODO: Find out why this can't be pickled if generated with a factory.

class DocClassDefExpr(ClassDefExpr, CPPDocumentedObject):
    def __init__(self):
        ClassDefExpr.__init__(self, NameDefExpr(''), 'public', False, [])
        CPPDocumentedObject.__init__(self)

    def get_uri(self, builder, fromdocname):
        return builder.get_relative_uri(fromdocname, self.docname)


class DocMemberObjDefExpr(MemberObjDefExpr, CPPDocumentedObject):
    def __init__(self):
        MemberObjDefExpr.__init__(self, NameDefExpr(''), 'public', False, '', [], None)
        CPPDocumentedObject.__init__(self)


class DocFuncDefExpr(FuncDefExpr, CPPDocumentedObject):
    def __init__(self):
        FuncDefExpr.__init__(self, NameDefExpr(''), 'public', False, False,
                             False, NameDefExpr(''), [], False, False, False)
        CPPDocumentedObject.__init__(self)
