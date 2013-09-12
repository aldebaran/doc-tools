import os
import re

from docutils import nodes
from docutils.statemachine import StringList
from mycpp import *
from sphinx import addnodes
from sphinx.application import ExtensionError
from sphinx.directives import ObjectDescription
from sphinx.domains import Index
from sphinx.util.compat import Directive

import data.indexparser


'''
qiapidoc
========

This modules comes from a simple need: produce a simple, clear and complete
documentation of our C++ api. Multiple possibilities have been studied, and we
came to the conclusion that a bridge from doxygen to sphinx was the best we
could do.

It lets doxygen the task to parse C++, and sphinx will be our base to generate
HTML documentation.

There are at least two bridges already existing: breathe and Robin, but they
aren't exactly what we need and we expect and their codebase is huge, so we are
going to try from scratch something more simple.
'''


class CPPAutoDocObject:
    has_content = True
    option_spec = {
        'brief': lambda x: x,
        'title': lambda x: x,
    }

    def __init__(self):
        self._obj = None

    def _get_domain(self):
        return self.state.document.settings.env.domains['cpp']

    def _get_obj(self, name_provided=None):
        if self._obj is not None and not name_provided:
            return self._obj
        name = name_provided
        if name_provided is None:
            name = self.arguments[0]
        res = self._get_domain().data['doxygen_objs'].get(name, None)
        if not name_provided:
            self._obj = res
        return res

    def _get_name(self):
        obj = self._get_obj()
        if obj is not None:
            return obj.get_name()
        return self.arguments[0]

    def _populate(self):
        obj = self._get_obj()
        if obj is None:
            return False
        obj.docname = self.state.document.settings.env.docname
        self.arguments[0] = unicode(obj)
        if not self.content:
            self.content = StringList(initlist=obj.details() or obj.brief())
        return True

    def _make_section(self, title_text):
        section = nodes.section()
        section += nodes.title(text=title_text)
        section.attributes['ids'].append(nodes.make_id(title_text))
        return section

    def _make_main_section(self, title):
        return self._make_section(self.options.get('title', title))

    def _make_brief(self, obj):
        para = nodes.paragraph()
        para += nodes.Text(self.options.get('brief', ' '.join(obj.brief())))
        para += nodes.Text(' ')
        ref = nodes.reference()
        ref['refuri'] = '#detailed-description'
        ref += nodes.literal(text='More...')
        para += ref
        return para

    def _make_details(self, obj):
        contentnode = nodes.paragraph()
        self.state.nested_parse(self.content, self.content_offset, contentnode,
                                match_titles=1)
        return contentnode

    def _make_enum_documentation(self, obj):
        def get_entry(node):
            para = addnodes.compact_paragraph()
            para += node
            entry = nodes.entry()
            entry += para
            return entry
        desc = addnodes.desc_signature()
        desc['ids'].append(obj.get_id())
        first = False
        desc += nodes.emphasis(text=u'enum')
        desc += nodes.Text(u' ')
        desc += addnodes.desc_name(text=obj.get_name())
        desc.attributes['first'] = True
        content = addnodes.desc_content()
        if obj.brief():
            para = nodes.paragraph()
            para += nodes.emphasis(text='Brief: ')
            para += nodes.Text(' '.join(obj.brief()))
            content += para
        table, body = nodes.table(), nodes.tbody()
        tgroup = nodes.tgroup(cols=3)
        thead = nodes.thead()
        for it in [20, 10, 70]:
            tgroup += nodes.colspec(colwidth=it)
        tgroup += thead
        tgroup += body
        table += tgroup
        head_row = nodes.row()
        for it in ['Name', 'Value', 'Brief']:
            head_row += get_entry(nodes.Text(it))
        thead += head_row
        for val in sorted(obj.values):
            row = nodes.row()
            row += get_entry(nodes.literal(text=val.name))
            tmp = [val.value if val.value is not None else '',
            ' '.join(val.brief())]
            for it in tmp:
                row += get_entry(nodes.Text(it))
            body += row
        content += table
        return (desc, content)

