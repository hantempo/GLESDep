import logging
logger = logging.getLogger(__name__)

import ply.lex as lex

from ShaderPreprocessor import tokens, t_WHITESPACE, t_NUMBER, t_STRING, t_COMMENT, t_error
from ShaderPreprocessor import ShaderPreprocessor

keywords = {
    'varying'       : 'VARYING',
    'uniform'       : 'UNIFORM',
    'attribute'     : 'ATTRIBUTE',
}
tokens += keywords.values()

def t_IDENTIFIER(t):
    r'[A-Za-z_][\w_]*'
    t.type = keywords.get(t.value, 'IDENTIFIER')
    return t

lexer = lex.lex()

class ShaderParserException(Exception):
    def __init__(self, linenum, msg):
        self.linenum = linenum
        self.message = msg

    def __repr__(self):
        return 'Shader Parser Exception [Line No.{0}] : {1}'.format(self.linenum, self.message)

class ShaderParser(object):

    def __init__(self):
        self.lexer = lexer

        self.uniforms = {}
        self.varyings = {}
        self.attributes = {}

    def parse(self, input, filename=''):
        self.filename = filename

        # pre-process firstly
        spp = ShaderPreprocessor()
        spp.preprocess(input, filename)
        self.version = spp.version
