import logging, collections
logger = logging.getLogger(__name__)

import re
import ply.lex as lex

tokens = (
    'ID', 'WHITESPACE',
    'INT_CONST', 'FLOAT_CONST', 'STR_CONST', 'CHARACTER_CONST',
    'COMMENT',
)

def t_WHITESPACE(t):
    r'\s+'
    t.lexer.lineno += t.value.count('\n')
    return t

t_ID = r'[A-Za-z_][\w_]*'

# Integer literal
t_INT_CONST = r'(((((0x)|(0X))[0-9a-fA-F]+)|(\d+))([uU]|[lL]|[uU][lL]|[lL][uU])?)'

# Floating literal
t_FLOAT_CONST = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'

# String literal
def t_STR_CONST(t):
    r'\"([^\\\n]|(\\(.|\n)))*?\"'
    t.lexer.lineno += t.value.count("\n")
    return t

# Character constant 'c' or L'c'
def t_CHARACTER_CONST(t):
    r'(L)?\'([^\\\n]|(\\(.|\n)))*?\''
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

class ShaderParserException(Exception):
    def __init__(self, linenum, msg):
        self.linenum = linenum
        self.message = msg

    def __repr__(self):
        return 'Shader Parser Exception [Line No.{0}] : {1}'.format(self.linenum, self.message)

ShaderIOVariable = collections.namedtuple('ShaderIOVariable',
    ['name', 'location', 'size', 'type', 'precision'])

class ShaderParser(object):

    def __init__(self):
        self.lexer = lexer

        # default version is 100, for GLES2
        self.version = 100

        self.uniforms = {}

        self.record_token_ids()

    # A checking for the used lexer and fetch the token IDs
    def record_token_ids(self):
        # for the token type for whitespaces
        self.lexer.input(" ")
        token = self.lexer.token()
        if not token or token.value != " ":
            self.t_SPACE = None
        else:
            self.t_SPACE = token.type

        # for the token type for newlines
        self.lexer.input("\n")
        token = self.lexer.token()
        if not token or token.value != "\n":
            logger.error("Couldn't determine the token for newlines")
        else:
            self.t_NEWLINE = token.type

        self.t_WHITESPACE = (self.t_SPACE, self.t_NEWLINE)

    # remove leading and trailing whitespaces
    def tokenstrip(self, tokens):
        i = 0
        while i < len(tokens) and tokens[i].type in self.t_WHITESPACE:
            i += 1
        del tokens[:i]

        i = len(tokens)-1
        while i >= 0 and tokens[i].type in self.t_WHITESPACE:
            i -= 1
        del tokens[i+1:]

        return tokens

    def parse(self, input, filename=''):
        self.filename = filename

        for line in self.group_lines(input):
            # skip the leading whitespaces
            for i, token in enumerate(line):
                if token.type not in self.t_WHITESPACE:
                    break
            # preprocessor directive
            if token.value == '#':
                name = line[i+1].value
                args = self.tokenstrip(line[i+2:])

                if name == 'version':
                    self.version = int(args[0].value)

    # split a input string into lines and tokenize each line
    def group_lines(self, input):
        lexer = self.lexer.clone()

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

            if token.type in self.t_WHITESPACE and '\n' in token.value:
                yield current_line
                current_line = []

        if current_line:
            yield current_line
