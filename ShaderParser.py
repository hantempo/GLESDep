import logging
logger = logging.getLogger(__name__)

from subprocess import Popen, PIPE
from ply import lex, yacc

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

    def __init__(self):
        self.last_token = None

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    def reset_lineno(self):
        self.lexer.lineno = 1

    keywords = (
        # types
        'vec2', 'vec3', 'float',
        # layout qualifiers
        'varying', 'uniform', 'attribute',
        #'precision', 'lowp', 'mediump', 'highp',
    )
    keywords_mapping = { k : k.upper() for k in keywords}

    tokens = keywords_mapping.values() + [
        'IDENTIFIER',
        'SEMICOLON',
    ]

    t_SEMICOLON = r';'

    t_ignore = ' \t'

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_IDENTIFIER(self, t):
        r'[A-Za-z_][0-9A-Za-z]*'
        t.type = self.keywords_mapping.get(t.value, 'IDENTIFIER')
        return t

    def t_error(self, t):
        logger.error('Illegal character %s' % repr(t.value[0]))

    def build(self, **kwargs):
        self.lexer = lex.lex(object=self, **kwargs)

class ShaderParserException(Exception):
    def __init__(self, linenum, msg):
        self.linenum = linenum
        self.message = msg

    def __repr__(self):
        return 'Shader Parser Exception [Line No.{0}] : {1}'.format(self.linenum, self.message)

class ShaderVariable(object):

    def __init__(self, type, name, layout_qualifier):
        self.type = type
        self.name = name
        self.layout_qualifier = layout_qualifier

    def is_input_variable(self, fragment_shader):
        if fragment_shader:
            return self.layout_qualifier in ('varying')
        else:
            return self.layout_qualifier in ('attribute')

    def is_output_variable(self, fragment_shader):
        if fragment_shader:
            return self.layout_qualifier in ()
        else:
            return self.layout_qualifier in ('varying')

class ShaderParser(object):

    def __init__(self, debug=False):
        self.lexer = ShaderLexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self,
            start='declaration_list_or_empty',
            debug=debug)

        self.version = 100
        self.input_variables = {}
        self.output_variables = {}

        self.uniforms = {}
        self.varyings = {}
        self.attributes = {}

    def p_declaration_list_or_empty(self, p):
        ''' declaration_list_or_empty : declaration_list
                                      | empty
        '''
        if p[1] == None:
            p[0] = []
        else:
            p[0] = p[1]

    def p_declaration_list_1(self, p):
        ''' declaration_list : declaration_list declaration
        '''
        p[0] = p[1] + [p[2]]

    def p_declaration_list_2(self, p):
        ''' declaration_list : declaration
        '''
        p[0] = [p[1]]

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
        p[0] = ShaderVariable(type=p[2], name=p[3], layout_qualifier=p[1])

    def p_category_qualifier(self, p):
        ''' category_qualifier : VARYING
                               | UNIFORM
                               | ATTRIBUTE
        '''
        p[0] = p[1]

    def p_type_specifier(self, p):
        ''' type_specifier : FLOAT
                           | VEC2
                           | VEC3
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

    def parse(self, text, fragment_shader=True, filename='', debuglevel=0):
        self.lexer.filename = filename
        self.lexer.build()
        self.lexer.reset_lineno()

        # check whether the first line of the input file contains "#version 300 es"
        parts = text.split('\n', 1)
        if parts[0].split() == ['#version', '300', 'es']:
            self.version = 300
            if len(parts) == 1:
                text = ''
            else:
                text = parts[1]

        io_variables = self.parser.parse(input=text,
            lexer=self.lexer,
            debug=debuglevel)
        for var in io_variables:
            if var.is_input_variable(fragment_shader):
                self.input_variables[var.name] = var
            elif var.is_output_variable(fragment_shader):
                self.output_variables[var.name] = var
