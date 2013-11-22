import unittest

from ShaderParser import ShaderParser, Preprocess

class TestPreprocessor(unittest.TestCase):

    def test_empty_shader(self):
        input = ''
        output, version = Preprocess(input)
        self.assertEqual(output, '')
        self.assertEqual(version, 100)

    def test_version_300(self):
        input = '  \t # version 300  es'
        output, version = Preprocess(input)
        self.assertEqual(output, '')
        self.assertEqual(version, 300)

    def test_gl_es(self):
        input = '''  \t #version 300  es
#ifndef GL_ES
        uniform lowp sampler2D texture_unit0;
#endif
#ifdef GL_ES
        varying samplerCube texture_unit0;
#endif
'''
        expected_output = '''




        varying samplerCube texture_unit0;'''
        output, version = Preprocess(input)
        self.assertEqual(output, expected_output)
        self.assertEqual(version, 300)

        # GL_ES is a predefined macro
        sp = ShaderParser()
        sp.parse(input)
        self.assertEqual(sp.version, 300)
        self.assertEqual(len(sp.input_variables), 1)
        self.assertEqual(len(sp.output_variables), 0)

        self.assertTrue('texture_unit0' in sp.input_variables)
        self.assertEqual(sp.input_variables['texture_unit0'].type_specifier, 'samplerCube')
        self.assertEqual(sp.input_variables['texture_unit0'].layout_qualifier, 'varying')
        self.assertEqual(sp.input_variables['texture_unit0'].precision_qualifier, 'lowp')

        self.assertEqual(sp.to_str(), 'varying lowp samplerCube texture_unit0;')

    def test_gl_es2(self):
        input = '''#version 300 es
#ifdef GL_ES
precision mediump float;
#endif
#ifndef GL_ES
#define highp
#define mediump
#define lowp
#endif
#define SHADOW_MAP
#define SOFT_SHADOW
#ifdef GL_ES
#if defined LIGHTING || defined REFLECTION || defined DEP_TEXTURING || defined TRANSITION_EFFECT
precision mediump float;
#else
precision lowp float;
#endif
#endif
#ifdef GL_ES
#if defined NEED_HIGHP
precision highp float;
#endif
#endif
in vec2 out_texcoord0;
out vec4 frag_color;

uniform lowp sampler2D texture_unit0;
uniform lowp vec3 color;

void main()
{
    vec4 texel = texture( texture_unit0, out_texcoord0) * vec4( color, 1.0);
    frag_color = vec4( texel.xyz, 0.0);
}'''
        expected_output = '''

precision mediump float;












precision lowp float;







in vec2 out_texcoord0;
out vec4 frag_color;

uniform lowp sampler2D texture_unit0;
uniform lowp vec3 color;

void main()
{
    vec4 texel = texture( texture_unit0, out_texcoord0) * vec4( color, 1.0);
    frag_color = vec4( texel.xyz, 0.0);
}'''
        output, version = Preprocess(input)
        self.assertEqual(output, expected_output)
        self.assertEqual(version, 300)