class CPPAutoEnumObject(CPPAutoDocObject, CPPObject):
    def __init__(self, *args, **kwargs):
        print("Autoenum: " + ','.join(map(lambda x: str(x), args)))
        CPPAutoDocObject.__init__(self)
        CPPObject.__init__(self, *args, **kwargs)
        print("args: " + ','.join(map(lambda x: str(x), self.arguments)))

    def run(self):
        populated = CPPAutoDocObject._populate(self)
        if populated:
          (desc, content) = CPPAutoDocObject._make_enum_documentation(self, self._obj)
          lst = addnodes.desc()
          lst += desc
          lst += content
          lst['objtype'] = 'type'
          return [lst]

class CPPAutoMemberObject(CPPAutoDocObject, CPPMemberObject):
    def __init__(self, *args, **kwargs):
        CPPAutoDocObject.__init__(self)
        CPPMemberObject.__init__(self, *args, **kwargs)

    def run(self):
        CPPAutoDocObject._populate(self)
        self.name = 'member'
        return CPPMemberObject.run(self)


class CPPAutoMacroObject(CPPAutoDocObject, CPPObject):
    def __init__(self, *args, **kwargs):
        CPPAutoDocObject.__init__(self)
        CPPObject.__init__(self, *args, **kwargs)

    def get_index_text(self, name):
        if self.objtype == 'macro':
            return _('%s (C++ Macro)') % name
        return ''

    def parse_definition(self, parser):
        pass

    def describe_signature(self, signode, obj):
        self.attach_name(signode, obj.name)

    def run(self):
        CPPAutoDocObject._populate(self)
        return CPPObject.run(self)


class CPPAutoFunctionObject(CPPAutoDocObject, CPPFunctionObject):
    def __init__(self, *args, **kwargs):
        CPPAutoDocObject.__init__(self)
        CPPFunctionObject.__init__(self, *args, **kwargs)

    def run(self):
        populated = CPPAutoDocObject._populate(self)
        self.name = 'function'
        res, obj = CPPFunctionObject.run(self), self._get_obj()
        if populated:
            fieldlist, _empty = nodes.field_list(), True
            doc_args = [it for it in obj.signature
                        if obj.brief('param_' + str(it.get_name()))]
            if doc_args:
                tmp = []
                for it in doc_args:
                    param_name = 'param_' + str(it.get_name())
                    node = addnodes.compact_paragraph()
                    if obj.param_ways.get(param_name, None) is not None:
                        node += nodes.literal(text='[{}] '.format(
                            obj.param_ways[param_name]
                        ))
                    node += nodes.Text(obj.brief(param_name)[0])
                    tmp.append((it.name, node))
                fieldlist += self.doc_field_types[0].make_field(
                    [], # [it.type for it in doc_args],
                    self._get_domain(),
                    tmp,
                )
                _empty = False
            def _simple_field(fieldlist, name, nb_):
                if obj.brief(name):
                    fieldlist += self.doc_field_types[nb_].make_field(
                        None, self._get_domain(),
                        (None, [nodes.Text(it) for it in obj.brief(name)])
                    )
                    return False
                return True
            _empty =_simple_field(fieldlist, 'return', 1) and _empty
            _empty = _simple_field(fieldlist, 'pre', 3) and _empty
            _empty = _simple_field(fieldlist, 'post', 4) and _empty
            if not _empty:
                res[1][1].insert(0, fieldlist)
            if obj.details() and not _empty:
                para = nodes.paragraph()
                para += nodes.emphasis(text='Brief: ')
                para += nodes.Text(''.join(obj.brief()))
                res[1][1].insert(0, para)
        return res


