import logging
logger = logging.getLogger(__name__)

from ply import lex

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
        # multiplicative operators
        'STAR',
        # assignment operators
        'EQUAL',
        'SEMICOLON',
        'LEFT_BRACE', 'RIGHT_BRACE',
        'LEFT_PAREN', 'RIGHT_PAREN',
        # literal
        'INT_CONSTANT', 'FLOAT_CONSTANT', 'BOOL_CONSTANT',
    ]

    t_SEMICOLON = r';'

    # multiplicative operators
    t_STAR = r'\*'

    # assignment operators
    t_EQUAL = r'='

    t_LEFT_PAREN = r'\('
    t_RIGHT_PAREN = r'\)'
    t_LEFT_BRACE = r'\{'
    t_RIGHT_BRACE = r'\}'

    t_INT_CONSTANT = r'\d+([uU]|[lL]|[uU][lL]|[lL][uU])?'
    t_FLOAT_CONSTANT = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'
    t_BOOL_CONSTANT = r'true|false'

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
