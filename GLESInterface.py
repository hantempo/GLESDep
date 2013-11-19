import logging
logger = logging.getLogger(__name__)

from GLESEnum import GLESEnum

class GLESContext(object):

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

    def glPixelStorei(self, pname, param):
        name = GLESEnum.names[pname]
        setattr(self, name, param)

class GLESInterface(object):

    def __init__(self):

        self.current_context = GLESContext()

    def __getattr__(self, attr):

        if not self.current_context:
            logger.error('No current context')
            return None

        return getattr(self.current_context, attr)