class CPPAutoClassObject(CPPAutoDocObject, CPPClassObject):
    def __init__(self, *args, **kwargs):
        CPPAutoDocObject.__init__(self)
        CPPClassObject.__init__(self, *args, **kwargs)
        self._section_title = '{name} Class Reference'

    def _make_include(self, obj):
        tmp=u'#include <{name}>'.format(name = obj.include_name)
        hl = nodes.literal_block(tmp, tmp)
        hl['language'] = 'cpp'
        return hl

    def _make_inheritance(self, obj):
        def sub(title, lst):
            if not lst:
                return None
            item, res, tmp = nodes.list_item(), addnodes.compact_paragraph(), []
            res += nodes.strong(text=(title + ': '))
            kwargs = {
                'refdomain': 'cpp',
                'refexplicit': False,
                'reftype': 'class',
            }
            for it in lst:
                kwargs['reftarget'] = unicode(it.name)
                node = addnodes.pending_xref('', **kwargs)
                node += nodes.literal(text=it.name)
                tmp.extend([node, nodes.Text(', ')])
            res.extend(tmp[:-1])
            item += res
            return item
        para = nodes.bullet_list()
        para += sub('Inherits', obj.basecls.values())
        para += sub('Inherited by', obj.inhecls.values())
        return para

    def _make_index_section(self, obj, title, id):
        section = self._make_section(title)
        subobjs = obj.filter_by_id(id)
        kwargs = {
            'refdomain': 'cpp',
            'refexplicit': False,
        }
        if subobjs:
            lst = addnodes.desc()
            lst['objtype'] = 'function function-index'
            for obj in subobjs:
                desc = addnodes.desc_signature()
                span = nodes.inline()
                try:
                    kwargs['reftype'] = 'func'
                    if obj.rv is not None:
                        span += addnodes.desc_type(text=str(obj.rv))
                except AttributeError:
                    kwargs['reftype'] = 'member'
                    span += addnodes.desc_type(text=str(obj.typename))
                desc += span
                desc += nodes.Text(u' ')
                name = unicode(obj.name)
                kwargs['reftarget'] = unicode(obj.get_name())
                name = name.split('::')[-1]
                desc_name = addnodes.desc_name()
                refnode = addnodes.pending_xref('', **kwargs)
                innernode = nodes.literal(text=name)
                innernode.attributes['classes'].extend(['xref', 'cpp', 'cpp-func'])
                refnode += innernode
                desc_name += refnode
                desc += desc_name
                try:
                    paramlist = addnodes.desc_parameterlist()
                    for param_obj in obj.signature:
                        param = addnodes.desc_parameter('', '', noemph=True)
                        if param_obj.type is not None:
                            param += nodes.Text(str(param_obj.type) + ' ')
                        param += nodes.emphasis(text=str(param_obj.name))
                        paramlist += param
                    desc += paramlist
                    if obj.const:
                        desc += nodes.Text(u' const')
                except AttributeError:
                    pass
                lst += desc
            section += lst
            return section
        return None

    def _make_methods_documentation(self, obj):
        section = self._make_section('Function Documentation')
        subobjs = [it for it in obj.filter_by_id('all-functions')
                   if it.is_documented()]
        if subobjs:
            for obj_ in sorted(subobjs):
                name = obj_.get_name()
                tmp = CPPAutoFunctionObject(
                    'cpp:function', [name], dict(), StringList([], items=[]),
                    0, 0, u'.. cpp:autofunction:: {}'.format(name), self.state,
                    self.state_machine)
                section += tmp.run()
                pass
            return section
        return None

    def _make_members_documentation(self, obj):
        section = self._make_section('Members Documentation')
        subobjs = [it for it in obj.filter_by_id('public-members')
                   if it.is_documented()]
        if subobjs:
            for obj_ in sorted(subobjs):
                name = unicode(obj_.get_name())
                tmp = u'.. cpp:automember:: {}'.format(name)
                tmp = CPPAutoMemberObject(
                    'cpp:member', [name], dict(), StringList([], items=[]), 0,
                    0, tmp, self.state, self.state_machine)
                section += tmp.run()
            return section
        else:
            return None

    def run(self):
        populated = CPPAutoDocObject._populate(self)
        indexnode = addnodes.index(entries=[])
        title = self._section_title.format(name = self._get_name())
        main_section = self._make_main_section(title)
        if populated:
            obj = CPPAutoDocObject._get_obj(self)
            section = self._make_section('Introduction')
            section += self._make_brief(obj)
            section += self._make_include(obj)
            section += self._make_inheritance(obj)
            main_section += section
            sects = {
                'types': 'Types',
                'functions': 'Functions',
                'static-functions': 'Static Functions',
                'members': 'Members',
            }
            sects_order = ['types', 'members', 'functions', 'static-functions']
            for status in ['public']: #, 'private']:
                for id in sects_order:
                    title = '{} {}'.format(status.title(), sects[id])
                    id = '{}-{}'.format(status, id)
                    main_section += self._make_index_section(obj, title, id)
            section = self._make_section('Detailed Description')
            section += self._make_details(obj)
            main_section += section
            main_section += self._make_methods_documentation(obj)
            main_section += self._make_members_documentation(obj)
            return [indexnode, main_section]
        else:
            main_section += nodes.paragraph(text='Unknow Class.')
        return [indexnode, main_section]


