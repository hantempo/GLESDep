import unittest

#from ShaderPreprocessor import ShaderPreprocessor, ShaderPreprocessorException
from ShaderParser import ShaderParser

class TestPreprocessor(unittest.TestCase):

    def test_empty_shader(self):
        sp = ShaderParser()
        sp.parse('')
        self.assertEqual(sp.version, 100)
        self.assertEqual(len(sp.uniforms), 0)

    def test_version_300(self):
        sp = ShaderParser()
        sp.parse('  \t #version 300')
        self.assertEqual(sp.version, 300)
        self.assertEqual(len(sp.uniforms), 0)

    #def test_redefine_predefined(self):
        #raw_shader = '''  \t #version 300
            ##define GL_ANYTHING
        #'''
        #spp = ShaderPreprocessor()
        #self.assertRaises(ShaderPreprocessorException, spp.preprocess, raw_shader)

        #raw_shader = '''#undef POO__ 1
        #'''
        #spp = ShaderPreprocessor()
        #self.assertRaises(ShaderPreprocessorException, spp.preprocess, raw_shader)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
