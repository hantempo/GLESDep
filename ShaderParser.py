import logging
logger = logging.getLogger(__name__)

import collections
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

class VariableDeclaration(object):

    def __init__(self, name, type_specifier=None, type_qualifier=None, layout_qualifier=None, precision_qualifier=None):
        self.name = name
        self.type_specifier = type_specifier
        self.type_qualifier = type_qualifier
        self.layout_qualifier = layout_qualifier
        self.precision_qualifier = precision_qualifier
        self.initializer = None

    def __repr__(self):
        tokens = []
        if self.type_qualifier: tokens.append(self.type_qualifier)
        if self.layout_qualifier: tokens.append(self.layout_qualifier)
        if self.precision_qualifier: tokens.append(self.precision_qualifier)
        if self.type_specifier: tokens.append(self.type_specifier)
        tokens.append(self.name)
        if self.initializer:
            tokens.append('=')
            tokens.append(str(self.initializer))
        return ' '.join(tokens)

    def is_input_variable(self, fragment_shader):
        if not self.layout_qualifier:
            return False
        if fragment_shader:
            return self.layout_qualifier in ('varying', 'in')
        else:
            return self.layout_qualifier in ('attribute', 'in')

    def is_output_variable(self, fragment_shader):
        if not self.layout_qualifier:
            return False
        if fragment_shader:
            return self.layout_qualifier in ('out')
        else:
            return self.layout_qualifier in ('varying', 'out')

class ParameterDeclaration(object):

    def __init__(self, type, name=None, parameter_qualifier='in'):
        self.type = type
        self.name = name
        self.parameter_qualifier = parameter_qualifier

    def __repr__(self):
        tokens = [self.parameter_qualifier, self.type]
        if self.name: tokens.append(self.name)
        return ' '.join(tokens)

class FunctionPrototype(object):

    def __init__(self, name, return_type, parameters=[]):
        self.name = name
        self.return_type = return_type
        self.parameters = parameters

    def __repr__(self):
        return '%s %s(%s)' % (self.return_type, self.name, ', '.join(map(lambda k:str(k), self.parameters)))

class FunctionDefinition(object):

    def __init__(self, function_prototype, compound_statements):
        self.function_prototype = function_prototype
        self.compound_statements = compound_statements

    @property
    def name(self):
        return self.function_prototype.name

    @property
    def return_type(self):
        return self.function_prototype.return_type

    @property
    def parameters(self):
        return self.function_prototype.parameters

    def __repr__(self):
        return '\n'.join([str(self.function_prototype), str(self.compound_statements)])

class FunctionCall(object):

    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

    def __repr__(self):
        return '%s(%s)' % (self.name, ', '.join(map(lambda a:str(a), self.arguments)))

class BinaryExpression(object):

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        tokens = ['(%s)' % str(self.left) if isinstance(self.left, BinaryExpression) else str(self.left)]
        tokens.append(str(self.op))
        tokens.append('(%s)' % str(self.right) if isinstance(self.right, BinaryExpression) else str(self.right))
        return ' '.join(tokens)

class AssignmentExpression(object):

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        str = '%s %s %s;' % (self.left, self.op, self.right)
        return str

class IfStatement(object):

    def __init__(self, condition, if_true, if_false=None):
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    def __repr__(self):
        lines = ['if (%s)' % str(self.condition)]
        lines += str(self.if_true).splitlines()
        if self.if_false:
            lines += ['else']
            lines += str(self.if_false).splitlines()
        return '\n'.join(lines)

class DiscardStatement(object):

    def __repr__(self):
        return 'discard;'

class ReturnStatement(object):

    def __init__(self, return_value=None):
        self.return_value = return_value

    def __repr__(self):
        if self.return_value:
            return 'return %s;' % str(self.return_value)
        else:
            return 'return;'

class CompoundStatement(object):

    def __init__(self, block_items):
        self.block_items = []
        for item in block_items:
            if isinstance(item, list): # for declarations
                self.block_items += item
            else:
                self.block_items.append(item)

    def __getitem__(self, index):
        return self.block_items[index]

    def __len__(self):
        return len(self.block_items)

    def __repr__(self):
        lines = []
        lines.append('{')
        for item in self.block_items:
            if isinstance(item, VariableDeclaration):
                lines += ['    %s;' % str(item)]
            else:
                lines += map(lambda l : ' '*4+l, str(item).splitlines())
        lines.append('}')
        return '\n'.join(lines)

