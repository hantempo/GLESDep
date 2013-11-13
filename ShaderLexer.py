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
        'const', 'struct',
        # jumps
        'break', 'continue', 'do', 'else', 'for', 'if', 'discard',
        'return', 'switch', 'case', 'default', 'while',
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
        'varying', 'uniform', 'attribute', 'in', 'out', 'inout',
        'centroid', 'flat', 'smooth', 'layout', 'invariant',
        # precision qualifiers
        'precision', 'lowp', 'mediump', 'highp',
    )
    keywords_mapping = { k : k.upper() for k in keywords}

    tokens = keywords_mapping.values() + [
        'IDENTIFIER',
        # literal
        'INT_CONSTANT', 'FLOAT_CONSTANT', 'BOOL_CONSTANT',
        #'UINT_CONSTANT',

        # Operators (+,-,*,/,%,|,&,~,^,<<,>>, ||, &&, !, <, <=, >, >=, ==, !=)
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO',
        'OR', 'AND', 'NOT', 'XOR', 'LSHIFT', 'RSHIFT',
        'LOR', 'LAND', 'LNOT',
        'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',

        # Assignment (=, *=, /=, %=, +=, -=, <<=, >>=, &=, ^=, |=)
        'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',
        'LSHIFTEQUAL','RSHIFTEQUAL', 'ANDEQUAL', 'XOREQUAL', 'OREQUAL',

        # Increment/decrement (++,--)
        'PLUSPLUS', 'MINUSMINUS',

        # Structure dereference (->)
        'ARROW',

        # Ternary operator (?)
        'TERNARY',

        # Delimeters ( ) [ ] { } , . ; :
        'LPAREN', 'RPAREN',
        'LBRACKET', 'RBRACKET',
        'LBRACE', 'RBRACE',
        'COMMA', 'DOT', 'SEMI', 'COLON',
    ]

    # Operators
    t_PLUS             = r'\+'
    t_MINUS            = r'-'
    t_TIMES            = r'\*'
    t_DIVIDE           = r'/'
    t_MODULO           = r'%'
    t_OR               = r'\|'
    t_AND              = r'&'
    t_NOT              = r'~'
    t_XOR              = r'\^'
    t_LSHIFT           = r'<<'
    t_RSHIFT           = r'>>'
    t_LOR              = r'\|\|'
    t_LAND             = r'&&'
    t_LNOT             = r'!'
    t_LT               = r'<'
    t_GT               = r'>'
    t_LE               = r'<='
    t_GE               = r'>='
    t_EQ               = r'=='
    t_NE               = r'!='

    # Assignment operators

    t_EQUALS           = r'='
    t_TIMESEQUAL       = r'\*='
    t_DIVEQUAL         = r'/='
    t_MODEQUAL         = r'%='
    t_PLUSEQUAL        = r'\+='
    t_MINUSEQUAL       = r'-='
    t_LSHIFTEQUAL      = r'<<='
    t_RSHIFTEQUAL      = r'>>='
    t_ANDEQUAL         = r'&='
    t_OREQUAL          = r'\|='
    t_XOREQUAL         = r'^='

    # Increment/decrement
    t_PLUSPLUS         = r'\+\+'
    t_MINUSMINUS       = r'--'

    # ->
    t_ARROW            = r'->'

    # ?
    t_TERNARY          = r'\?'

    # Delimeters
    t_LPAREN           = r'\('
    t_RPAREN           = r'\)'
    t_LBRACKET         = r'\['
    t_RBRACKET         = r'\]'
    t_LBRACE           = r'\{'
    t_RBRACE           = r'\}'
    t_COMMA            = r','
    t_DOT              = r'\.'
    t_SEMI             = r';'
    t_COLON            = r':'

    t_BOOL_CONSTANT = r'true|false'
    t_INT_CONSTANT = r'\d+([uU]|[lL]|[uU][lL]|[lL][uU])?'
    #t_UINT_CONSTANT = r''

    # possible candidate to match : '2.', '.2'
    exponent_part = r'([eE][-+]?[0-9]+)'
    fractional_constant = r'((\d+)(\.\d*) | (\d*)(\.\d+))'
    t_FLOAT_CONSTANT = '(((('+fractional_constant+')'+exponent_part+'?)|([0-9]+'+exponent_part+'))[FfLl]?)'

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
