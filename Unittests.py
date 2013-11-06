import unittest

from ShaderParser import ShaderParser, ShaderParserException

class TestPreprocessor(unittest.TestCase):

    def test_empty_shader(self):
        sp = ShaderParser()
        sp.parse('')
        self.assertEqual(sp.version, 100)

    def test_version_300(self):
        sp = ShaderParser()
        sp.parse('  \t #version 300  es')
        self.assertEqual(sp.version, 300)

class TestShaderVariables(unittest.TestCase):

    def test_varying(self):
        sp = ShaderParser()
        sp.parse('\tvarying  vec2 vTexCoord ;  ')
        self.assertEqual(sp.version, 100)
        self.assertEqual(len(sp.input_variables), 1)
        self.assertEqual(len(sp.output_variables), 0)

        self.assertTrue('vTexCoord' in sp.input_variables)
        self.assertEqual(sp.input_variables['vTexCoord'].name, 'vTexCoord')
        self.assertEqual(sp.input_variables['vTexCoord'].type, 'vec2')
        self.assertEqual(sp.input_variables['vTexCoord'].layout_qualifier, 'varying')

    def test_io_variables(self):
        sp = ShaderParser()
        sp.parse('''#version 300 es
        attribute vec3 fresnet;
        uniform float time;
        varying  vec2 vTexCoord ;
        ''', fragment_shader=False)
        self.assertEqual(sp.version, 300)
        self.assertEqual(len(sp.input_variables), 1)
        self.assertEqual(len(sp.output_variables), 1)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
