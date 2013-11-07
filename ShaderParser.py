import logging
logger = logging.getLogger(__name__)

from subprocess import Popen, PIPE
from ply import lex, yacc

def preprocess(input_text, cpp_path='cpp', cpp_args='-DGL_ES'):

    path_list = [cpp_path]
    if isinstance(cpp_args, list):
        path_list += cpp_args
    elif cpp_args != '':
        path_list += [cpp_args]

    try:
        # Note the use of universal_newlines to treat all newlines
        # as \n for Python's purpose
        #
        pipe = Popen(path_list, stdin=PIPE, stdout=PIPE, universal_newlines=True)
        text = pipe.communicate(input=input_text)[0]
    except OSError as e:
        raise RuntimeError("Unable to invoke 'cpp'.  " +
            'Make sure its path was passed correctly\n' +
            ('Original error: %s' % e))

    # remove the leading comment lines
    lines = text.splitlines()
    lines = filter(lambda l : not l.lstrip().startswith('#'), lines)
    text = '\n'.join(lines)

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
        'void', 'bool', 'int', 'uint', 'float',
        'vec2', 'vec3', 'vec4',
        'bvec2', 'bvec3', 'bvec4',
        'ivec2', 'ivec3', 'ivec4',
        'uvec2', 'uvec3', 'uvec4',
        'mat2', 'mat3', 'mat4',
        'mat2x2', 'mat2x3', 'mat2x4',
        'mat3x2', 'mat3x3', 'mat3x4',
        'mat4x2', 'mat4x3', 'mat4x4',
        'sampler2D', 'sampler2DArray', 'sampler3D', 'samplerCube',
        'sampler2DShadow', 'sampler2DArrayShadow', 'samplerCubeShadow',
        'isampler2D', 'isampler2DArray', 'isampler3D', 'isamplerCube',
        'usampler2D', 'usampler2DArray', 'usampler3D', 'usamplerCube',
        # layout qualifiers
        'varying', 'uniform', 'attribute',
        # precision qualifiers
        'precision', 'lowp', 'mediump', 'highp',
    )
    keywords_mapping = { k : k.upper() for k in keywords}

    tokens = keywords_mapping.values() + [
        'IDENTIFIER',
        #'COMMENT',
        'SEMICOLON',
    ]

    t_SEMICOLON = r';'

    t_ignore = ' \t'

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    #def t_COMMENT(self, t):
        #r'/\*(.|\n)*?\*/'
        #t.lexer.lineno += t.value.count("\n")
        #return t

    def t_IDENTIFIER(self, t):
        r'[A-Za-z_][0-9A-Za-z_]*'
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

    @staticmethod
    def is_floating_point_type(type):
        return type in ('float', 'vec2', 'vec3', 'vec4',
            'mat2', 'mat3', 'mat4',
            'mat2x2', 'mat2x3', 'mat2x4',
            'mat3x2', 'mat3x3', 'mat3x4',
            'mat4x2', 'mat4x3', 'mat4x4')

    @staticmethod
    def is_integer_type(type):
        return type in ('bool', 'int', 'uint',
            'bvec2', 'bvec3', 'bvec4',
            'ivec2', 'ivec3', 'ivec4',
            'uvec2', 'uvec3', 'uvec4')

    @staticmethod
    def get_default_precision_qualifier(type, is_fragment_shader):
        if is_fragment_shader:
            if ShaderVariable.is_integer_type(type):
                return 'mediump'
            elif type in ('sampler2D', 'samplerCube'):
                return 'lowp'
            else:
                logger.error('Unexpected non-precision-qualified type in fragment shader : "%s"' % type)
        else:
            if ShaderVariable.is_floating_point_type(type) or ShaderVariable.is_integer_type(type):
                return 'highp'
            elif type in ('sampler2D', 'samplerCube'):
                return 'lowp'
            else:
                logger.error('Unexpected non-precision-qualified type in vertex shader : "%s"' % type)

    def __init__(self, type, name, layout_qualifier, precision_qualifier=None):
        self.type = type
        self.name = name
        self.layout_qualifier = layout_qualifier
        self.precision_qualifier = precision_qualifier

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
        self.uniform_variables = {}

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

    def p_declaration_specifiers1(self, p):
        ''' declaration_specifiers : layout_qualifier type_specifier IDENTIFIER
        '''
        p[0] = ShaderVariable(type=p[2], name=p[3], layout_qualifier=p[1])

    def p_declaration_specifiers2(self, p):
        ''' declaration_specifiers : layout_qualifier precision_qualifier type_specifier IDENTIFIER
        '''
        p[0] = ShaderVariable(type=p[3], name=p[4], layout_qualifier=p[1], precision_qualifier=p[2])

    def p_layout_qualifier(self, p):
        ''' layout_qualifier : VARYING
                             | UNIFORM
                             | ATTRIBUTE
        '''
        p[0] = p[1]

    def p_precision_qualifier(self, p):
        ''' precision_qualifier : LOWP
                                | MEDIUMP
                                | HIGHP
        '''
        p[0] = p[1]

    def p_type_specifier(self, p):
        ''' type_specifier : VOID
                           | BOOL
                           | INT
                           | UINT
                           | FLOAT
                           | VEC2
                           | VEC3
                           | VEC4
                           | BVEC2
                           | BVEC3
                           | BVEC4
                           | IVEC2
                           | IVEC3
                           | IVEC4
                           | UVEC2
                           | UVEC3
                           | UVEC4
                           | MAT2
                           | MAT3
                           | MAT4
                           | MAT2X2
                           | MAT2X3
                           | MAT2X4
                           | MAT3X2
                           | MAT3X3
                           | MAT3X4
                           | MAT4X2
                           | MAT4X3
                           | MAT4X4
                           | SAMPLER2D
                           | SAMPLER2DARRAY
                           | SAMPLER3D
                           | SAMPLERCUBE
                           | SAMPLER2DSHADOW
                           | SAMPLER2DARRAYSHADOW
                           | SAMPLERCUBESHADOW
                           | ISAMPLER2D
                           | ISAMPLER2DARRAY
                           | ISAMPLER3D
                           | ISAMPLERCUBE
                           | USAMPLER2D
                           | USAMPLER2DARRAY
                           | USAMPLER3D
                           | USAMPLERCUBE
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

        logger.debug('Input before pre-processor : "%s"' % (text))

        # check whether the first line of the input file contains "#version 300 es"
        parts = text.split('\n', 1)
        if parts[0].split() == ['#version', '300', 'es']:
            self.version = 300
            if len(parts) == 1:
                text = ''
            else:
                text = parts[1]

        if text:
            text = preprocess(text)

        logger.debug('Input after pre-processor : "%s"' % (text))

        io_variables = self.parser.parse(input=text,
            lexer=self.lexer,
            debug=debuglevel)
        for var in io_variables:
            # use default precision qualifier if equals None
            if not var.precision_qualifier:
                var.precision_qualifier = var.get_default_precision_qualifier(
                    var.type, fragment_shader)

            if var.is_input_variable(fragment_shader):
                self.input_variables[var.name] = var
            elif var.is_output_variable(fragment_shader):
                self.output_variables[var.name] = var
            elif var.layout_qualifier == 'uniform':
                self.uniform_variables[var.name] = var
