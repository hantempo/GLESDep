import unittest

from ShaderPreprocessor import ShaderPreprocessor, ShaderPreprocessorException
from ShaderParser import ShaderParser, ShaderParserException

class TestPreprocessor(unittest.TestCase):

    def test_empty_shader(self):
        spp = ShaderPreprocessor()
        spp.preprocess('')
        self.assertEqual(spp.version, 100)
        self.assertEqual(spp.output, '')

    def test_version_300(self):
        spp = ShaderPreprocessor()
        spp.preprocess('  \t #version 300')
        self.assertEqual(spp.version, 300)
        self.assertEqual(spp.output, '')

    def test_redefine_predefined(self):
        raw_shader = '''  \t #version 300
            #define GL_ANYTHING
        '''
        spp = ShaderPreprocessor()
        self.assertRaises(ShaderPreprocessorException, spp.preprocess, raw_shader)

        raw_shader = '''#undef POO__
        '''
        self.assertRaises(ShaderPreprocessorException, spp.preprocess, raw_shader)

class TestShaderVariables(unittest.TestCase):

    def test_varying(self):
        sp = ShaderParser()
        sp.parse('\tvarying  vec2 vTexCoord ;  ')
        self.assertEqual(sp.version, 100)
        self.assertEqual(len(sp.uniforms), 0)
        self.assertEqual(len(sp.attributes), 0)
        self.assertEqual(len(sp.varyings), 1)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
