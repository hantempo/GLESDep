import logging
logger = logging.getLogger(__name__)

import pandas, collections

from GLESContext import TextureObject
from GLESEnum import Enum

class TextureCollector(object):

    def __init__(self):
        self.textures = pandas.DataFrame(columns=TextureObject.Attributes)

    # next available index for each GLES name
    NextIndex = collections.defaultdict(int)

    @staticmethod
    def generate_index(gles_name):
        second_part = TextureCollector.NextIndex[gles_name]
        TextureCollector.NextIndex[gles_name] += 1
        return '%04d_%04d' % (gles_name, second_part)

    def collect(self, context):
        for tex_name, tex_obj in context.texture_objects.items():
            if not tex_obj.modified:
                continue

            tex_attrs = collections.OrderedDict()
            for attr in TextureObject.Attributes:
                attr_value = getattr(tex_obj, attr)
                if attr in ['type', 'internalformat']:
                    attr_value = Enum.names[attr_value]
                tex_attrs[attr] = attr_value

            df = pandas.DataFrame(tex_attrs, index=[self.generate_index(tex_name)])
            self.textures = self.textures.append(df)
            tex_obj.modified = False
