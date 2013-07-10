class CPPLocation:
    def __init__(self, element):
        self.header_filename = element.attrib['file']
        self.header_line = element.attrib['line']
        self.body_filename = element.attrib['bodyfile']
        self.body_line = element.attrib['bodystart']

    def __str__(self):
        return '{}:{}'.format(self.header_filename, self.header_line)
