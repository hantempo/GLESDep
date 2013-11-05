import logging
logger = logging.getLogger(__name__)

from subprocess import Popen, PIPE
from ply import yacc

def preprocess(filename, cpp_path='cpp', cpp_args='-DGL_ES'):

    path_list = [cpp_path]
    if isinstance(cpp_args, list):
        path_list += cpp_args
    elif cpp_args != '':
        path_list += [cpp_args]
    path_list += [filename]

    try:
        # Note the use of universal_newlines to treat all newlines
        # as \n for Python's purpose
        #
        pipe = Popen(path_list, stdout=PIPE, universal_newlines=True)
        text = pipe.communicate()[0]
    except OSError as e:
        raise RuntimeError("Unable to invoke 'cpp'.  " +
            'Make sure its path was passed correctly\n' +
            ('Original error: %s' % e))

    return text

class ShaderLexer(object):
    keywords = (
        'varying', 'uniform', 'attribute',
        'precision', 'lowp', 'mediump', 'highp',
        'vec2',
    )
    keywords_mapping = { k : k.upper() for k in keywords}

    tokens = keywords_mapping.values() + [
        'IDENTIFIER',
        'SEMICOLON',
    ]

    t_SEMICOLON = r';'

    t_ignore = '\t'

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_IDENTIFIER(self, t):
        r'[A-Za-z_][0-9A-Za-z]*'
        t.type = keywords_mapping.get(t.value, 'IDENTIFIER')
        return t

    def t_error(self, t):
        logger.error('Illegal character %s' % repr(t.value[0]))

#def p_varying_declaration(p):
    #'varying_declaration : VARYING IDENTIFIER IDENTIFIER SEMICOLON'
    #print p

class ShaderParserException(Exception):
    def __init__(self, linenum, msg):
        self.linenum = linenum
        self.message = msg

    def __repr__(self):
        return 'Shader Parser Exception [Line No.{0}] : {1}'.format(self.linenum, self.message)

class ShaderParser(object):

    def __init__(self, yacc_debug=False):
        self.lexer = ShaderLexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self,
            start='declaration_or_empty',
            debug=yacc_debug)

        self.version = 100

        self.uniforms = {}
        self.varyings = {}
        self.attributes = {}

    def p_declaration_or_empty(self, p):
        ''' declaration_or_empty : declaration
                                 | empty
        '''
        p[0] = p[1]

    def p_declaration(self, p):
        ''' declaration : declaration_body SEMICOLON
        '''
        p[0] = p[1]

    def p_declaration_body(self, p):
        ''' declaration_body : declaration_specifiers
        '''
        p[0] = p[1]

    def p_declaration_specifiers(self, p):
        ''' declaration_specifiers : category_qualifier type_specifier IDENTIFIER
        '''
        p[0] = p[1]

    def p_category_qualifier(self, p):
        ''' category_qualifier : VARYING
                               | UNIFORM
                               | ATTRIBUTE
        '''
        p[0] = p[1]

    def p_type_specifier(self, p):
        ''' type_specifier : VEC2
        '''
        p[0] = p[1]

    def p_empty(self, p):
        ''' empty : '''
        p[0] = None

    def p_error(self, p):
        if p:
            raise ShaderParserException(p.lineno, 'before: %s' % p.value)
        else:
            raise ShaderParserException(-1, 'at end of input')

    def parse(self, text, filename='', debuglevel=0):
        self.lexer.filename = filename
        self.lexer.reset_lineno()

        # check whether the first line of the input file contains "#version 300 es"
        parts = text.split('\n', 1)
        if parts[0].split() == ['#version', '300', 'es']:
            self.version = 300

        if len(parts) == 1:
            return ''
        else:
            return self.parser.parse(input=text,
                lexer=self.lexer,
                debug=debuglevel)
