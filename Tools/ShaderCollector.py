import logging
logger = logging.getLogger(__name__)

import pandas, collections, os

from GLESContext import ShaderObject, ProgramObject
from GLESEnum import Enum

VERTEX_SHADER_SUFFIX = 'vertex'
FRAGMENT_SHADER_SUFFIX = 'fragment'
SHADER_SUFFIX = {
    Enum.GL_VERTEX_SHADER       : VERTEX_SHADER_SUFFIX,
    Enum.GL_FRAGMENT_SHADER     : FRAGMENT_SHADER_SUFFIX,
}
SHADER_DIR = 'shaders'

class ShaderCollector(object):

    def __init__(self):
        self.shaders = pandas.DataFrame(columns=ShaderObject.Attributes)
        self.programs = pandas.DataFrame(columns=ProgramObject.Attributes)

    # next available index for each GLES name
    NextShaderIndex = collections.defaultdict(int)
    NextProgramIndex = collections.defaultdict(int)

    @staticmethod
    def generate_shader_index(gles_name):
        second_part = ShaderCollector.NextShaderIndex[gles_name]
        ShaderCollector.NextShaderIndex[gles_name] += 1
        return '%04d_%04d' % (gles_name, second_part)

    @staticmethod
    def generate_program_index(gles_name):
        second_part = ShaderCollector.NextProgramIndex[gles_name]
        ShaderCollector.NextProgramIndex[gles_name] += 1
        return '%04d_%04d' % (gles_name, second_part)

    def collect(self, context):
        current_program_name = context.glGet(Enum.GL_CURRENT_PROGRAM)
        if not context.glIsProgram(current_program_name):
            return
        current_program = context.program_objects[current_program_name]

        if not current_program.IsModified(context):
            return

        program_index = self.generate_program_index(current_program_name)
        df = pandas.DataFrame({}, index=[program_index])
        self.programs = self.programs.append(df)

        for shader_name in current_program.attached_shaders:
            shader = context.shader_objects[shader_name]

            if shader.modified:
                shader_index = self.generate_shader_index(shader_name)

                shader_attrs = collections.OrderedDict()
                shader_attrs['type'] = Enum.names[shader.type]
                filename = os.path.join(SHADER_DIR, '.'.join([shader_index, SHADER_SUFFIX[shader.type]]))

                if not os.path.exists(SHADER_DIR):
                    os.mkdir(SHADER_DIR)

                with open(filename, 'w') as output:
                    output.write(shader.source)
                shader_attrs['filename'] = filename

                df = pandas.DataFrame(shader_attrs, index=[shader_index])
                self.shaders = self.shaders.append(df)

                shader.modified = False
                shader.filename = filename

            filename = os.path.join(SHADER_DIR, '.'.join([program_index, SHADER_SUFFIX[shader.type]]))
            if os.path.exists(filename):
                os.remove(filename)
            os.symlink(os.path.basename(shader.filename), filename)
