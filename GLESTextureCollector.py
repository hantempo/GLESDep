import logging
logger = logging.getLogger(__name__)

import GLESContext

class TextureCollector(object):

    def __init__(self):

        self.current_context = GLESContext.Context()

    def __getattr__(self, attr):

        if not self.current_context:
            logger.error('No current context')
            return None

        return getattr(self.current_context, attr)
