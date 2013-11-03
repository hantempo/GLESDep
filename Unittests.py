import unittest

from ShaderPreprocessor import ShaderPreprocessor, ShaderPreprocessorException

class TestPreprocessor(unittest.TestCase):

    def test_empty_shader(self):
        shader = ''
        spp = ShaderPreprocessor()
        spp.preprocess(shader)
        self.assertEqual(spp.shader, '')
        self.assertEqual(spp.__VERSION__, 100)
        self.assertTrue('GL_ES' in spp.defined)

    def test_version_300(self):
        raw_shader = '  \t #version 300'
        processed_shader = ''
        spp = ShaderPreprocessor()
        self.assertTrue(spp.preprocess(raw_shader))
        self.assertEqual(spp.shader, processed_shader)
        self.assertEqual(spp.__VERSION__, 300)
        self.assertTrue('GL_ES' in spp.defined)

    def test_redefine_predefined(self):
        raw_shader = '''  \t #version 300
            #define GL_ANYTHING
        '''
        spp = ShaderPreprocessor()
        self.assertRaises(ShaderPreprocessorException, spp.preprocess, raw_shader)

        raw_shader = '''#undef POO__ 1
        '''
        spp = ShaderPreprocessor()
        self.assertRaises(ShaderPreprocessorException, spp.preprocess, raw_shader)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
