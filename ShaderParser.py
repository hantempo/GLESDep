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

# categories of variable types
def is_floating_point_type(type):
    return type in (
        'float', 'vec2', 'vec3', 'vec4',
        'mat2', 'mat3', 'mat4',
        'mat2x2', 'mat2x3', 'mat2x4',
        'mat3x2', 'mat3x3', 'mat3x4',
        'mat4x2', 'mat4x3', 'mat4x4')

def is_integer_type(type):
    return type in (
        'bool', 'int', 'uint',
        'bvec2', 'bvec3', 'bvec4',
        'ivec2', 'ivec3', 'ivec4',
        'uvec2', 'uvec3', 'uvec4')

def is_sampler_type(type):
    return type in (
        'sampler2D', 'sampler2DArray', 'sampler3D', 'samplerCube',
        'sampler2DShadow', 'sampler2DArrayShadow', 'samplerCubeShadow',
        'isampler2D', 'isampler2DArray', 'isampler3D', 'isamplerCube',
        'usampler2D', 'usampler2DArray', 'usampler3D', 'usamplerCube')

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
        'varying', 'uniform', 'attribute', 'in', 'out',
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

class PrecisionStatement(object):

    def __init__(self, precision_qualifier, type_specifier):
        self.precision_qualifier = precision_qualifier
        self.type_specifier = type_specifier

class Variable(object):

    def __init__(self, type, name, layout_qualifier=None, precision_qualifier=None):
        self.type = type
        self.name = name
        self.layout_qualifier = layout_qualifier
        self.precision_qualifier = precision_qualifier

    def __repr__(self):
        return 'Shader variable : %s %s %s %s' % (
            self.layout_qualifier, self.precision_qualifier,
            self.type, self.name)

    def is_input_variable(self, fragment_shader):
        if fragment_shader:
            return self.layout_qualifier in ('varying', 'in')
        else:
            return self.layout_qualifier in ('attribute', 'in')

    def is_output_variable(self, fragment_shader):
        if fragment_shader:
            return self.layout_qualifier in ('out')
        else:
            return self.layout_qualifier in ('varying', 'out')

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

        self.default_precision_qualifier = {}

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
        p[0] = Variable(type=p[2], name=p[3], layout_qualifier=p[1])

    def p_declaration_specifiers2(self, p):
        ''' declaration_specifiers : layout_qualifier precision_qualifier type_specifier IDENTIFIER
        '''
        p[0] = Variable(type=p[3], name=p[4], layout_qualifier=p[1], precision_qualifier=p[2])

    # precision statement : set default precision qualifier for some type(s)
    def p_declaration_specifiers3(self, p):
        ''' declaration_specifiers : PRECISION precision_qualifier type_specifier
        '''
        p[0] = PrecisionStatement(precision_qualifier=p[2], type_specifier=p[3])

    def p_layout_qualifier(self, p):
        ''' layout_qualifier : VARYING
                             | UNIFORM
                             | ATTRIBUTE
                             | IN
                             | OUT
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

        self.initialize_default_precision_qualifiers(fragment_shader)

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

        declaration_list = self.parser.parse(input=text,
            lexer=self.lexer,
            debug=debuglevel)
        for decal in declaration_list:
            if isinstance(decal, PrecisionStatement):
                self.set_default_precision_qualifier(decal.type_specifier, decal.precision_qualifier)
            elif isinstance(decal, Variable):
                var = decal
                # use default precision qualifier if equals None
                if not var.precision_qualifier:
                    var.precision_qualifier = self.get_default_precision_qualifier(var.type)
                    if var.precision_qualifier == None:
                        logger.error('Unexpected non-precision-qualified variable: "%s"' % str(var))

                if var.is_input_variable(fragment_shader):
                    self.input_variables[var.name] = var
                elif var.is_output_variable(fragment_shader):
                    self.output_variables[var.name] = var
                elif var.layout_qualifier == 'uniform':
                    self.uniform_variables[var.name] = var

    def initialize_default_precision_qualifiers(self, is_fragment_shader):
        if is_fragment_shader:
            self.default_precision_qualifier['int'] = 'mediump'
            self.default_precision_qualifier['sampler2D'] = 'lowp'
            self.default_precision_qualifier['samplerCube'] = 'lowp'
        else:
            self.default_precision_qualifier['int'] = 'highp'
            self.default_precision_qualifier['float'] = 'highp'
            self.default_precision_qualifier['sampler2D'] = 'lowp'
            self.default_precision_qualifier['samplerCube'] = 'lowp'

    def get_default_precision_qualifier(self, type):
        if is_integer_type(type):
            type = 'int'
        elif is_floating_point_type(type):
            type = 'float'
        return self.default_precision_qualifier.get(type, None)

    # in "precision precision-qualifier type-qualifier"
    # valid type qualifier : int, float or any of sampler types
    # valid precision_qualifier : lowp, mediump, highp
    def set_default_precision_qualifier(self, type, precision_qualifier):
        if precision_qualifier not in ('lowp', 'mediump', 'highp'):
            logger.error('Unexpected precision-qualifier in default precision qualifier setting : "%s"' % precision_qualifier)
            return

        if is_sampler_type(type) or type in ('int', 'float'):
            self.default_precision_qualifier[type] = precision_qualifier
        else:
            logger.error('Unexpected type-qualifier in default precision qualifier setting : "%s"' % type)
