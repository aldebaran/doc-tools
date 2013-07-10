from qiapidoc.data.cppclass import CPPClass

class CPPStruct(CPPClass):
    def __init__(self, *args, **kwargs):
        CPPClass.__init__(self, *args, **kwargs)
        self.sorting_type = 'struct'
