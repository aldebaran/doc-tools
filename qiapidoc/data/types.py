import sys

import qiapidoc.data.cppclass
import qiapidoc.data.cppenum
import qiapidoc.data.cppfunction
import qiapidoc.data.cppmacro
import qiapidoc.data.cppnamespace
import qiapidoc.data.cppstruct
import qiapidoc.data.cpptypedef
import qiapidoc.data.cppvariable
import qiapidoc.data.hppfile

TYPES = {
    'class': qiapidoc.data.cppclass.CPPClass,
    'define': qiapidoc.data.cppmacro.CPPMacro,
    'enum': qiapidoc.data.cppenum.CPPEnum,
    'file': qiapidoc.data.hppfile.HPPFile,
    'function': qiapidoc.data.cppfunction.CPPFunction,
    'namespace': qiapidoc.data.cppnamespace.CPPNamespace,
    'struct': qiapidoc.data.cppstruct.CPPStruct,
    'typedef': qiapidoc.data.cpptypedef.CPPTypedef,
    'variable': qiapidoc.data.cppvariable.CPPVariable,
}

def get_class(kind):
    try:
        return qiapidoc.data.types.TYPES[kind]
    except KeyError:
# Uncomment this to debug:
#        print >> sys.stderr, 'Element kind `{}` is not yet implemented.'.format(
#            kind
#        )
        return None

def parse_type(root, objs, element):
    kind = element.attrib['kind']
    if kind in ['dir']:
#        print >> sys.stderr, 'Directory ignored.'
        return None
#    print >> sys.stderr, 'Found a compound element named', kind, '!'
    cls = qiapidoc.data.types.get_class(kind)
    if cls is None:
        return None
    obj = cls(root, objs)
    obj.parse_attributes(element)
    obj.parse(element)
    return obj
