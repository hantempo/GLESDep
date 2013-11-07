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
        sp = ShaderParser()
        sp.parse('\tvarying  ivec2 vTexCoord ;  ')
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

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
