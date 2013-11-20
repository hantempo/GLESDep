import logging
logger = logging.getLogger(__name__)

import collections

from GLESEnum import Enum

class TextureUnit(object):

    def __init__(self):

        # texture binding
        self.GL_TEXTURE_BINDING_2D = 0
        self.GL_TEXTURE_BINDING_2D_ARRAY = 0
        self.GL_TEXTURE_BINDING_3D = 0
        self.GL_TEXTURE_BINDING_CUBE_MAP = 0

    def bind_texture(self, target, texture):

        if target == Enum.GL_TEXTURE_2D:
            self.GL_TEXTURE_BINDING_2D = texture
        elif target == Enum.GL_TEXTURE_2D_ARRAY:
            self.GL_TEXTURE_BINDING_2D_ARRAY = texture
        elif target == Enum.GL_TEXTURE_3D:
            self.GL_TEXTURE_BINDING_3D = texture
        elif target == Enum.GL_TEXTURE_CUBE_MAP:
            self.GL_TEXTURE_BINDING_CUBE_MAP = texture
        else:
            logger.error('Unexpected texture target  : %s' % Enum.names[target])

class Context(object):

    def __init__(self):

        # pixel store states
        self.GL_PACK_ROW_LENGTH = 0
        self.GL_PACK_IMAGE_HEIGHT = 0
        self.GL_PACK_SKIP_PIXELS = 0
        self.GL_PACK_SKIP_ROWS = 0
        self.GL_PACK_SKIP_IMAGES = 0
        self.GL_PACK_ALIGNMENT = 4
        self.GL_UNPACK_ROW_LENGTH = 0
        self.GL_UNPACK_IMAGE_HEIGHT = 0
        self.GL_UNPACK_SKIP_PIXELS = 0
        self.GL_UNPACK_SKIP_ROWS = 0
        self.GL_UNPACK_SKIP_IMAGES = 0
        self.GL_UNPACK_ALIGNMENT = 4

        # texture states
        self.texture_units = collections.defaultdict(TextureUnit)
        self.GL_ACTIVE_TEXTURE = Enum.GL_TEXTURE0

    # textures
    def glPixelStorei(self, pname, param):
        name = Enum.names[pname]
        setattr(self, name, param)

    def glBindTexture(self, target, texture):
        self.texture_units[self.GL_ACTIVE_TEXTURE].bind_texture(target, texture)

    def __getattr__(self, attr):
        if attr in ['GL_TEXTURE_BINDING_2D', 'GL_TEXTURE_BINDING_2D_ARRAY',
            'GL_TEXTURE_BINDING_3D', 'GL_TEXTURE_BINDING_CUBE_MAP']:
            return getattr(self.texture_units[self.GL_ACTIVE_TEXTURE], attr)

class Interface(object):

    def __init__(self):

        self.current_context = Context()

    def __getattr__(self, attr):

        if not self.current_context:
            logger.error('No current context')
            return None

        return getattr(self.current_context, attr)