class ShaderParser(object):

    def __init__(self, debug=False):
        self.lexer = ShaderLexer.ShaderLexer()
        self.tokens = self.lexer.tokens

        rules_with_opt = [ 'block_item_list',
            'parameter_declaration_list',
        ]
        for rule in rules_with_opt:
            self._create_opt_rule(rule)

        self.parser = yacc.yacc(module=self,
            start='translation_unit_or_empty',
            debug=debug)

        self.version = 100
        self.variable_declarations = collections.OrderedDict()
        self.input_variables = collections.OrderedDict()
        self.output_variables = collections.OrderedDict()
        self.uniform_variables = collections.OrderedDict()

        self.default_precision_qualifier = {}

        self.function_definitions = collections.OrderedDict()

    def to_str(self):
        return '\n'.join(map(lambda var : str(var) + ';', self.variable_declarations.values()) +
            map(lambda d : str(d), self.function_definitions.values()))

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
        ''' postfix_expression : primary_expression LBRACKET expression RBRACKET
        '''
        p[0] = '%s[%s]' % (p[1], p[3])

    def p_postfix_expression3(self, p):
        ''' postfix_expression : postfix_expression DOT IDENTIFIER
        '''
        if isinstance(p[1], BinaryExpression):
            p[0] = '(%s).%s' % (str(p[1]), p[3])
        else:
            p[0] = '.'.join([p[1], p[3]])

    def p_postfix_expression4(self, p):
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
                              | binary_expression LT binary_expression
                              | binary_expression LE binary_expression
                              | binary_expression GT binary_expression
                              | binary_expression GE binary_expression
                              | binary_expression EQ binary_expression
                              | binary_expression NE binary_expression
                              | binary_expression OR binary_expression
                              | binary_expression AND binary_expression
                              | binary_expression XOR binary_expression
                              | binary_expression LOR binary_expression
                              | binary_expression LAND binary_expression
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

    def p_selection_statement1(self, p):
        ''' selection_statement : IF LPAREN expression RPAREN statement
        '''
        p[0] = IfStatement(p[3], p[5])

    def p_selection_statement2(self, p):
        ''' selection_statement : IF LPAREN expression RPAREN statement ELSE statement
        '''
        p[0] = IfStatement(p[3], p[5], p[7])

    def p_jump_statement1(self, p):
        ''' jump_statement : DISCARD SEMI
        '''
        p[0] = DiscardStatement()

    def p_jump_statement2(self, p):
        ''' jump_statement : RETURN expression_statement
                           | RETURN SEMI
        '''
        if p[2] == ';':
            p[0] = ReturnStatement()
        else:
            p[0] = ReturnStatement(p[2])

    def p_expression_statement(self, p):
        ''' expression_statement : expression SEMI
        '''
        p[0] = p[1]

    def p_statement(self, p):
        ''' statement : expression_statement
                      | selection_statement
                      | compound_statement
                      | jump_statement
        '''
        p[0] = p[1]

    def p_block_item(self, p):
        ''' block_item : statement
                       | declaration
        '''
        p[0] = p[1]

    def p_block_item_list(self, p):
        ''' block_item_list : block_item
                            | block_item_list block_item
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_compound_statement(self, p):
        ''' compound_statement : LBRACE block_item_list_opt RBRACE
        '''
        p[0] = CompoundStatement(p[2])

    def p_parameter_declaration1(self, p):
        ''' parameter_declaration : type_specifier
        '''
        if p[1] != 'void':
            p[0] = ParameterDeclaration(type=p[1])

    def p_parameter_declaration2(self, p):
        ''' parameter_declaration : type_specifier IDENTIFIER
        '''
        p[0] = ParameterDeclaration(type=p[1], name=p[2])

    def p_parameter_declaration3(self, p):
        ''' parameter_declaration : parameter_qualifier type_specifier IDENTIFIER
        '''
        p[0] = ParameterDeclaration(type=p[2], name=p[3], parameter_qualifier=p[1])

    def p_parameter_declaration_list(self, p):
        ''' parameter_declaration_list : parameter_declaration
                                       | parameter_declaration_list COMMA parameter_declaration
        '''
        if len(p) == 2:
            p[0] = [p[1]] if p[1] else []
        else:
            p[0] = p[1] + [p[3]] if p[3] else p[1]

    def p_function_prototype(self, p):
        ''' function_prototype : type_specifier IDENTIFIER LPAREN parameter_declaration_list_opt RPAREN
        '''
        p[0] = FunctionPrototype(name=p[2], return_type=p[1], parameters=p[4])

    def p_function_definition(self, p):
        ''' function_definition : function_prototype compound_statement
        '''
        p[0] = FunctionDefinition(function_prototype=p[1], compound_statements=p[2])

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

    def p_declaration_body1(self, p):
        ''' declaration_body : PRECISION precision_qualifier type_specifier
        '''
        p[0] = PrecisionStatement(precision_qualifier=p[2], type_specifier=p[3])

    def p_declaration_body2(self, p):
        ''' declaration_body : type_specifier init_declarator_list
        '''
        for dec in p[2]:
            dec.type_specifier = p[1]
        p[0] = p[2]

    def p_declaration_body3(self, p):
        ''' declaration_body : layout_qualifier type_specifier init_declarator_list
        '''
        for dec in p[3]:
            dec.layout_qualifier = p[1]
            dec.type_specifier = p[2]
        p[0] = p[3]

    def p_declaration_body4(self, p):
        ''' declaration_body : layout_qualifier precision_qualifier type_specifier init_declarator_list
        '''
        for dec in p[4]:
            dec.layout_qualifier = p[1]
            dec.precision_qualifier = p[2]
            dec.type_specifier = p[3]
        p[0] = p[4]

    def p_declaration_body5(self, p):
        ''' declaration_body : type_qualifier type_specifier init_declarator_list
        '''
        for dec in p[3]:
            dec.type_qualifier = p[1]
            dec.type_specifier = p[2]
        p[0] = p[3]

    def p_declaration_body6(self, p):
        ''' declaration_body : type_qualifier precision_qualifier type_specifier init_declarator_list
        '''
        for dec in p[4]:
            dec.type_qualifier = p[1]
            dec.precision_qualifier = p[2]
            dec.type_specifier = p[3]
        p[0] = p[4]

    def p_type_qualifier(self, p):
        ''' type_qualifier : CONST
        '''
        p[0] = p[1]

    def p_init_declarator_list(self, p):
        ''' init_declarator_list : init_declarator
                                 | init_declarator_list COMMA init_declarator
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_init_declarator(self, p):
        ''' init_declarator : declarator
                            | declarator EQUALS initializer
        '''
        if len(p) == 4:
            p[1].initializer = p[3]
        p[0] = p[1]

    def p_initializer(self, p):
        ''' initializer : assignment_expression
        '''
        p[0] = p[1]

    def p_declarator(self, p):
        ''' declarator : direct_declarator
        '''
        p[0] = p[1]

    def p_direct_declarator1(self, p):
        ''' direct_declarator : IDENTIFIER
        '''
        p[0] = VariableDeclaration(name=p[1])

    def p_direct_declarator2(self, p):
        ''' direct_declarator : direct_declarator LBRACKET assignment_expression RBRACKET
        '''
        p[1].name += '[%s]' % p[3]
        p[0] = p[1]

    def p_layout_qualifier(self, p):
        ''' layout_qualifier : VARYING
                             | UNIFORM
                             | ATTRIBUTE
                             | IN
                             | OUT
        '''
        p[0] = p[1]

    def p_parameter_qualifier(self, p):
        ''' parameter_qualifier : IN
                                | OUT
                                | INOUT
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
        p[0] = []

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

        external_declarations = self.parser.parse(input=text,
            lexer=self.lexer,
            debug=1 if debug else 0)
        for decal in external_declarations:
            if isinstance(decal, PrecisionStatement):
                self.set_default_precision_qualifier(decal.type_specifier, decal.precision_qualifier)
            elif isinstance(decal, FunctionDefinition):
                self.function_definitions[decal.name] = decal
            elif isinstance(decal, list): # variable declaration come as a list
                for var in decal:
                    if isinstance(var, VariableDeclaration):
                        # use default precision qualifier if equals None
                        if not var.precision_qualifier:
                            var.precision_qualifier = self.get_default_precision_qualifier(var.type_specifier)
                            if var.precision_qualifier == None:
                                logger.error('Unexpected non-precision-qualified variable: "%s"' % str(var))

                        if var.is_input_variable(fragment_shader):
                            self.input_variables[var.name] = var
                        elif var.is_output_variable(fragment_shader):
                            self.output_variables[var.name] = var
                        elif var.layout_qualifier == 'uniform':
                            self.uniform_variables[var.name] = var
                        self.variable_declarations[var.name] = var

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

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vertex', action='store_true',
            help='Specify this shader is a vertex shader')
    parser.add_argument('input_shader')

    args = parser.parse_args()

    with open(args.input_shader) as f:
        sp = ShaderParser()
        sp.parse(f.read(), fragment_shader=not args.vertex)
        print sp.to_str()