class CPPAutoStructObject(CPPAutoClassObject):
    def __init__(self, *args, **kwargs):
        CPPAutoClassObject.__init__(self, *args, **kwargs)
        self._section_title = '{name} Struct Reference'


class CPPAutoHeaderObject(CPPAutoDocObject, ObjectDescription):
    def __init__(self, *args, **kwargs):
        CPPAutoDocObject.__init__(self)
        ObjectDescription.__init__(self, *args, **kwargs)

    def __make_list(self, obj, _lst, _type):
        def get_entry(node):
            para = addnodes.compact_paragraph()
            para += node
            entry = nodes.entry()
            entry += para
            return entry
        table, body, tgroup = nodes.table(), nodes.tbody(), nodes.tgroup(cols=2)
        thead = nodes.thead()
        tgroup += nodes.colspec(colwidth=20)
        tgroup += nodes.colspec(colwidth=80)
        tgroup += thead
        tgroup += body
        table += tgroup
        head_row = nodes.row()
        head_row += get_entry(nodes.Text('Name'))
        head_row += get_entry(nodes.Text('Brief'))
        thead += head_row
        kwargs = {
            'refdomain': 'cpp',
            'refexplicit': False,
            'reftype': _type,
        }
        for it in sorted(_lst):
            row = nodes.row()
            subobj = self._get_obj(unicode(it.get_name()))
            if subobj is not None:
                kwargs['reftarget'] = unicode(it.get_name())
                ref = addnodes.pending_xref('', **kwargs)
                ref += nodes.literal(text=unicode(subobj.name))
            else:
                kwargs['reftarget'] = unicode(it.name)
                ref = addnodes.pending_xref('', **kwargs)
                ref += nodes.literal(text=unicode(it.name))
            row += get_entry(ref)
            texts = None
            if subobj is not None and subobj.brief():
                texts = nodes.Text(' '.join(subobj.brief()))
            row += get_entry(texts)
            body += row
        return table

    def _make_innerclasses(self, obj):
        section = None
        if obj.innerclasses:
            section = self._make_section('Classes')
            section += self.__make_list(obj, obj.innerclasses, 'class')
        return section

    def _make_innerenums(self, obj):
        section = None
        if obj.enums:
            section = self._make_section('Enumerations')
            section += self.__make_list(obj, obj.enums, 'type')
        return section

    def _make_innerfunctions(self, obj):
        # FIXME: Functions don't seem to be in XML. This means this will never
        # be called. Header information in doesn't really look int.
        # PS: This is used by namespace documenter just below.
        section = None
        if obj.functions:
            section = self._make_section('Functions')
            section += self.__make_list(obj, obj.functions, 'func')
        return section

    def _make_innermacros(self, obj):
        section = None
        macros = [it for it in obj.macros if not it.name.startswith('_')]
        if macros:
            section = self._make_section('Macros')
            section += self.__make_list(obj, macros, 'macros')
        return section

    def _make_innernamespaces(self, obj):
        section = None
        if obj.innernamespaces:
            section = self._make_section('Namespaces')
            section += self.__make_list(obj, obj.innernamespaces, 'namespace')
        return section

    def _make_innertypes(self, obj):
        section = None
        if obj.typedefs:
            section = self._make_section('Types')
            section += self.__make_list(obj, obj.typedefs, 'type')
        return section

    def _make_macro_documentation(self, obj):
        lst = [it for it in obj.macros
               if it.is_detailed() and not it.name.startswith('_')]
        if lst:
            section = self._make_section('Macros')
            for obj in sorted(lst):
                tmp = u'.. cpp:automacro:: {}'.format(obj.get_name())
                tmp = CPPAutoMacroObject('cpp:macro', [obj.get_name()],
                                         dict(), StringList([], items=[]), 0,
                                         0, tmp, self.state,
                                         self.state_machine)
                section += tmp.run()
            return section
        else:
            return None

    def run(self):
        populated = CPPAutoDocObject._populate(self)
        indexnode = addnodes.index(entries=[])
        title = '{name} Header Reference'.format(name = self._get_name())
        main_section = self._make_main_section(title)
        if populated:
            obj = self._get_obj()
            section = self._make_section('Introduction')
            section += self._make_brief(obj)
            main_section += section
            section = self._make_section('Inner Definitions')
            main_section += section
            section += self._make_innernamespaces(obj)
            section += self._make_innerclasses(obj)
            section += self._make_innerfunctions(obj)
            section += self._make_innermacros(obj)
            section = self._make_section('Detailed Description')
            section += self._make_details(obj)
            main_section += section
            main_section += self._make_macro_documentation(obj)
        else:
            main_section += nodes.paragraph(text='Unknown Header.')
        return [indexnode, main_section]


