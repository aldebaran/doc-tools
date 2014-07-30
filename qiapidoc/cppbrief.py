"""
 Cpp Indexes

 where does the scene take place?
 here sir, here!!! I saw chaisaw, acid, and the like.
 what? this is just python code idiot!
"""

__author__ = (u"Cedric GESTES <gestes@aldebaran-robotics.com>")
__copyright__ = u"Copyright (C) 2011 Aldebaran Robotics"

#import re
from copy import deepcopy, copy

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.locale import l_, _
from sphinx.util.nodes import set_source_info
from sphinx.util.compat import Directive

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


class filebrief(nodes.General, nodes.Element):
    pass

class CPPBriefObject(Directive):
    """
    This directive create a summary for the current file
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    # option_spec = {
    #     'maxdepth': int,
    #     'functions': directives.flag,
    #     'classes': directives.flag,
    #     'brief': directives.flag,
    # }

    def run(self):
        env = self.state.document.settings.env
        ret = list()
        mynode = filebrief()
        mynode['parent'] = env.docname
        ret.append(mynode)
        return ret


def filebrief_nodefuncmap(doctree):
    """
    return a map of (function_name, node)

    node look like:
    <desc desctype="function" domain="cpp" noindex="False" objtype="function">
      <desc_signature first="False" ids="qi::log::LogStream::LogStream__X"
                                    names="qi::log::LogStream::LogStream__X">
        <desc_addname>qi::log::LogStream::</desc_addname>
        <desc_name>LogStream</desc_name>
        <desc_parameterlist>
          <desc_parameter noemph="True"><emphasis>const LogStream&</emphasis></desc_parameter>
        </desc_parameterlist>
      </desc_signature>
    </desc>
    """
    nodefuncmap = dict()
    for node in doctree.traverse(addnodes.desc):
        if not hasattr(node, "domain") or node['domain'] != "cpp":
            continue
        if not hasattr(node, "desctype") or node['desctype'] != "function":
            continue

        i = node.first_child_matching_class(addnodes.desc_signature)
        sig = node[i]
        if not sig:
            continue
        for refid in sig['ids']:
            newnode = node.deepcopy()
            i = newnode.first_child_matching_class(addnodes.desc_signature)
            desc_sig = newnode[i]
            newnode['noindex'] = True
            newnode.children = [ desc_sig ]
            nodefuncmap[refid] = newnode
    return nodefuncmap

#todo: sort function by namespace,
# do not display information in the link
# do not color something else than the function name
# class: display visibility
def filebrief_replace_node(app, doctree, itemtype, items):
    """ where does the scene take place?
        here sir, here!!! I saw chaisaw, acid, and the like.
        what? this is just python code idiot!
    """
    env = app.builder.env
    nodefuncmap = dict()

    if itemtype == "functions":
        nodefuncmap = filebrief_nodefuncmap(doctree)

    listnode = nodes.bullet_list()
    for refname, (docname, type, theid) in sorted(items.iteritems()):
        pnode   = nodes.paragraph()
        if itemtype == "classes":
            pnode   = nodes.paragraph("class ", "class ")
        refnode = nodes.reference(refname, refname, refdocname=docname, refid=theid)

        retnode = refnode
        cnode = nodefuncmap.get(theid)
        if cnode:
            (_, fname) = split_func_name(refname)
            refnode = nodes.reference(fname, fname, refdocname=docname, refid=theid)
            i = cnode[0].first_child_matching_class(addnodes.desc_name)
            cnode[0][i] = refnode
            cnode.children = cnode[0].children
            retnode = cnode
        pnode.append(retnode)
        listnode.append(pnode)
    return listnode


class BriefEnv:
    """ store func/type/class/mem associated to a docname """
    def __init__(self, refname=None, docname=None, type=None, theid=None, scope='global'):
        """ type could be: global, class, namespace
            name is the name of the object
        """
        self.refname    = refname
        self.docname    = docname
        self.type       = type
        self.theid      = theid

        self.scope      = scope

        #dict of docname,type,theid
        self.macros     = dict()
        self.functions  = dict()
        self.types      = dict()
        self.members    = dict()
        #dict of briefenv
        self.classes    = dict()
        self.namespaces = dict()

    def add(self, refname, docname, type, theid):
        if type == "function":
            self.functions[refname] = (docname, type, theid)
        elif type == "class":
            self.classes[refname]   = BriefEnv(refname, docname, type, theid, scope='class')
        elif type == "type":
            self.types[refname]     = (docname, type, theid)
        elif type == "member":
            self.members[refname]   = (docname, type, theid)
        elif type == "automacro":
            self.macros[refname]    = (docname, type, theid)

    def _populate(self, obj, func):
        #move object to belonging classes/namespace
        #use black magic when applicable
        fctscopy = deepcopy(obj)
        for refname, (docname, type, theid) in fctscopy.iteritems():
            (_ns, _name) = split_func_name(refname)
            if not _ns:
                continue
            if _ns in self.classes:
                be = self.classes[_ns]
            else:
                be = self.namespaces.setdefault(_ns, BriefEnv(_ns, scope='namespace'))

            if func == "function":
                be.functions[refname] = (docname, type, theid)
            elif func == "type":
                be.types[refname] = (docname, type, theid)
            elif func == "member":
                be.members[refname] = (docname, type, theid)
            elif func == "class":
                be.classes[refname] = (docname, type, theid)
            elif fund == "automacro":
                be.macros[refname] = (docname, type, theid)
            del obj[refname]

    def _populate_class(self):
        #move classes to subclasses and namespaces
        fctscopy = deepcopy(self.classes)
        for refname, be in fctscopy.iteritems():
            (_ns, _name) = split_func_name(refname)
            if not _ns:
                continue
            if _ns in self.classes:
                self.classes[_ns].classes[refname] = be
                del self.classes[refname]
            if _ns in self.namespaces:
                self.namespaces[_ns].classes[refname] = be
                del self.classes[refname]

    def populate(self):
        self._populate(self.functions, "function")
        self._populate(self.members  , "member"  )
        self._populate(self.types    , "type"    )
        self._populate(self.macros   , "automacro")
        self._populate_class()

    def render_sub(self, app, doctree, objs, n1, n2):
        if objs:
            #pni  = nodes.list_item()
            pni  = nodes.paragraph()
            pni  = nodes.definition_list_item()
            prub = nodes.rubric(text=n1)
            st = nodes.strong()
            st.append(prub)
            pni.append(st)
            pbl = nodes.bullet_list()
            pni.append(pbl)
            for (n, be) in objs.iteritems():
                ni  = nodes.list_item()
                prub = nodes.paragraph(text=n2 + n)
                pbl.append(ni)
                ni.append(prub)
                ni.append(be.render(app, doctree))
            return pni

    def render_simple(self, app, doctree, objs, n1, n2):
        if objs:
            #ni  = nodes.list_item()
            ni  = nodes.definition_list_item()
            rub = nodes.rubric(text=n1)
            st = nodes.strong()
            st.append(rub)
            ren = filebrief_replace_node(app, doctree, n2, objs)
            ni.append(st)
            ni.append(ren)
            return ni

    def render(self, app, doctree):
        rootnode = nodes.bullet_list()
        rootnode = nodes.paragraph()
        rootnode = nodes.definition_list()
        prepend = ""
        append = ""
        if self.scope == "global":
            prepend = "Global "
        if self.scope == "class":
            append = " (class %s)" % self.refname
        elif self.scope == "namespace":
            append = " (namespace %s)" % self.refname

        n = self.render_sub(app, doctree, self.namespaces,
                            prepend + "Namespaces" + append,
                            "namespace ")
        if n:
            rootnode.append(n)
        n = self.render_sub(app, doctree, self.classes,
                            prepend + "Classes" + append,
                            "class ")
        if n:
            rootnode.append(n)
        n = self.render_simple(app, doctree, self.functions,
                               prepend + "Functions"  + append,
                               "functions")
        if n:
            rootnode.append(n)
        n = self.render_simple(app, doctree, self.members,
                               prepend + "Members"  + append,
                               "members")
        if n:
            rootnode.append(n)
        n = self.render_simple(app, doctree, self.types,
                               prepend + "Types"  + append,
                               "types")
        if n:
            rootnode.append(n)
        n = self.render_simple(app, doctree, self.macros,
                               prepend + "Macros" + append,
                               "macros");
        if n:
            rootnode.append(n)
        return rootnode

def process_filebrief_nodes(app, doctree, fromdocname):
    """ process each filebrief node

        replace the empty node by a full shiny new one
    """

    env = app.builder.env
    bemap = dict()

    for refname, (docname, type, theid) in env.domains["cpp"].data['objects'].iteritems():
        be = bemap.setdefault(docname, BriefEnv())
        be.add(refname, docname, type, theid)
    for v in bemap.values():
        v.populate()

    for node in doctree.traverse(filebrief):
        rootnode = nodes.paragraph()
        be = bemap.get(node['parent'])
        if not be:
            be = BriefEnv()

        newnode = be.render(app, doctree)
        node.replace_self(newnode)


#this is included and called from qiapidoc setup
def setup(app):
    if "cpp" not in app.domains:
        raise ExtensionError('domain %s not yet registered' % domain)
    app.add_node(filebrief)
    app.connect('doctree-resolved', process_filebrief_nodes)
    app.domains["cpp"].directives["brief"] = CPPBriefObject
