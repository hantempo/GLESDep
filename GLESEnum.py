import logging
logger = logging.getLogger(__name__)

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['names'] = reverse
    return type('Enum', (), enums)

Enum = enum(
    GL_NONE                         = 0x0000,

    GL_TEXTURE_2D                   = 0x0DE1,
    GL_TEXTURE_CUBE_MAP             = 0x8513,
    GL_TEXTURE_CUBE_MAP_POSITIVE_X  = 0x8515,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_X  = 0x8516,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Y  = 0x8517,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y  = 0x8518,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Z  = 0x8519,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z  = 0x851A,
    GL_TEXTURE_2D_ARRAY             = 0x8C1A,
    GL_TEXTURE_3D                   = 0x806F,

    GL_TEXTURE_IMMUTABLE_FORMAT     = 0x912F,

    GL_TEXTURE_BINDING_2D           = 0x8069,
    GL_TEXTURE_BINDING_CUBE_MAP     = 0x8514,
    GL_TEXTURE_BINDING_2D_ARRAY     = 0x8C1D,
    GL_TEXTURE_BINDING_3D           = 0x806A,

    GL_ACTIVE_TEXTURE               = 0x84E0,
    GL_TEXTURE0                     = 0x84C0,
    GL_TEXTURE1                     = 0x84C1,
    GL_TEXTURE2                     = 0x84C2,
    GL_TEXTURE3                     = 0x84C3,
    GL_TEXTURE4                     = 0x84C4,
    GL_TEXTURE5                     = 0x84C5,
    GL_TEXTURE6                     = 0x84C6,
    GL_TEXTURE7                     = 0x84C7,
    GL_TEXTURE8                     = 0x84C8,

    GL_BYTE                         = 0x1400,
    GL_UNSIGNED_BYTE                = 0x1401,
    GL_SHORT                        = 0x1402,
    GL_UNSIGNED_SHORT               = 0x1403,
    GL_INT                          = 0x1404,
    GL_UNSIGNED_INT                 = 0x1405,
    GL_FLOAT                        = 0x1406,
    GL_HALF_FLOAT                   = 0x140B,
    GL_FIXED                        = 0x140C,

    GL_DEPTH_COMPONENT              = 0x1902,
    GL_ALPHA                        = 0x1906,
    GL_RGB                          = 0x1907,
    GL_RGBA                         = 0x1908,
    GL_LUMINANCE                    = 0x1909,
    GL_LUMINANCE_ALPHA              = 0x190A,

    GL_UNSIGNED_SHORT_4_4_4_4       = 0x8033,
    GL_UNSIGNED_SHORT_5_5_5_1       = 0x8034,
    GL_UNSIGNED_SHORT_5_6_5         = 0x8363,

    GL_RGB8                         = 0x8051,
    GL_RGBA4                        = 0x8056,
    GL_RGB5_A1                      = 0x8057,
    GL_RGBA8                        = 0x8058,
    GL_RGB10_A2                     = 0x8059,
    GL_DEPTH_COMPONENT24            = 0x81A6,
    GL_DEPTH_COMPONENT16            = 0x81A5,
    GL_SRGB                         = 0x8C40,
    GL_SRGB8                        = 0x8C41,
    GL_SRGB8_ALPHA8                 = 0x8C43,
    GL_STENCIL_INDEX8               = 0x8D48,
    GL_RGB565                       = 0x8D62,

    GL_ETC1_RGB8_OES                = 0x8D64,
    GL_COMPRESSED_RGB8_ETC2         = 0x9274,
    GL_COMPRESSED_SRGB8_ETC2        = 0x9275,
    GL_COMPRESSED_RGB8_PUNCHTHROUGH_ALPHA1_ETC2 = 0x9276,
    GL_COMPRESSED_SRGB8_PUNCHTHROUGH_ALPHA1_ETC2 = 0x9277,
    GL_COMPRESSED_RGBA8_ETC2_EAC    = 0x9278,
    GL_COMPRESSED_SRGB8_ALPHA8_ETC2_EAC = 0x9279,

    GL_COMPRESSED_RGBA_ASTC_4x4_KHR            = 0x93B0,
    GL_COMPRESSED_RGBA_ASTC_5x4_KHR            = 0x93B1,
    GL_COMPRESSED_RGBA_ASTC_5x5_KHR            = 0x93B2,
    GL_COMPRESSED_RGBA_ASTC_6x5_KHR            = 0x93B3,
    GL_COMPRESSED_RGBA_ASTC_6x6_KHR            = 0x93B4,
    GL_COMPRESSED_RGBA_ASTC_8x5_KHR            = 0x93B5,
    GL_COMPRESSED_RGBA_ASTC_8x6_KHR            = 0x93B6,
    GL_COMPRESSED_RGBA_ASTC_8x8_KHR            = 0x93B7,
    GL_COMPRESSED_RGBA_ASTC_10x5_KHR           = 0x93B8,
    GL_COMPRESSED_RGBA_ASTC_10x6_KHR           = 0x93B9,
    GL_COMPRESSED_RGBA_ASTC_10x8_KHR           = 0x93BA,
    GL_COMPRESSED_RGBA_ASTC_10x10_KHR          = 0x93BB,
    GL_COMPRESSED_RGBA_ASTC_12x10_KHR          = 0x93BC,
    GL_COMPRESSED_RGBA_ASTC_12x12_KHR          = 0x93BD,

    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR    = 0x93D0,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR    = 0x93D1,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR    = 0x93D2,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR    = 0x93D3,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR    = 0x93D4,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR    = 0x93D5,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR    = 0x93D6,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR    = 0x93D7,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR   = 0x93D8,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR   = 0x93D9,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR   = 0x93DA,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR  = 0x93DB,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR  = 0x93DC,
    GL_COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR  = 0x93DD,

    GL_PACK_ROW_LENGTH                         = 0x0D02,
    GL_PACK_IMAGE_HEIGHT                       = 0x806C,
    GL_PACK_SKIP_ROWS                          = 0x0D03,
    GL_PACK_SKIP_PIXELS                        = 0x0D04,
    GL_PACK_SKIP_IMAGES                        = 0x806B,
    GL_PACK_ALIGNMENT                          = 0x0D05,

    GL_UNPACK_ROW_LENGTH                       = 0x0CF2,
    GL_UNPACK_IMAGE_HEIGHT                     = 0x806E,
    GL_UNPACK_SKIP_ROWS                        = 0x0CF3,
    GL_UNPACK_SKIP_PIXELS                      = 0x0CF4,
    GL_UNPACK_SKIP_IMAGES                      = 0x806D,
    GL_UNPACK_ALIGNMENT                        = 0x0CF5,
)