class TestShaderVariables(unittest.TestCase):

    def test_varying(self):
        sp = ShaderParser(debug=False)
        sp.parse('\tvarying  ivec2 vTexCoord ;  ', debug=False)
        self.assertEqual(sp.version, 100)
        self.assertEqual(len(sp.input_variables), 1)
        self.assertEqual(len(sp.output_variables), 0)

        self.assertTrue('vTexCoord' in sp.input_variables)
        self.assertEqual(sp.input_variables['vTexCoord'].name, 'vTexCoord')
        self.assertEqual(sp.input_variables['vTexCoord'].type_specifier, 'ivec2')
        self.assertEqual(sp.input_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.input_variables['vTexCoord'].precision_qualifier, 'mediump')

        self.assertEqual(sp.to_str(), 'varying mediump ivec2 vTexCoord;')

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
        self.assertEqual(sp.input_variables['fresnet'].type_specifier, 'vec3')
        self.assertEqual(sp.input_variables['fresnet'].layout_qualifier, 'attribute')
        self.assertEqual(sp.input_variables['fresnet'].precision_qualifier, 'highp')

        self.assertTrue('vTexCoord' in sp.output_variables)
        self.assertEqual(sp.output_variables['vTexCoord'].type_specifier, 'ivec2')
        self.assertEqual(sp.output_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.output_variables['vTexCoord'].precision_qualifier, 'highp')

        self.assertTrue('time' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['time'].type_specifier, 'float')
        self.assertEqual(sp.uniform_variables['time'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['time'].precision_qualifier, 'highp')

        self.assertEqual(sp.to_str(), 'attribute highp vec3 fresnet;\nuniform highp float time;\nvarying highp ivec2 vTexCoord;')

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
        self.assertEqual(sp.input_variables['fresnet'].type_specifier, 'vec3')
        self.assertEqual(sp.input_variables['fresnet'].layout_qualifier, 'attribute')
        self.assertEqual(sp.input_variables['fresnet'].precision_qualifier, 'lowp')

        self.assertTrue('vTexCoord' in sp.output_variables)
        self.assertEqual(sp.output_variables['vTexCoord'].type_specifier, 'vec2')
        self.assertEqual(sp.output_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.output_variables['vTexCoord'].precision_qualifier, 'highp')

        self.assertTrue('time' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['time'].type_specifier, 'float')
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
        self.assertEqual(sp.input_variables['vTexCoord'].type_specifier, 'uvec2')
        self.assertEqual(sp.input_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.input_variables['vTexCoord'].precision_qualifier, 'mediump')

        self.assertTrue('time' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['time'].type_specifier, 'sampler2D')
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
        self.assertEqual(sp.input_variables['vTexCoord'].type_specifier, 'uvec2')
        self.assertEqual(sp.input_variables['vTexCoord'].layout_qualifier, 'in')
        self.assertEqual(sp.input_variables['vTexCoord'].precision_qualifier, 'mediump')

        self.assertTrue('time' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['time'].type_specifier, 'samplerCube')
        self.assertEqual(sp.uniform_variables['time'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['time'].precision_qualifier, 'mediump')

        self.assertTrue('space' in sp.output_variables)
        self.assertEqual(sp.output_variables['space'].type_specifier, 'samplerCube')
        self.assertEqual(sp.output_variables['space'].layout_qualifier, 'out')
        self.assertEqual(sp.output_variables['space'].precision_qualifier, 'highp')

    def test_global_variable_def(self):
        sp = ShaderParser()
        sp.parse('''precision highp float;vec2 wave0 = vec2( 1.01, 1.08);vec2 wave2 = vec2( -1.03, 1.03 );''', debug=False)

        self.assertEqual(len(sp.input_variables), 0)
        self.assertEqual(len(sp.output_variables), 0)
        self.assertEqual(len(sp.uniform_variables), 0)
        self.assertEqual(len(sp.function_definitions), 0)

        self.assertEqual(sp.to_str(), 'highp vec2 wave0 = vec2(1.01, 1.08);\nhighp vec2 wave2 = vec2(-1.03, 1.03);')

    def test_array_variable_def(self):
        sp = ShaderParser()
        sp.parse('uniform vec4 bones[3*2];float matrix[4][4];', fragment_shader=False, debug=False)

        self.assertEqual(len(sp.input_variables), 0)
        self.assertEqual(len(sp.output_variables), 0)
        self.assertEqual(len(sp.uniform_variables), 1)
        self.assertEqual(len(sp.function_definitions), 0)

        self.assertEqual(sp.to_str(), 'uniform highp vec4 bones[3 * 2];\nhighp float matrix[4][4];')

    def test_const_variable_def(self):
        sp = ShaderParser()
        sp.parse('const mediump int n = 4;')

        self.assertEqual(len(sp.input_variables), 0)
        self.assertEqual(len(sp.output_variables), 0)
        self.assertEqual(len(sp.uniform_variables), 0)
        self.assertEqual(len(sp.function_definitions), 0)

        self.assertEqual(sp.to_str(), 'const mediump int n = 4;')

class TestFunction(unittest.TestCase):

    def test_empty_function_definition(self):
        sp = ShaderParser()
        sp.parse('''
        attribute vec3 vertex;
        void main() {}
        ''', fragment_shader=False)
        self.assertEqual(sp.version, 100)

        self.assertTrue('vertex' in sp.input_variables)
        self.assertEqual(sp.input_variables['vertex'].type_specifier, 'vec3')
        self.assertEqual(sp.input_variables['vertex'].layout_qualifier, 'attribute')
        self.assertEqual(sp.input_variables['vertex'].precision_qualifier, 'highp')

        self.assertEqual(len(sp.function_definitions), 1)
        self.assertTrue('main' in sp.function_definitions)
        self.assertEqual(sp.function_definitions['main'].return_type, 'void')
        self.assertEqual(sp.function_definitions['main'].parameters, [])
        self.assertEqual(str(sp.function_definitions['main'].compound_statements), '{\n}')

        self.assertEqual(sp.to_str(), 'attribute highp vec3 vertex;\nvoid main()\n{\n}')

    def test_function_definition1(self):
        sp = ShaderParser()
        sp.parse('''
        attribute vec3 vertex;
        uniform mat4 mvp;
        void main()
        {
            gl_Position = 2 + mvp * vertex;
            gl_Position = (2 + mvp) * vertex;
        }
        ''', fragment_shader=False, debug=False)
        self.assertEqual(sp.version, 100)

        self.assertTrue('vertex' in sp.input_variables)
        self.assertEqual(sp.input_variables['vertex'].type_specifier, 'vec3')
        self.assertEqual(sp.input_variables['vertex'].layout_qualifier, 'attribute')
        self.assertEqual(sp.input_variables['vertex'].precision_qualifier, 'highp')

        self.assertTrue('mvp' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['mvp'].type_specifier, 'mat4')
        self.assertEqual(sp.uniform_variables['mvp'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['mvp'].precision_qualifier, 'highp')

        self.assertEqual(len(sp.function_definitions), 1)
        self.assertTrue('main' in sp.function_definitions)
        self.assertEqual(sp.function_definitions['main'].return_type, 'void')
        self.assertEqual(sp.function_definitions['main'].parameters, [])

        self.assertEqual(str(sp.function_definitions['main'].compound_statements),
                '{\n    gl_Position = 2 + (mvp * vertex);\n    gl_Position = (2 + mvp) * vertex;\n}')

    def test_function_definition2(self):
        sp = ShaderParser()
        sp.parse('''
#ifdef GL_ES
        precision mediump float;
#endif
        uniform sampler2D texChars;
        varying vec2 vTexCoord;
        void main(void)
        {
            gl_FragColor = texture2D(texChars, vTexCoord);
        }
        ''', fragment_shader=True, debug=False)
        self.assertEqual(sp.version, 100)

        self.assertEqual(len(sp.input_variables), 1)
        self.assertTrue('vTexCoord' in sp.input_variables)
        self.assertEqual(sp.input_variables['vTexCoord'].type_specifier, 'vec2')
        self.assertEqual(sp.input_variables['vTexCoord'].layout_qualifier, 'varying')
        self.assertEqual(sp.input_variables['vTexCoord'].precision_qualifier, 'mediump')

        self.assertEqual(len(sp.uniform_variables), 1)
        self.assertTrue('texChars' in sp.uniform_variables)
        self.assertEqual(sp.uniform_variables['texChars'].type_specifier, 'sampler2D')
        self.assertEqual(sp.uniform_variables['texChars'].layout_qualifier, 'uniform')
        self.assertEqual(sp.uniform_variables['texChars'].precision_qualifier, 'lowp')

        self.assertEqual(len(sp.function_definitions), 1)
        self.assertTrue('main' in sp.function_definitions)
        fun_def = sp.function_definitions['main']
        self.assertEqual(fun_def.return_type, 'void')
        self.assertEqual(len(fun_def.parameters), 0)

        self.assertEqual(str(fun_def.compound_statements), '{\n    gl_FragColor = texture2D(texChars, vTexCoord);\n}')

        self.assertEqual(str(fun_def), 'void main()\n{\n    gl_FragColor = texture2D(texChars, vTexCoord);\n}')

    def test_function_definition3(self):
        sp = ShaderParser()
        sp.parse('''
#ifdef GL_ES
        precision highp float;
#endif
        attribute vec4 myVertex;
        varying vec2 vTexCoord;
        void main(float v, int k)
        {
            gl_Position = vec4( -myVertex.y, myVertex.x, 0.,.2);
            vTexCoord = vec2(myVertex.zw);
        }
        ''', fragment_shader=False, debug=False)
        self.assertEqual(sp.version, 100)

        self.assertEqual(len(sp.input_variables), 1)
        self.assertTrue('myVertex' in sp.input_variables)
        self.assertEqual(str(sp.input_variables['myVertex']), 'attribute highp vec4 myVertex')

        self.assertEqual(len(sp.output_variables), 1)
        self.assertTrue('vTexCoord' in sp.output_variables)
        self.assertEqual(str(sp.output_variables['vTexCoord']), 'varying highp vec2 vTexCoord')

        self.assertEqual(len(sp.function_definitions), 1)
        self.assertTrue('main' in sp.function_definitions)
        fun_def = sp.function_definitions['main']
        self.assertEqual(fun_def.return_type, 'void')
        self.assertEqual(len(fun_def.parameters), 2)
        self.assertEqual(str(fun_def.parameters[0]), 'in float v')
        self.assertEqual(str(fun_def.parameters[1]), 'in int k')
        self.assertEqual(str(fun_def.function_prototype), 'void main(in float v, in int k)')

        self.assertEqual(str(fun_def.compound_statements), '{\n    gl_Position = vec4(-myVertex.y, myVertex.x, 0., .2);\n    vTexCoord = vec2(myVertex.zw);\n}')

    def test_function_definition4(self):
        sp = ShaderParser()
        sp.parse('''
#ifdef GL_ES
        precision mediump float;
#endif
        varying vec2 texcoord0;
        uniform sampler2D tex0;
        uniform vec3 fragmentColorVP;
        void main(void)
        {
	        vec4 tex = texture2D(tex0, texcoord0);
	        if(tex.a < 0.5)
	        {
		        discard;
	        }
	        else
	        {
	        gl_FragColor = tex * vec4(fragmentColorVP, 1.0);
	        }

            if (tex.x == tex.y){if(tex.z==tex.w){}}
        }
        ''', fragment_shader=False, debug=False)
        self.assertEqual(len(sp.function_definitions), 1)
        self.assertTrue('main' in sp.function_definitions)
        fun_def = sp.function_definitions['main']

        self.assertEqual(str(fun_def.compound_statements[0]), 'vec4 tex = texture2D(tex0, texcoord0)')
        self.assertEqual(str(fun_def.compound_statements[1]), 'if (tex.a < 0.5)\n{\n    discard;\n}\nelse\n{\n    gl_FragColor = tex * vec4(fragmentColorVP, 1.0);\n}')
        self.assertEqual(str(fun_def), '''void main()
{
    vec4 tex = texture2D(tex0, texcoord0);
    if (tex.a < 0.5)
    {
        discard;
    }
    else
    {
        gl_FragColor = tex * vec4(fragmentColorVP, 1.0);
    }
    if (tex.x == tex.y)
    {
        if (tex.z == tex.w)
        {
        }
    }
}''')

    def test_parameter_qualifier(self):
        sp = ShaderParser()
        sp.parse('''
        void decodeFromByteVec3(inout vec3 myVec)
        {
            vec4 tmp;
            vec3 position;
        }
        ''', fragment_shader=False)

        self.assertEqual(len(sp.function_definitions), 1)
        self.assertTrue('decodeFromByteVec3' in sp.function_definitions)
        fun_def = sp.function_definitions['decodeFromByteVec3']
        self.assertEqual(len(fun_def.compound_statements), 2)

        self.assertEqual(str(fun_def), 'void decodeFromByteVec3(inout vec3 myVec)\n{\n    vec4 tmp;\n    vec3 position;\n}')

    def test_function_call_with_array(self):
        sp = ShaderParser()
        sp.parse('''
        void main()
        {
            mat4 M1 = mat4( BONE[I.y * 3 + 0],BONE[I.y * 3 + 1],BONE[I.y * 3 + 2],vec4( 0.0, 0.0, 0.0, 1.0));
            tangent = (vec4( tangent, 0.0) * M4).xyz;
            return;
        }''', fragment_shader=False)

        self.assertEqual(len(sp.function_definitions), 1)
        fun_def = sp.function_definitions['main']
        self.assertEqual(len(fun_def.compound_statements), 3)
        self.assertEqual(str(fun_def.compound_statements), """{
    mat4 M1 = mat4(BONE[(I.y * 3) + 0], BONE[(I.y * 3) + 1], BONE[(I.y * 3) + 2], vec4(0.0, 0.0, 0.0, 1.0));
    tangent = (vec4(tangent, 0.0) * M4).xyz;
    return;
}""")

    def test_function_with_return(self):
        sp = ShaderParser()
        sp.parse('vec3 calculate_normal( vec2 tc){return vec3(tc, 0.1);}', fragment_shader=False)

        self.assertEqual(len(sp.function_definitions), 1)
        fun_def = sp.function_definitions['calculate_normal']
        self.assertEqual(len(fun_def.compound_statements), 1)

        self.assertEqual(str(fun_def), 'vec3 calculate_normal(in vec2 tc)\n{\n    return vec3(tc, 0.1);\n}')

from GLESEnum import Enum

class TestTextures(unittest.TestCase):

    def test_pixel_store(self):
        from GLESContext import Context as GLES
        gles = GLES()

        # check the initial states
        self.assertEqual(gles.glGet(Enum.GL_PACK_ROW_LENGTH), 0)
        self.assertEqual(gles.glGet(Enum.GL_PACK_IMAGE_HEIGHT), 0)
        self.assertEqual(gles.glGet(Enum.GL_PACK_SKIP_PIXELS), 0)
        self.assertEqual(gles.glGet(Enum.GL_PACK_SKIP_ROWS), 0)
        self.assertEqual(gles.glGet(Enum.GL_PACK_SKIP_IMAGES), 0)
        self.assertEqual(gles.glGet(Enum.GL_PACK_ALIGNMENT), 4)
        self.assertEqual(gles.glGet(Enum.GL_UNPACK_ROW_LENGTH), 0)
        self.assertEqual(gles.glGet(Enum.GL_UNPACK_IMAGE_HEIGHT), 0)
        self.assertEqual(gles.glGet(Enum.GL_UNPACK_SKIP_PIXELS), 0)
        self.assertEqual(gles.glGet(Enum.GL_UNPACK_SKIP_ROWS), 0)
        self.assertEqual(gles.glGet(Enum.GL_UNPACK_SKIP_IMAGES), 0)
        self.assertEqual(gles.glGet(Enum.GL_UNPACK_ALIGNMENT), 4)

        gles.glPixelStorei(Enum.GL_PACK_ALIGNMENT, 1)
        self.assertEqual(gles.glGet(Enum.GL_PACK_ALIGNMENT), 1)
        self.assertEqual(gles.glGet(Enum.GL_UNPACK_ALIGNMENT), 4)
        gles.glPixelStorei(Enum.GL_UNPACK_ALIGNMENT, 8)
        self.assertEqual(gles.glGet(Enum.GL_PACK_ALIGNMENT), 1)
        self.assertEqual(gles.glGet(Enum.GL_UNPACK_ALIGNMENT), 8)

    def test_bind_texture(self):
        from GLESContext import Context as GLES
        gles = GLES()

        # check the initial state
        self.assertEqual(gles.glGet(Enum.GL_ACTIVE_TEXTURE), Enum.GL_TEXTURE0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_2D), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_2D_ARRAY), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_3D), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_CUBE_MAP), 0)

        gles.glBindTexture(Enum.GL_TEXTURE_2D, 2)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_2D), 2)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_2D_ARRAY), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_3D), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_CUBE_MAP), 0)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, False)

        gles.glBindTexture(Enum.GL_TEXTURE_CUBE_MAP, 4)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_2D), 2)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_2D_ARRAY), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_3D), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_CUBE_MAP), 4)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_CUBE_MAP)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, False)

        gles.glBindTexture(Enum.GL_TEXTURE_2D, 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_2D), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_2D_ARRAY), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_3D), 0)
        self.assertEqual(gles.glGet(Enum.GL_TEXTURE_BINDING_CUBE_MAP), 4)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj, None)

    def test_tex_storage_2d(self):
        from GLESContext import Context as GLES
        gles = GLES()

        gles.glBindTexture(Enum.GL_TEXTURE_2D, 1)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 0)

        gles.glTexStorage2D(Enum.GL_TEXTURE_2D, 1, Enum.GL_RGB8, 2, 2)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj.mipmap, False)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB8)
        self.assertEqual(tex_obj.width, 2)
        self.assertEqual(tex_obj.height, 2)
        self.assertEqual(tex_obj.depth, 1)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_CUBE_MAP)
        self.assertEqual(tex_obj, None)

        gles.glBindTexture(Enum.GL_TEXTURE_CUBE_MAP, 3)
        gles.glTexStorage2D(Enum.GL_TEXTURE_CUBE_MAP, 3, Enum.GL_RGBA4, 4, 4)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_CUBE_MAP)
        self.assertEqual(tex_obj.mipmap, True)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGBA4)
        self.assertEqual(tex_obj.width, 4)
        self.assertEqual(tex_obj.height, 4)
        self.assertEqual(tex_obj.depth, 1)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_CUBE_MAP, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertNotEqual(tex_obj, None)

    def test_tex_storage_3d(self):
        from GLESContext import Context as GLES
        gles = GLES()

        gles.glBindTexture(Enum.GL_TEXTURE_3D, 1)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_3D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 0)
        gles.glTexStorage3D(Enum.GL_TEXTURE_3D, 2, Enum.GL_RGB8, 2, 2, 4)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_3D)
        self.assertEqual(tex_obj.mipmap, True)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB8)
        self.assertEqual(tex_obj.width, 2)
        self.assertEqual(tex_obj.height, 2)
        self.assertEqual(tex_obj.depth, 4)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_3D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D_ARRAY)
        self.assertEqual(tex_obj, None)

        gles.glBindTexture(Enum.GL_TEXTURE_2D_ARRAY, 3)
        gles.glTexStorage3D(Enum.GL_TEXTURE_2D_ARRAY, 3, Enum.GL_RGBA4, 4, 4, 1)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D_ARRAY)
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_2D_ARRAY)
        self.assertEqual(tex_obj.mipmap, True)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGBA4)
        self.assertEqual(tex_obj.width, 4)
        self.assertEqual(tex_obj.height, 4)
        self.assertEqual(tex_obj.depth, 1)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D_ARRAY, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_3D)
        self.assertNotEqual(tex_obj, None)

    def test_active_texture(self):
        from GLESContext import Context as GLES
        gles = GLES()

        # check the initial state
        self.assertEqual(gles.glGet(Enum.GL_ACTIVE_TEXTURE), Enum.GL_TEXTURE0)

        # try to bind a texture object to the old texture unit
        gles.glBindTexture(Enum.GL_TEXTURE_3D, 1)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_3D)
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_3D)
        self.assertNotEqual(tex_obj, None)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj, None)

        # switch to a new texture unit and check the initial states
        gles.glActiveTexture(Enum.GL_TEXTURE3)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_3D)
        self.assertEqual(tex_obj, None)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj, None)

        # try to bind a new texture object to the new texture unit
        gles.glBindTexture(Enum.GL_TEXTURE_2D, 1)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertNotEqual(tex_obj, None)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_3D)
        self.assertEqual(tex_obj, None)

        # switch back to the old texture unit and make sure its states are restored
        gles.glActiveTexture(Enum.GL_TEXTURE0)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_3D)
        self.assertNotEqual(tex_obj, None)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj, None)

    def test_tex_image_2D(self):
        from GLESContext import Context as GLES
        gles = GLES()

        # bind and set format and dimensions for an empty 2D texture
        gles.glBindTexture(Enum.GL_TEXTURE_2D, 1)
        gles.glTexImage2D(Enum.GL_TEXTURE_2D, 0, Enum.GL_RGB5_A1, 2, 2, 0, Enum.GL_RGB, Enum.GL_UNSIGNED_SHORT_5_5_5_1, None)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj.mipmap, False)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB5_A1)
        self.assertEqual(tex_obj.width, 2)
        self.assertEqual(tex_obj.height, 2)
        self.assertEqual(tex_obj.depth, 1)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)

        # reset the modification state
        tex_obj.modified = False

        # set level 1 with None data
        gles.glTexImage2D(Enum.GL_TEXTURE_2D, 1, Enum.GL_RGB5_A1, 1, 1, 0, Enum.GL_RGB, Enum.GL_UNSIGNED_SHORT_5_5_5_1, None)
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj.mipmap, True)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB5_A1)
        self.assertEqual(tex_obj.width, 2)
        self.assertEqual(tex_obj.height, 2)
        self.assertEqual(tex_obj.depth, 1)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)

        # reset the modification state
        tex_obj.modified = False

        # set level 1 with data
        gles.glTexSubImage2D(Enum.GL_TEXTURE_2D, 1, 0, 0, 1, 1, Enum.GL_RGB, Enum.GL_UNSIGNED_SHORT_5_5_5_1, 'FFFF'.decode('hex'))
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_2D)
        self.assertEqual(tex_obj.mipmap, True)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB5_A1)
        self.assertEqual(tex_obj.width, 2)
        self.assertEqual(tex_obj.height, 2)
        self.assertEqual(tex_obj.depth, 1)
        self.assertEqual(tex_obj.initialized, True)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)

        # check cube texture target isn't affected
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_CUBE_MAP)
        self.assertEqual(tex_obj, None)

        # try to set the data for a cubemap texture
        gles.glBindTexture(Enum.GL_TEXTURE_CUBE_MAP, 2)
        gles.glTexImage2D(Enum.GL_TEXTURE_CUBE_MAP_POSITIVE_X, 0, Enum.GL_RGB565, 1, 1, 0, Enum.GL_RGB, Enum.GL_UNSIGNED_SHORT_5_6_5, '0000'.decode('hex'))
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_CUBE_MAP)
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_CUBE_MAP)
        self.assertEqual(tex_obj.mipmap, False)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB565)
        self.assertEqual(tex_obj.width, 1)
        self.assertEqual(tex_obj.height, 1)
        self.assertEqual(tex_obj.depth, 1)
        self.assertEqual(tex_obj.initialized, True)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)

    def test_tex_image_3D(self):
        from GLESContext import Context as GLES
        gles = GLES()

        # bind and set format and dimensions for an empty 2D array texture
        gles.glBindTexture(Enum.GL_TEXTURE_2D_ARRAY, 10)
        gles.glTexImage3D(Enum.GL_TEXTURE_2D_ARRAY, 0, Enum.GL_RGB5_A1, 2, 2, 10, 0, Enum.GL_RGB, Enum.GL_UNSIGNED_SHORT_5_5_5_1, None)
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_2D_ARRAY)
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_2D_ARRAY)
        self.assertEqual(tex_obj.mipmap, False)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB5_A1)
        self.assertEqual(tex_obj.width, 2)
        self.assertEqual(tex_obj.height, 2)
        self.assertEqual(tex_obj.depth, 10)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D_ARRAY, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)

        # reset the modification state
        tex_obj.modified = False

        # set level 1 with None data
        gles.glTexImage3D(Enum.GL_TEXTURE_2D_ARRAY, 1, Enum.GL_RGB5_A1, 1, 1, 5, 0, Enum.GL_RGB, Enum.GL_UNSIGNED_SHORT_5_5_5_1, None)
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_2D_ARRAY)
        self.assertEqual(tex_obj.mipmap, True)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB5_A1)
        self.assertEqual(tex_obj.width, 2)
        self.assertEqual(tex_obj.height, 2)
        self.assertEqual(tex_obj.depth, 10)
        self.assertEqual(tex_obj.initialized, False)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D_ARRAY, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)

        # reset the modification state
        tex_obj.modified = False

        # set level 1 with data
        gles.glTexSubImage3D(Enum.GL_TEXTURE_2D_ARRAY, 1, 0, 0, 1, 1, 1, 1, Enum.GL_RGB, Enum.GL_UNSIGNED_SHORT_5_5_5_1, 'FFFF'.decode('hex'))
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_2D_ARRAY)
        self.assertEqual(tex_obj.mipmap, True)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB5_A1)
        self.assertEqual(tex_obj.width, 2)
        self.assertEqual(tex_obj.height, 2)
        self.assertEqual(tex_obj.depth, 10)
        self.assertEqual(tex_obj.initialized, True)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_2D_ARRAY, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)

        # check 3d texture target isn't affected
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_3D)
        self.assertEqual(tex_obj, None)

        # try to set the data for a 3D texture
        gles.glBindTexture(Enum.GL_TEXTURE_3D, 2)
        gles.glTexImage3D(Enum.GL_TEXTURE_3D, 0, Enum.GL_RGB565, 1, 1, 1, 0, Enum.GL_RGB, Enum.GL_UNSIGNED_SHORT_5_6_5, '0000'.decode('hex'))
        tex_obj = gles.GetBoundTexture(Enum.GL_TEXTURE_3D)
        self.assertEqual(tex_obj.type, Enum.GL_TEXTURE_3D)
        self.assertEqual(tex_obj.mipmap, False)
        self.assertEqual(tex_obj.internalformat, Enum.GL_RGB565)
        self.assertEqual(tex_obj.width, 1)
        self.assertEqual(tex_obj.height, 1)
        self.assertEqual(tex_obj.depth, 1)
        self.assertEqual(tex_obj.initialized, True)
        self.assertEqual(tex_obj.modified, True)
        self.assertEqual(gles.glGetTexParameter(Enum.GL_TEXTURE_3D, Enum.GL_TEXTURE_IMMUTABLE_FORMAT), 1)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
