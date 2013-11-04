import logging
logger = logging.getLogger(__name__)

import ply.lex as lex

tokens = [
    'IDENTIFIER', 'WHITESPACE',
    'NUMBER', 'STRING',
    'COMMENT',
]

def t_WHITESPACE(t):
    r'\s+'
    t.lexer.lineno += t.value.count('\n')
    return t

t_IDENTIFIER = r'[A-Za-z_][\w_]*'

# Integer literal
t_NUMBER = r'(((((0x)|(0X))[0-9a-fA-F]+)|(\d+))([uU]|[lL]|[uU][lL]|[lL][uU])?) | (((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?)'

# String literal
def t_STRING(t):
    r'\"([^\\\n]|(\\(.|\n)))*?\"'
    t.lexer.lineno += t.value.count("\n")
    return t

# Comment
def t_COMMENT(t):
    r'(/\*(.|\n)*?\*/)|(//.*?\n)'
    t.lexer.lineno += t.value.count("\n")
    return t

def t_error(t):
    t.type = t.value[0]
    t.value = t.value[0]
    t.lexer.skip(1)
    return t

lexer = lex.lex()

class ShaderPreprocessorException(Exception):
    def __init__(self, linenum, msg):
        self.linenum = linenum
        self.message = msg

    def __repr__(self):
        return 'Shader Preprocessor Exception [Line No.{0}] : {1}'.format(self.linenum, self.message)

# remove leading and trailing whitespaces
def tokenstrip(tokens):
    i = 0
    while i < len(tokens) and tokens[i].type == 'WHITESPACE':
        i += 1
    del tokens[:i]

    i = len(tokens)-1
    while i >= 0 and tokens[i].type == 'WHITESPACE':
        i -= 1
    del tokens[i+1:]

    return tokens

#ShaderVariable = collections.namedtuple('ShaderVariable',
    #['name', 'location', 'size', 'type', 'precision'])

# preprocessor macros
class Macro(object):

    @staticmethod
    def IsValidName(name):
        # All macro names containing two consecutive underscores ( __ ) are reserved for future use as predefined macro names.
        # All macro names prefixed with "GL_" ("GL" followed by a single underscore) are also reserved.
        if '__' in name:
            return False
        if name.startswith('GL_'):
            return False
        return True

    def __init__(self, name, value):
        self.name = name
        self.value = value

class ShaderPreprocessor(object):

    def __init__(self):
        self.lexer = lexer

        # default version is 100, for GLES2
        self.version = 100

        self.output = ''

    def preprocess(self, input, filename=''):
        self.filename = filename

        for line in self.group_lines(input):
            logger.debug('Before preprocessor line {0} tokens : {1}'.format(self.lexer.lineno, line))
            # skip the leading whitespaces
            for i, token in enumerate(line):
                if token.type != 'WHITESPACE':
                    break

            # preprocessor directive
            if token.value == '#':
                name = line[i+1].value
                args = tokenstrip(line[i+2:])

                if name == 'version':
                    self.version = int(args[0].value)
                elif name == 'define':
                    self.define(args)
                elif name == 'undef':
                    self.undef(args)
            else:
                for token in tokenstrip(line[i+1:]):
                    self.output += token.value

    # split a input string into lines and tokenize each line
    def group_lines(self, input):
        # strip the trailing whitespaces
        lines = [line.rstrip() for line in input.splitlines()]

        lexer.input(input)
        lexer.lineno = 1

        current_line = []
        while True:
            token = lexer.token()
            if token == None:
                break;
            current_line.append(token)

            if token.type == 'WHITESPACE' and '\n' in token.value:
                yield current_line
                current_line = []

        if current_line:
            yield current_line

    def define(self, tokens):
        macro_name = tokens[0].value
        if not Macro.IsValidName(macro_name):
            raise ShaderPreprocessorException(self.lexer.lineno, 'Invalid macro name ({0}) to define'.format(macro_name))
        m = Macro(macro_name.value)

    def undef(self, tokens):
        macro_name = tokens[0].value
        if not Macro.IsValidName(macro_name):
            raise ShaderPreprocessorException(self.lexer.lineno, 'Invalid macro name ({0}) to undef'.format(macro_name))
