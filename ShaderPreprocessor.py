import logging
logger = logging.getLogger(__name__)

class ShaderPreprocessorException(Exception):
    def __init__(self, linenum, msg):
        self.linenum = linenum
        self.message = msg

    def __repr__(self):
        return 'Shader Preprocessor Exception [Line No.{0}] : {1}'.format(self.linenum, self.message)

class ShaderPreprocessor(object):

    def __init__(self):
        self.shader = ''
        self.__VERSION__ = 100
        self.__LINE__ = 1
        self.defined = {
            'GL_ES'         : None,
        }

    def preprocess(self, shader):

        # TODO: replace multiline preprocessor statements with one-line statements

        for line in shader.splitlines(True):
            # remove the prefix whitespaces and tabs
            line = line.lstrip()

            if line.startswith('#'):
                line = self.process_line(line)
            self.shader += line
            self.__LINE__ += 1

        return True

    def process_line(self, line):
        # All macro names containing two consecutive underscores ( __ ) are reserved
        # for future use as predefined macro names. All macro names prefixed with "GL_"
        # ("GL" followed by a single underscore) are also reserved.
        if line.startswith('#define'):
            line = line[len('#define'):]
            macro_name = line.split()[0]
            if '__' in macro_name or macro_name.startswith('GL_'):
                raise ShaderPreprocessorException(self.__LINE__, 'reserved macro ({0}) defined'.format(macro_name))
        elif line.startswith('#undef'):
            line = line[len('#undef'):]
            macro_name = line.split()[0]
            if '__' in macro_name or macro_name.startswith('GL_'):
                raise ShaderPreprocessorException(self.__LINE__, 'reserved macro ({0}) undefined'.format(macro_name))

        if line.startswith('#version'):
            self.__VERSION__ = int(line.split()[1])

        if line.endswith('\n'):
            return '\n'
        else:
            return ''
