import re
import string
import sys

from qiapidoc.mycpp import DefinitionParser, DefinitionError
from qiapidoc.data.rootparser import RootParser

_WORD = re.compile('^\w+$')

class DocParser(RootParser):
    def __init__(self, *args, **kwargs):
        RootParser.__init__(self, *args, **kwargs)
        self.sorting_type, self._definition = None, ''

    def _get_fulltext(self, element):
        return ''.join(element.itertext())

    def _replace_text(self, element, text=None, frmt='{full_text}'):
        full_text = self._get_fulltext(element) if text is None else text
        for child in element:
            child.clear()
        element.text = frmt.format(full_text = full_text)

    def _parse_briefdescription(self, element):
        self.parse(element)

    def _parse_detaileddescription(self, element):
        self.parse(element)

    def _parse_para(self, element):
        lst, self._contains_includename = None, False
        self.parse(element)
        if self._backtrace[-1] == 'briefdescription':
            lst = self.brief()
        elif self._backtrace[-1] == 'detaileddescription':
            lst = self.details()
        else:
            self._replace_text(element)
        if lst is not None:
            if lst and lst[-1] != '':
                lst.append('')
            res = self._get_fulltext(element).splitlines()
            if self._contains_includename:
                res[0] = res[0].lstrip()
            lst.extend(res)

    def _parse_verbatim(self, element):
        # This part needs some explaination I guess. When using \verbatim, even
        # stars in the C++ comment are kept (I mean the stars used to align
        # comment). We need to delete them, since they are not part of the text
        # the user wrote.
        #
        # The two list comprehensions give a list of the characters present in
        # the verbatim block by column. Example:
        #
        #   This is the first sentence in verbatim block.
        #   Second sentence is there.
        #
        # Will give the following characters list: [['T', 'S'], ['h', 'e'], ...]
        # with only each character once (still by column). When this is done,
        # we just have to calculate the longuest prefix (if there is one
        # character in the list, every line begins with the same character) and
        # then we check that the first real character is *. If it is the case,
        # we probably have the stars of the C++ comment. This can fail if the
        # detailed description only conatins a list, and doesn't use aligned
        # stars in its comment. Should we set a rule on this to be sure?
        lines = element.text.splitlines()
        characters = [list(line.ljust(10000)) for line in lines]
        characters = [list(set(l)) for l in zip(*characters)]
        tmp = ''
        try:
            while len(characters[0]) == 1:
                tmp += characters[0][0]
                del characters[0]
        except IndexError:
            pass
        try:
            if tmp.split()[0] == '*':
                lines = [line.lstrip()[2:] for line in lines]
        except IndexError:
            pass
        element.text = '\n'.join(lines)

    def _in_detaileddescription(self):
        return ('detaileddescription' in self._backtrace)

    def _in_briefdescription(self):
        return ('briefdescription' in self._backtrace)

    def _parse_type(self, element):
        self._definition += self._get_fulltext(element)

    def _parse_definition(self, element):
        # XXX: This function targets common cases. It could break on some
        #      stuff. If sphinx complains that it cannot parse some definition
        #      and the type is present twice in it, you should check here. If
        #      you find some function in documentation with return type removed,
        #      you should check here.
        #
        # This part also needs detailed description :( Doxygen has a weird
        # behavior with definition element. Sometimes it contains only the name
        # of the compound documented, and sometimes it also contains the type
        # (already defined and parsed in type element).
        #
        # This means that we need to search for the type in the definition.
        # Could be easy, if it was at the beginning with the same layout BUT:
        #  - Spacing can be completely different.
        #  - Type can be written differently in definition and in type
        #    (namespaces in one of them, static, ...)
        #  - Return type can be found in function name....................
        #    (T qi::Atomic<T>::operator)
        #
        # First split_tokens is there to split the definition and the type into
        # tokens (either words or special characters ('::' fives [':', ':']).
        # It also escapes everything between two <> so that types in there
        # won't be matched.
        #
        # Once done, we try to find type in definition. If it is there, we
        # reset definition to '' to avoid having two types and this is done.
        def is_word(word):
            return _WORD.match(word) is not None
        def sublist_in_list(sublst, lst):
            len_sublst = len(sublst)
            for it in xrange(len(lst) - len_sublst + 1):
                if lst[it:it + len_sublst] == sublst:
                    return True
            return False
        def split_tokens(def_):
            # Split words and the rest of the world. Also strips and splits the
            # result. Once done, we have a list of lists containing either a
            # word or a list of special characters split on spaces:
            # Example:
            #   String 'QI_API word lala* foo::a<f** >::q'
            #   Gives [['QI_API'], ['word'], ['lala'], ['*'], ['foo'], ['::'],
            #          ['a'], ['<'], ['f'], ['**', '>::'], ['q']]
            toks = [it.strip().split() for it in re.split('(\w+)', def_) if it.strip()]
            # This line removes removes _API defines from definition.
            #   Gives [[], ['word'], ['lala'], ['*'], ['foo'], ['::'], ['a'],
            #          ['<'], ['f'], ['**', '>::'], ['q']]
            toks = [[it_ for it_ in it if 'API' not in it_] for it in toks]
            # This line splits special characters in one token by character.
            #   Gives [['word'], ['lala'], ['*'], ['foo'], [':', ':'], ['a'],
            #          ['<'], ['f'], ['*', '*'], ['>', ':', ':'], ['q']]
            toks = [[it] if is_word(it) else list(it) for it in sum(toks, [])]
            # Then we remove every token between <> (included).
            #   Gives ['word', 'lala', '*', 'foo', ':', ':', 'a', ':', ':', 'q']
            tmp, toks_tmp, toks = 0, sum(toks, []), []
            for tok in toks_tmp:
                if tok == '<': tmp += 1
                elif tok == '>': tmp -= 1
                elif not tmp: toks.append(tok)
            return toks
        tmp = [split_tokens(self._definition), split_tokens(element.text)]
        if sublist_in_list(*tmp):
            self._definition = u''
        self._definition += u' ' + element.text

    def _parse_argsstring(self, element):
        if element.text is not None:
            self._definition += element.text

    def get_obj(self):
        try:
            _def = DefinitionParser(self._definition)
            self.copy_obj(self._get_def_function()(_def))
        except DefinitionError:
            print >> sys.stderr, 'Could not parse following doxygen',
            print >> sys.stderr, 'definition:', self._definition
            return False
        return True

    def _get_def_function(self):
        raise NotImplementedError('must be implemented by child.')
