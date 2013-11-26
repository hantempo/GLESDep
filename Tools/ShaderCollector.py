import logging
logger = logging.getLogger(__name__)

import pandas, collections, os

from GLESContext import ShaderObject
from GLESEnum import Enum

SHADER_SUFFIX = {
    Enum.GL_VERTEX_SHADER       : 'vertex',
    Enum.GL_FRAGMENT_SHADER     : 'fragment',
}
SHADER_DIR = 'shaders'

class ShaderCollector(object):

    def __init__(self):
        self.shaders = pandas.DataFrame(columns=ShaderObject.Attributes)

    # next available index for each GLES name
    NextIndex = collections.defaultdict(int)

    @staticmethod
    def generate_index(gles_name):
        second_part = ShaderCollector.NextIndex[gles_name]
        ShaderCollector.NextIndex[gles_name] += 1
        return '%04d_%04d' % (gles_name, second_part)

    def collect(self, context):
        current_program = context.GetCurrentProgram()
        if current_program:
            for shader_name in current_program.attached_shaders:
                shader = context.shader_objects[shader_name]

                if shader.modified:
                    shader_index = self.generate_index(shader_name)

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
