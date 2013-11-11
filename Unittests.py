import unittest

from ShaderParser import ShaderParser

class TestPreprocessor(unittest.TestCase):

    def test_empty_shader(self):
        sp = ShaderParser()
        sp.parse('')
        self.assertEqual(sp.version, 100)

    def test_version_300(self):
        sp = ShaderParser()
        sp.parse('  \t #version 300  es')
        self.assertEqual(sp.version, 300)

    def test_gl_es(self):
        # GL_ES is a predefined macro
        sp = ShaderParser()
        sp.parse('''  \t #version 300  es
        #ifndef GL_ES
        uniform lowp sampler2D texture_unit0;
        #endif
        #ifdef GL_ES
        varying samplerCube texture_unit0;
        #endif
        ''')
        self.assertEqual(sp.version, 300)
        self.assertEqual(len(sp.input_variables), 1)
        self.assertEqual(len(sp.output_variables), 0)

        self.assertTrue('texture_unit0' in sp.input_variables)
        self.assertEqual(sp.input_variables['texture_unit0'].type, 'samplerCube')
        self.assertEqual(sp.input_variables['texture_unit0'].layout_qualifier, 'varying')
        self.assertEqual(sp.input_variables['texture_unit0'].precision_qualifier, 'lowp')

class TestShaderVariables(unittest.TestCase):

    def test_varying(self):
        sp = ShaderParser(debug=False)
        sp.parse('\tvarying  ivec2 vTexCoord ;  ', debug=False)
        self.assertEqual(sp.version, 100)
        self.assertEqual(len(sp.input_variables), 1)
        self.assertEqual(len(sp.output_variables), 0)

        self.assertTrue('vTexCoord' in sp.input_variables)
        self.assertEqual(sp.input_variables['vTexCoord'].name, 'vTexCoord')
        self.assertEqual(sp.input_variables['vTexCoord'].type, 'ivec2')
        self.assertEqual(sp.input_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.input_variables['vTexCoord'].precision_qualifier, 'mediump')

    def test_io_variables(self):
        sp = ShaderParser()
        sp.parse('''
        attribute vec3 fresnet;
        uniform float time;
        varying  ivec2 vTexCoord ;
        ''', fragment_shader=False)
        self.assertEqual(sp.version, 100)
        self.assertEqual(len(sp.input_variables), 1)
        self.assertEqual(len(sp.output_variables), 1)

        self.assertTrue('fresnet' in sp.input_variables)
        self.assertEqual(sp.input_variables['fresnet'].type, 'vec3')
        self.assertEqual(sp.input_variables['fresnet'].layout_qualifier, 'attribute')
        self.assertEqual(sp.input_variables['fresnet'].precision_qualifier, 'highp')

        self.assertTrue('vTexCoord' in sp.output_variables)
        self.assertEqual(sp.output_variables['vTexCoord'].type, 'ivec2')
        self.assertEqual(sp.output_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.output_variables['vTexCoord'].precision_qualifier, 'highp')

        self.assertTrue('time' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['time'].type, 'float')
        self.assertEqual(sp.uniform_variables['time'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['time'].precision_qualifier, 'highp')

    def test_precision(self):
        sp = ShaderParser()
        sp.parse('''
        attribute lowp vec3 fresnet;
        uniform highp float time;
        varying highp vec2 vTexCoord ;
        ''', fragment_shader=False)
        self.assertEqual(sp.version, 100)
        self.assertEqual(len(sp.input_variables), 1)
        self.assertEqual(len(sp.output_variables), 1)

        self.assertTrue('fresnet' in sp.input_variables)
        self.assertEqual(sp.input_variables['fresnet'].type, 'vec3')
        self.assertEqual(sp.input_variables['fresnet'].layout_qualifier, 'attribute')
        self.assertEqual(sp.input_variables['fresnet'].precision_qualifier, 'lowp')

        self.assertTrue('vTexCoord' in sp.output_variables)
        self.assertEqual(sp.output_variables['vTexCoord'].type, 'vec2')
        self.assertEqual(sp.output_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.output_variables['vTexCoord'].precision_qualifier, 'highp')

        self.assertTrue('time' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['time'].type, 'float')
        self.assertEqual(sp.uniform_variables['time'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['time'].precision_qualifier, 'highp')

        self.assertEqual(sp.get_default_precision_qualifier('int'), 'highp')
        self.assertEqual(sp.get_default_precision_qualifier('float'), 'highp')
        self.assertEqual(sp.get_default_precision_qualifier('sampler2D'), 'lowp')
        self.assertEqual(sp.get_default_precision_qualifier('samplerCube'), 'lowp')
        self.assertEqual(sp.get_default_precision_qualifier('sampler2DArray'), None)

    def test_default_precision(self):
        sp = ShaderParser()
        sp.parse('''
        uniform sampler2D time;
        varying uvec2 vTexCoord ;
        ''', fragment_shader=True)
        self.assertEqual(sp.version, 100)

        self.assertTrue('vTexCoord' in sp.input_variables)
        self.assertEqual(sp.input_variables['vTexCoord'].type, 'uvec2')
        self.assertEqual(sp.input_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.input_variables['vTexCoord'].precision_qualifier, 'mediump')

        self.assertTrue('time' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['time'].type, 'sampler2D')
        self.assertEqual(sp.uniform_variables['time'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['time'].precision_qualifier, 'lowp')

        sp = ShaderParser()
        sp.parse('''#version 300 es
        precision mediump samplerCube;
        uniform samplerCube time;
        in uvec2 vTexCoord ;
        precision highp samplerCube;
        out samplerCube space;
        ''', fragment_shader=True)
        self.assertEqual(sp.version, 300)

        self.assertTrue('vTexCoord' in sp.input_variables)
        self.assertEqual(sp.input_variables['vTexCoord'].type, 'uvec2')
        self.assertEqual(sp.input_variables['vTexCoord'].layout_qualifier, 'in')
        self.assertEqual(sp.input_variables['vTexCoord'].precision_qualifier, 'mediump')

        self.assertTrue('time' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['time'].type, 'samplerCube')
        self.assertEqual(sp.uniform_variables['time'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['time'].precision_qualifier, 'mediump')

        self.assertTrue('space' in sp.output_variables)
        self.assertEqual(sp.output_variables['space'].type, 'samplerCube')
        self.assertEqual(sp.output_variables['space'].layout_qualifier, 'out')
        self.assertEqual(sp.output_variables['space'].precision_qualifier, 'highp')

class TestFunctionDefinition(unittest.TestCase):

    def test_empty_function_definition(self):
        sp = ShaderParser()
        sp.parse('''
        attribute vec3 vertex;
        void main() {}
        ''', fragment_shader=False)
        self.assertEqual(sp.version, 100)

        self.assertTrue('vertex' in sp.input_variables)
        self.assertEqual(sp.input_variables['vertex'].type, 'vec3')
        self.assertEqual(sp.input_variables['vertex'].layout_qualifier, 'attribute')
        self.assertEqual(sp.input_variables['vertex'].precision_qualifier, 'highp')

        self.assertEqual(len(sp.function_definitions), 1)
        self.assertTrue('main' in sp.function_definitions)
        self.assertEqual(sp.function_definitions['main'].return_type, 'void')
        self.assertEqual(sp.function_definitions['main'].parameters, [])
        self.assertEqual(sp.function_definitions['main'].statements, [])

    def test_function_definition(self):
        sp = ShaderParser()
        sp.parse('''
        attribute vec3 vertex;
        uniform mat4 mvp;
        void main()
        {
            gl_Position = 2 * mvp * vertex;
        }
        ''', fragment_shader=False)
        self.assertEqual(sp.version, 100)

        self.assertTrue('vertex' in sp.input_variables)
        self.assertEqual(sp.input_variables['vertex'].type, 'vec3')
        self.assertEqual(sp.input_variables['vertex'].layout_qualifier, 'attribute')
        self.assertEqual(sp.input_variables['vertex'].precision_qualifier, 'highp')

        self.assertTrue('mvp' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['mvp'].type, 'mat4')
        self.assertEqual(sp.uniform_variables['mvp'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['mvp'].precision_qualifier, 'highp')

        self.assertEqual(len(sp.function_definitions), 1)
        self.assertTrue('main' in sp.function_definitions)
        self.assertEqual(sp.function_definitions['main'].return_type, 'void')
        self.assertEqual(sp.function_definitions['main'].parameters, [])
        self.assertEqual(len(sp.function_definitions['main'].statements), 1)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