class CPPAutoNamespaceObject(CPPAutoHeaderObject):
    def _make_methods_documentation(self, obj):
        section = self._make_section('Functions')
        if obj.functions:
            for obj_ in sorted(obj.functions):
                if not obj_.is_documented():
                    continue
                name = unicode(obj_.get_name())
                tmp = CPPAutoFunctionObject(
                    'cpp:function', [name], dict(), StringList([], items=[]),
                    0, 0, u'.. cpp:autofunction:: {}'.format(name), self.state,
                    self.state_machine)
                section += tmp.run()
                pass
            return section
        return None

    def _make_enums_documentation(self, obj):
        first = True
        if obj.enums:
            section = self._make_section('Enumerations')
            lst = addnodes.desc()
            section += lst
            lst['objtype'] = 'type'
            for obj_ in obj.enums:
                obj_.docname = obj.docname
                (desc, content) = _make_enum_documentation(self, obj_)
                desc.attributes['first'] = first
                lst += desc
                lst += content
            return section
        return None

    def run(self):
        populated = CPPAutoDocObject._populate(self)
        indexnode = addnodes.index(entries=[])
        title = '{name} Namespace Reference'.format(name = self._get_name())
        main_section = self._make_main_section(title)
        if populated:
            obj = self._get_obj()
            section = self._make_section('Introduction')
            section += self._make_brief(obj)
            main_section += section
            section = self._make_section('Inner Definitions')
            main_section += section
            section += self._make_innernamespaces(obj)
            section += self._make_innermacros(obj)
            section += self._make_innertypes(obj)
            section += self._make_innerclasses(obj)
            section += self._make_innerfunctions(obj)
            section = self._make_section('Detailed Description')
            section += self._make_details(obj)
            main_section += section
            main_section += self._make_methods_documentation(obj)
            main_section += self._make_enums_documentation(obj)
        else:
            main_section += nodes.paragraph(text='Unknown Namespace.')
        return [indexnode, main_section]


def split_func_name(name, discard_args = False):
    pif = name.split("(", 1)
    if len(pif) == 2:
        name = pif[0]
        param = "(" + pif[1]
    else:
        param = ""

    if discard_args:
        param = ""

    fnames = name.rsplit("::", 1)
    if len(fnames) == 2:
        fpath = fnames[0]
        fname = fnames[1] + param
    else:
        fpath = ""
        fname = name + param
    return (fpath, fname)


