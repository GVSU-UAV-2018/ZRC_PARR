from construct import *

message_crc = Struct('message_crc', SLInt32('crc'))

message_format = Struct('message_format',
    Enum(Byte('direction'),
        RPI_to_GS = 0x40,
        GS_to_RPI = 0x80,
        _default_ = 0x00
    ),
    Enum(Byte('data_type'),
        SYS_INFO = 0x40,
        DETECTION = 0x80,
        SETTINGS = 0x22,
        _default_ = 0x00
    ),
    Array(3, LFloat32('data')),
    Bit('scanning'),
    Embed(message_crc)
)
