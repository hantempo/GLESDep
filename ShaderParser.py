import logging
logger = logging.getLogger(__name__)

import ply.yacc as yacc

from ShaderPreprocessor import tokens, t_WHITESPACE, t_NUMBER, t_STRING, t_COMMENT, t_error
from ShaderPreprocessor import ShaderPreprocessor

keywords = {
    'varying'       : 'VARYING',
    'uniform'       : 'UNIFORM',
    'attribute'     : 'ATTRIBUTE',
}
tokens += keywords.values()

tokens += ['SEMICOLON']

t_SEMICOLON = r';'

def t_IDENTIFIER(t):
    r'[A-Za-z_][\w_]*'
    t.type = keywords.get(t.value, 'IDENTIFIER')
    return t

def p_varying_declaration(p):
    'varying_declaration : VARYING IDENTIFIER IDENTIFIER SEMICOLON'
    print p

def p_error(p):
    print "Syntax error in input!"

#lexer = lex.lex()
parser = yacc.yacc()

class ShaderParserException(Exception):
    def __init__(self, linenum, msg):
        self.linenum = linenum
        self.message = msg

    def __repr__(self):
        return 'Shader Parser Exception [Line No.{0}] : {1}'.format(self.linenum, self.message)

class ShaderParser(object):

    def __init__(self):
        self.uniforms = {}
        self.varyings = {}
        self.attributes = {}

    def parse(self, input, filename=''):
        self.filename = filename

        # pre-process firstly
        spp = ShaderPreprocessor()
        spp.preprocess(input, filename)
        self.version = spp.version

        parser.parse(spp.output)