class CppIndex(Index):
    def generate(self, docnames=None):
        def split_name(refname):
            fnames = split_func_name(refname, discard_args=True)
            if len(fnames) == 2:
                fname = fnames[1]
                fpath = fnames[0]
            else:
                fname = refname
                fpath = "global"
            return fname, fpath
        content = {}

        functable = dict()
        for refname, (docname, type, theid) in self.domain.data['objects'].iteritems():
            if type == self._type:
                fname, fpath = split_name(refname)
                e = functable.setdefault(fname, [])
                e.append([refname, (docname, type, theid)])

        for name, obj in self.domain.data.get('doxygen_objs', {}).iteritems():
            if obj.sorting_type == self._type:
                fname, fpath = split_name(unicode(obj))
                e = functable.setdefault(fname, [])
                e.append([obj.name, (obj.docname, self._type, obj.get_id())])

        for fun, funlist in functable.iteritems():
            st = fun[0]
            if fun.startswith("AL"):
                st = fun[2]

            entries = content.setdefault(st.upper(), [])
            if len(funlist) == 1:
                refname, (docname, type, theid) = funlist[0]
                if docnames and (not docname in docnames):
                    continue
                entries.append([fun, 0, docname, theid, '', '', refname])
                continue
            entries.append([fun, 1, '', '', '', '', ''])
            for (refname, (docname, type, theid)) in funlist:
                if docnames and (not docname in docnames):
                    continue
                entries.append([fun, 2, docname, theid, '', '', refname])

        # sort by first letter
        result   = sorted(content.iteritems())
        collapse = False

        return result, collapse


class CppClassIndex(CppIndex):
    name = 'classindex'
    localname = l_('C++ Class Index')
    shortname = l_('classes')
    _type = 'class'


class CppFunctionIndex(CppIndex):
    name = 'funcindex'
    localname = l_('C++ Function Index')
    shortname = l_('functions')
    _type = 'function'


class CPPAPIDocDomain(MyCPPDomain):
    def __init__(self, env):
        CPPDomain.__init__(self, env)
        self._doxygen_parsed, self._skel_generated = False, False

    def parse_doxygen(self):
        if self._doxygen_parsed:
            return
        self._doxygen_parsed = True
        self.data['doxygen_objs'] = dict()
        xml_src = self.env.app.config.qiapidoc_srcs
        if xml_src is not None:
            parser = data.indexparser.IndexParser(xml_src)
            parser.parse_index()
            for obj in parser.objs.values():
                if obj.get_obj():
                    self.data['doxygen_objs'][unicode(obj.get_name())] = obj

    def gen_skeleton(self):
        if self._skel_generated:
            return
        self._skel_generated = True
        root = self.env.app.config.qiapidoc_gen_skeleton
        if not root:
            print 'WARNING: No root set for qiapidoc, not generating skeleton.'
            return
        root_index = root
        while not root_index.endswith(os.sep + 'source'):
            root_index, filename = os.path.split(root_index)
            if filename == '':
                self.env.warn('Can\'t find root of sources of the doc.')
                return
        dirs = {
            'class': 'classes',
            'header': 'headers',
            'namespace': 'namespaces',
            'struct': 'structures',
        }
        def _mkdir(*args):
            path = os.path.join(root, *args)
            if not os.path.exists(path):
                os.mkdir(path)
        def _gen_index(sorting_type):
            path = os.path.join(root, dirs[sorting_type], 'index.rst')
            if os.path.exists(path):
                return
            with open(path, 'w') as f:
                f.write('''{}
{}

.. toctree::
    :glob:
    :maxdepth: 1

    *
'''.format(dirs[sorting_type].title(), '-' * len(dirs[sorting_type])))
        _mkdir()
        sdirs = dict((a, False) for a in dirs.iterkeys())
        for obj in self.data['doxygen_objs'].values():
            if not obj.is_documented():
                print 'WARNING: Object', str(obj), 'is not documented, ignored.'
                continue
            if obj.sorting_type not in dirs:
                continue
            sdirs[obj.sorting_type] = True
            _mkdir(dirs[obj.sorting_type])
            _gen_index(obj.sorting_type)
            path = os.path.join(root, dirs[obj.sorting_type], obj.rst_name())
            if os.path.exists(path):
                continue
            with open(path, 'w') as f:
                content = '.. cpp:auto{}:: {}\n'.format(
                    obj.sorting_type, obj.get_name())
                f.write(content)
        with open(os.path.join(root, 'index.rst'), 'w') as f:
            f.write('''API
---

.. /!\ WARNING /!\ THIS FILE WILL BE OVERRIDDEN BY QIAPIDOC EVERYTIME THE
                   SKELETON IS GENERATED. ALL THE MODIFICATIONS TO THIS FILE
                   WILL BE LOST.

.. toctree::
    :maxdepth: 2

''')
            for key, value in sorted(sdirs.iteritems()):
                if value:
                    f.write('    {}/index\n'.format(dirs[key]))
            f.write('''

- :doc:`/cpp-classindex`
- :doc:`/cpp-funcindex`
''')

        with open(os.path.join(root_index, 'cpp-funcindex.rst'), 'w') as f:
            f.write('''.. _cpp-funcindex:

C++ Function Index
==================

will be overrided
''')
        with open(os.path.join(root_index, 'cpp-classindex.rst'), 'w') as f:
            f.write('''.. _cpp-classindex:

C++ Class Index
===============

will be overrided
''')

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        res = MyCPPDomain.resolve_xref(self, env, fromdocname, builder, typ,
                                       target, node, contnode)
        if res is not None:
            return res
        if target not in self.data['doxygen_objs']:
            return None
        obj = self.data['doxygen_objs'][target]
        if obj.docname is None:
            return None
        refuri = obj.get_uri(builder, fromdocname)
        if refuri is None:
            return node.children
        res = nodes.reference(refuri=refuri)
        res += node.children
        return res

