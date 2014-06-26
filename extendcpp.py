#!/usr/bin/env python
##
## extendcpp.py
## Login : <ctaf@Cedric-GESTESs-MacBook.local>
## Started on  Sun Nov 20 20:00:02 2011 Cedric GESTES
## $Id$
##
## Author(s):
##  - Cedric GESTES <gestes@aldebaran-robotics.com>>
##
## Copyright (C) 2011 Aldebaran Robotics
##

"""
 Cpp Indexes

 where does the scene take place?
 here sir, here!!! I saw chaisaw, acid, and the like.
 what? this is just python code idiot!
"""

__author__ = (u"Cedric GESTES <gestes@aldebaran-robotics.com>")
__copyright__ = u"Copyright (C) 2011 Aldebaran Robotics"

import re
from sphinx.locale import l_, _
from sphinx.domains import Index


def split_func_name(name):
    fnames = name.rsplit("::", 1)
    if len(fnames) == 2:
        fpath = fnames[0]
        fname = fnames[1]
    else:
        fpath = ""
        fname = name
    return (fpath, fname)

class CppIndex(Index):
    """
    Index subclass to provide the Python module index.

    """
    # entries = [ ('l', [ ["logError", 0, '', '', '', '', ''],
    #                     ["LogManager.logError", 2, 'logmanager', 'logWarning', '', '', ''],
    #                     ["LogStream.logError", 2, 'logmanager', 'logWarning', '', '', ''],
    #                     ["logWarning", 0, 'logmanager', 'logError', '', '', '']
    #                   ])]
    # return (entries, False)

    def generate(self, docnames=None):
        content = {}

        functable = dict()
        for refname, (docname, type, theid) in self.domain.data['objects'].iteritems():
            if type == self._type:
                fnames = refname.rsplit("::", 1)
                if len(fnames) == 2:
                    fname = fnames[1]
                    fpath = fnames[0]
                else:
                    fname = refname
                    fpath = "global"
                e = functable.setdefault(fname, [])
                e.append([refname, (docname, type, theid)])

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
    """
    Index subclass to provide the Python module index.
    """

    name = 'classindex'
    localname = l_('C++ Class Index')
    shortname = l_('classes')
    _type = 'class'

class CppFunctionIndex(CppIndex):
    """
    Index subclass to provide the Python module index.
    """

    name = 'funcindex'
    localname = l_('C++ Function Index')
    shortname = l_('functions')
    _type = 'function'



#import re
from copy import deepcopy, copy

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.locale import l_, _
from sphinx.util.nodes import set_source_info
from sphinx.util.compat import Directive

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

def setup(app):
    if "cpp" not in app.domains:
        raise ExtensionError('domain %s not yet registered' % domain)
    #if indices has not been set by CPPDomain indice refer to Domain.indices which is not cool
    #create a new list only for CPPDomain.indices.
    if not len(app.domains["cpp"].indices):
        app.domains["cpp"].indices = []
    app.domains["cpp"].indices.append(CppClassIndex)
    app.domains["cpp"].indices.append(CppFunctionIndex)
