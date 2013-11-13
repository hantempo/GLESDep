import logging
logger = logging.getLogger(__name__)

from subprocess import Popen, PIPE
from ply import yacc

import ShaderLexer

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
        if self.layout_qualifier:
            return '%s %s %s %s' % (
                self.layout_qualifier, self.precision_qualifier,
                self.type, self.name)
        else:
            return '%s %s %s' % (
                self.precision_qualifier,
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

#class Assignment(object):

    #def __init__(self, operator, lvalue, rvalue):
        #self.operator = operator
        #self.lvalue = lvalue
        #self.rvalue = rvalue

class FunctionPrototype(object):

    def __init__(self, name, return_type, parameters=[]):
        self.name = name
        self.return_type = return_type
        self.parameters = parameters

class FunctionDefinition(object):

    def __init__(self, function_prototype, statements):
        self.function_prototype = function_prototype
        self.statements = statements if statements else []

    @property
    def name(self):
        return self.function_prototype.name

    @property
    def return_type(self):
        return self.function_prototype.return_type

    @property
    def parameters(self):
        return self.function_prototype.parameters

class FunctionCall(object):

    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

    def __repr__(self):
        return '%s(%s)' % (self.name, ', '.join(self.arguments))

class BinaryExpression(object):

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return '(%s %s %s)' % (self.left, self.op, self.right)

class AssignmentExpression(object):

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return '%s %s %s' % (self.left, self.op, self.right)

class ShaderParser(object):

    def __init__(self, debug=False):
        self.lexer = ShaderLexer.ShaderLexer()
        self.tokens = self.lexer.tokens

        rules_with_opt = [
            'statement_list',
        ]
        for rule in rules_with_opt:
            self._create_opt_rule(rule)

        self.parser = yacc.yacc(module=self,
            start='translation_unit_or_empty',
            debug=debug)

        self.version = 100
        self.input_variables = {}
        self.output_variables = {}
        self.uniform_variables = {}

        self.default_precision_qualifier = {}

        self.function_definitions = {}

    def _create_opt_rule(self, rulename):
        """ Given a rule name, creates an optional ply.yacc rule
            for it. The name of the optional rule is
            <rulename>_opt
        """
        optname = rulename + '_opt'

        def optrule(self, p):
            p[0] = p[1]

        optrule.__doc__ = '%s : empty\n| %s' % (optname, rulename)
        optrule.__name__ = 'p_%s' % optname
        setattr(self.__class__, optrule.__name__, optrule)

    precedence = (
        ('right', 'EQUALS'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
    )

    def p_primary_expression(self, p):
        ''' primary_expression : IDENTIFIER
                               | INT_CONSTANT
                               | FLOAT_CONSTANT
                               | BOOL_CONSTANT
                               | LPAREN expression RPAREN
                               | type_specifier
        '''
        p[0] = p[1] if len(p) == 2 else p[2]

    def p_argument_expression_list(self, p):
        ''' argument_expression_list : assignment_expression
                                     | argument_expression_list COMMA assignment_expression
        '''
        p[0] = [p[1]] if len(p) == 2 else (p[1] + [p[3]])

    def p_postfix_expression1(self, p):
        ''' postfix_expression : primary_expression
        '''
        p[0] = p[1]

    def p_postfix_expression2(self, p):
        ''' postfix_expression : postfix_expression DOT IDENTIFIER
        '''
        p[0] = '.'.join([p[1], p[3]])

    def p_postfix_expression3(self, p):
        ''' postfix_expression : postfix_expression LPAREN argument_expression_list RPAREN
        '''
        p[0] = FunctionCall(name=p[1], arguments=p[3])

    def p_unary_expression1(self, p):
        ''' unary_expression : postfix_expression
        '''
        p[0] = p[1]

    def p_unary_expression2(self, p):
        ''' unary_expression : unary_operator unary_expression
        '''
        p[0] = p[1] + p[2]

    def p_unary_operator(self, p):
        ''' unary_operator : AND
                           | TIMES
                           | PLUS
                           | MINUS
                           | NOT
                           | LNOT
        '''
        p[0] = p[1]

    def p_binary_expression(self, p):
        ''' binary_expression : unary_expression
                              | binary_expression PLUS binary_expression
                              | binary_expression MINUS binary_expression
                              | binary_expression TIMES binary_expression
                              | binary_expression DIVIDE binary_expression
        '''
        p[0] = p[1] if len(p) == 2 else BinaryExpression(p[2], p[1], p[3])

    def p_assignment_expression(self, p):
        ''' assignment_expression : binary_expression
                                  | unary_expression assignment_operator assignment_expression
        '''
        p[0] = p[1] if len(p) == 2 else AssignmentExpression(p[2], p[1], p[3])

    def p_expression(self, p):
        ''' expression : assignment_expression
        '''
        p[0] = p[1]

    def p_statement(self, p):
        ''' statement : expression SEMI
        '''
        p[0] = p[1]

    def p_statement_list(self, p):
        ''' statement_list : statement
                           | statement_list statement
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_compound_statement(self, p):
        ''' compound_statement : LBRACE statement_list_opt RBRACE
        '''
        p[0] = p[2]

    def p_function_prototype(self, p):
        ''' function_prototype : type_specifier IDENTIFIER LPAREN RPAREN
        '''
        p[0] = FunctionPrototype(name=p[2], return_type=p[1])

    def p_function_definition(self, p):
        ''' function_definition : function_prototype compound_statement
        '''
        p[0] = FunctionDefinition(function_prototype=p[1], statements=p[2])

    def p_external_declaration(self, p):
        ''' external_declaration : function_definition
                                 | declaration
        '''
        p[0] = p[1]

    def p_translation_unit(self, p):
        ''' translation_unit : external_declaration
                             | translation_unit external_declaration
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_translation_unit_or_empty(self, p):
        ''' translation_unit_or_empty : translation_unit
                                      | empty
        '''
        if p[1] == None:
            p[0] = []
        else:
            p[0] = p[1]

    def p_declaration(self, p):
        ''' declaration : declaration_body SEMI
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

    def p_assignment_operator(self, p):
        ''' assignment_operator : EQUALS
                                | TIMESEQUAL
                                | DIVEQUAL
                                | MODEQUAL
                                | PLUSEQUAL
                                | MINUSEQUAL
                                | LSHIFTEQUAL
                                | RSHIFTEQUAL
                                | ANDEQUAL
                                | XOREQUAL
                                | OREQUAL
        '''
        p[0] = p[1]

    def p_empty(self, p):
        ''' empty : '''
        p[0] = None

    def p_error(self, p):
        logger.error('Parser error in line #%d before token %s' % (p.lineno, p.value))

    def parse(self, text, fragment_shader=True, filename='', debug=False):
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
            debug=1 if debug else 0)
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
            elif isinstance(decal, FunctionDefinition):
                self.function_definitions[decal.name] = decal

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