def env_get_outdated(app, env, added, changed, removed):
    qfile = re.compile('^.*(index|cpp-|headers/|classes/|namespaces/|structures/).*')
    return [it for it in app.env.all_docs if qfile.match(it) is not None]

def env_purge_doc(app, env, docname):
    app.env.domains['cpp'].parse_doxygen()
    app.env.domains['cpp'].gen_skeleton()

def cleanup_custom_nodes(app, doctree, fromdocname):
    for node in doctree.traverse(customnode):
        node.parent.remove(node)

def setup(app):
    if 'cpp' not in app.domains:
        raise ExtensionError('Extension must be loaded after cpp.')
    app.override_domain(CPPAPIDocDomain)

    app.add_directive_to_domain('cpp', 'autoclass', CPPAutoClassObject)
    app.add_directive_to_domain('cpp', 'autofunction', CPPAutoFunctionObject)
    app.add_directive_to_domain('cpp', 'autoheader', CPPAutoHeaderObject)
    app.add_directive_to_domain('cpp', 'automacro', CPPAutoMacroObject)
    app.add_directive_to_domain('cpp', 'automember', CPPAutoMemberObject)
    app.add_directive_to_domain('cpp', 'autonamespace', CPPAutoNamespaceObject)
    app.add_directive_to_domain('cpp', 'autostruct', CPPAutoStructObject)
    app.add_directive_to_domain('cpp', 'autoenum', CPPAutoEnumObject)

    app.add_index_to_domain('cpp', CppClassIndex)
    app.add_index_to_domain('cpp', CppFunctionIndex)

    app.add_config_value('qiapidoc_srcs', None, 'html')
    app.add_config_value('qiapidoc_gen_skeleton', False, 'html')

    app.connect('env-get-outdated', env_get_outdated)
    app.connect('env-purge-doc', env_purge_doc)
    # The HTTP writter chockes on nodes it does not understand when visiting the
    # tree. So remove our custom nodes just before this step.
    app.connect('doctree-resolved', cleanup_custom_nodes)
