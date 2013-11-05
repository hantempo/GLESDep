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
        self.assertEqual(len(sp.uniforms), 0)
        self.assertEqual(len(sp.attributes), 0)
        self.assertEqual(len(sp.varyings), 1)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
