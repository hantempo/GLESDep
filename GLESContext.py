import logging
logger = logging.getLogger(__name__)

import collections

from GLESEnum import Enum

class TextureObject(object):

    def __init__(self, type):

        # 2D, 2D array, 2D or cube map
        self.type = type

        # whether this texture object is mipmapped.
        # true if any level other than level 0 is set
        self.mipmap = False

        # whether the data has been initialized with non-null pointers or other buffer objects
        # true if the data of any level is set
        self.initialized = False

        # whether the data, dimensions and internal format has been modified since the last checking point, used to identify a texture instance
        self.modified = False

        self.states = {
            Enum.GL_TEXTURE_IMMUTABLE_FORMAT : 0,
        }

class TextureUnit(object):

    def __init__(self):

        self.states = {
            Enum.GL_TEXTURE_BINDING_2D : 0,
            Enum.GL_TEXTURE_BINDING_2D_ARRAY : 0,
            Enum.GL_TEXTURE_BINDING_3D : 0,
            Enum.GL_TEXTURE_BINDING_CUBE_MAP : 0,
        }

class Context(object):

    def __init__(self):

        self.states = {
            # pixel store states
            Enum.GL_PACK_ROW_LENGTH : 0,
            Enum.GL_PACK_IMAGE_HEIGHT : 0,
            Enum.GL_PACK_SKIP_PIXELS : 0,
            Enum.GL_PACK_SKIP_ROWS : 0,
            Enum.GL_PACK_SKIP_IMAGES : 0,
            Enum.GL_PACK_ALIGNMENT : 4,
            Enum.GL_UNPACK_ROW_LENGTH : 0,
            Enum.GL_UNPACK_IMAGE_HEIGHT : 0,
            Enum.GL_UNPACK_SKIP_PIXELS : 0,
            Enum.GL_UNPACK_SKIP_ROWS : 0,
            Enum.GL_UNPACK_SKIP_IMAGES : 0,
            Enum.GL_UNPACK_ALIGNMENT : 4,

            # texture unit states
            Enum.GL_ACTIVE_TEXTURE : Enum.GL_TEXTURE0,
            Enum.GL_TEXTURE_BINDING_2D : 0,
            Enum.GL_TEXTURE_BINDING_2D_ARRAY : 0,
            Enum.GL_TEXTURE_BINDING_3D : 0,
            Enum.GL_TEXTURE_BINDING_CUBE_MAP : 0,
        }

        # texture states
        self.texture_units = collections.defaultdict(TextureUnit)
        self.texture_objects = {}

    #@property
    #def active_texture_unit(self):
        #return self.texture_units[self.states[Enum.GL_ACTIVE_TEXTURE]]

    # query methods
    def glGet(self, pname):
        return self.states[pname]

    # textures

    # target enum -> target binding enum
    TEXTURE_TARGET_BINDING = {
        Enum.GL_TEXTURE_2D : Enum.GL_TEXTURE_BINDING_2D,
        Enum.GL_TEXTURE_2D_ARRAY : Enum.GL_TEXTURE_BINDING_2D_ARRAY,
        Enum.GL_TEXTURE_3D : Enum.GL_TEXTURE_BINDING_3D,
        Enum.GL_TEXTURE_CUBE_MAP : Enum.GL_TEXTURE_BINDING_CUBE_MAP,
        Enum.GL_TEXTURE_CUBE_MAP_POSITIVE_X : Enum.GL_TEXTURE_BINDING_CUBE_MAP,
        Enum.GL_TEXTURE_CUBE_MAP_POSITIVE_Y : Enum.GL_TEXTURE_BINDING_CUBE_MAP,
        Enum.GL_TEXTURE_CUBE_MAP_POSITIVE_Z : Enum.GL_TEXTURE_BINDING_CUBE_MAP,
        Enum.GL_TEXTURE_CUBE_MAP_NEGATIVE_X : Enum.GL_TEXTURE_BINDING_CUBE_MAP,
        Enum.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y : Enum.GL_TEXTURE_BINDING_CUBE_MAP,
        Enum.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z : Enum.GL_TEXTURE_BINDING_CUBE_MAP,
    }

    def _check_texture_name(self, tex_name):
        if tex_name == 0:
            logger.error('Failed to get/set texture object 0')
            return False

        if tex_name not in self.texture_objects:
            logger.error('Failed to get/set a unavailable texture object : %d' % tex_name)
            return False

        return True

    def GetBoundTexture(self, target):
        tex_name = self.states[self.TEXTURE_TARGET_BINDING[target]]
        if tex_name and tex_name in self.texture_objects:
            return self.texture_objects[tex_name]
        else:
            return None

    def glPixelStorei(self, pname, param):
        self.states[pname] = param

    def glActiveTexture(self, texture):
        old_tex_unit = self.states[Enum.GL_ACTIVE_TEXTURE]
        if texture == old_tex_unit:
            return

        # save texture binding states for the old texture unit
        old_tex_unit_obj = self.texture_units[old_tex_unit]
        for state_name in old_tex_unit_obj.states:
            old_tex_unit_obj.states[state_name] = self.states[state_name]

        # load texture binding states from the new texture unit
        new_tex_unit_obj = self.texture_units[texture]
        for state_name in new_tex_unit_obj.states:
            self.states[state_name] = new_tex_unit_obj.states[state_name]

        # switch the texture unit
        self.states[Enum.GL_ACTIVE_TEXTURE] = texture

    def glGetTexParameter(self, target, pname):
        tex_name = self.states[self.TEXTURE_TARGET_BINDING[target]]
        if self._check_texture_name(tex_name):
            return self.texture_objects[tex_name].states[pname]

    def glBindTexture(self, target, texture):
        self.states[self.TEXTURE_TARGET_BINDING[target]] = texture
        self.texture_objects[texture] = TextureObject(type=target)

    def glTexStorage2D(self, target, levels, internalformat, width, height):
        tex_name = self.states[self.TEXTURE_TARGET_BINDING[target]]
        if self._check_texture_name(tex_name):
            tex_obj = self.texture_objects[tex_name]
            tex_obj.mipmap = levels > 1
            tex_obj.internalformat = internalformat
            tex_obj.width = width
            tex_obj.height = height
            tex_obj.depth = 1
            tex_obj.states[Enum.GL_TEXTURE_IMMUTABLE_FORMAT] = 1
            tex_obj.modified = True

    def glTexStorage3D(self, target, levels, internalformat, width, height, depth):
        tex_name = self.states[self.TEXTURE_TARGET_BINDING[target]]
        if self._check_texture_name(tex_name):
            tex_obj = self.texture_objects[tex_name]
            tex_obj.mipmap = levels > 1
            tex_obj.internalformat = internalformat
            tex_obj.width = width
            tex_obj.height = height
            tex_obj.depth = depth
            tex_obj.states[Enum.GL_TEXTURE_IMMUTABLE_FORMAT] = 1
            tex_obj.modified = True

    def glTexImage2D(self, target, level, internalformat, width, height, border, format, type, data):
        tex_name = self.states[self.TEXTURE_TARGET_BINDING[target]]
        if self._check_texture_name(tex_name):
            tex_obj = self.texture_objects[tex_name]
            tex_obj.mipmap = level != 0
            if level == 0:
                tex_obj.internalformat = internalformat
                tex_obj.width = width
                tex_obj.height = height
                tex_obj.depth = 1
                tex_obj.states[Enum.GL_TEXTURE_IMMUTABLE_FORMAT] = 1
            tex_obj.initialized = data != None
            tex_obj.modified = True

    def glTexSubImage2D(self, target, level, xoffset, yoffset, width, height, format, type, data):
        tex_name = self.states[self.TEXTURE_TARGET_BINDING[target]]
        if self._check_texture_name(tex_name):
            tex_obj = self.texture_objects[tex_name]
            tex_obj.initialized = data != None
            tex_obj.modified = True

    def glTexImage3D(self, target, level, internalformat, width, height, depth, border, format, type, data):
        tex_name = self.states[self.TEXTURE_TARGET_BINDING[target]]
        if self._check_texture_name(tex_name):
            tex_obj = self.texture_objects[tex_name]
            tex_obj.mipmap = level != 0
            if level == 0:
                tex_obj.internalformat = internalformat
                tex_obj.width = width
                tex_obj.height = height
                tex_obj.depth = depth
                tex_obj.states[Enum.GL_TEXTURE_IMMUTABLE_FORMAT] = 1
            tex_obj.initialized = data != None
            tex_obj.modified = True

    def glTexSubImage3D(self, target, level, xoffset, yoffset, zoffset, width, height, depth, format, type, data):
        tex_name = self.states[self.TEXTURE_TARGET_BINDING[target]]
        if self._check_texture_name(tex_name):
            tex_obj = self.texture_objects[tex_name]
            tex_obj.initialized = data != None
            tex_obj.modified = True
