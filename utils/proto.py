import ctypes
import codecs
import nacl.public

UMA_PUBKEY = "6b20e2ab6c311330f761d737ce3f3025750850665eea58b6372f8d2f57501eb3e6355f6fd9f01d9a3aba9d89cabd628635279b8a"
UMA_PUBKEY = codecs.decode(UMA_PUBKEY, "hex")
UMA_PUBKEY = nacl.public.PublicKey(UMA_PUBKEY[:32])

class AuthInfoCertUUID(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("cert_uuid", ctypes.c_ubyte * 16),
        ("random_padding", ctypes.c_ubyte * 18),
    ]


class AuthInfoAuthKey(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("auth_key", ctypes.c_ubyte * 34),
    ]


class AuthInfoEncrypted(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("encryted_bytes", ctypes.c_ubyte * 34),
    ]


class AuthInfoData(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ("cert_uuid", AuthInfoCertUUID),
        ("auth_key", AuthInfoAuthKey),
    ]


class AuthInfo(ctypes.LittleEndianStructure):
    _pack_ = 1
    _anonymous_ = ["data", ]
    _fields_ = [
        ("type", ctypes.c_uint16),
        ("data", AuthInfoData),
    ]


class UmaVariableDataMetaClass(type(ctypes.Structure)):
    # This trick is comes from https://github.com/python/cpython/blob/bb3e0c240bc60fe08d332ff5955d54197f79751c/Lib/ctypes/_endian.py#L23
    def __setattr__(self, attrname, value):
        if attrname == "_fields_":
            fields = []
            for desc in value:
                name = desc[0]
                typ = desc[1]
                rest = desc[2:]
                fields.append((name, typ) + rest)
                assert name != "_data"
            fields.insert(0, ("size", ctypes.c_uint32))
            fields.append(("_data", ctypes.c_ubyte*0))
            value = fields
        super().__setattr__(attrname, value)


class UmaVariableStructure(ctypes.LittleEndianStructure, metaclass=UmaVariableDataMetaClass): # type:ignore

    @property
    def data(self) -> bytes:
        assert self._pack_ == 1
        size = ctypes.sizeof(self) - (ctypes.addressof(self._data) - ctypes.addressof(self))
        typ = ctypes.POINTER((ctypes.c_ubyte*size))
        p = ctypes.cast(ctypes.pointer(self._data), typ)
        return bytes(p[0])

    @data.setter
    def data(self, bs: bytes):
        assert self._pack_ == 1
        size = (ctypes.addressof(self._data) - ctypes.addressof(self)) + len(bs)
        ctypes.resize(self, size)
        ctypes.memmove(ctypes.addressof(self._data), bs, len(bs))

        
class UmaRequest(UmaVariableStructure): # type: ignore
    _pack_ = 1
    _fields_ = [
        ("client_pubkey", ctypes.c_ubyte * 32),
        ("aes_info", ctypes.c_ubyte * 36),
        ("auth_tag", ctypes.c_ubyte * 16),
    ]


class UmaResponse(UmaVariableStructure): # type: ignore
    _pack_ = 1
    _fields_ = [
        ("gcm_iv", ctypes.c_ubyte * 16),
        ("auth_tag", ctypes.c_ubyte * 16),
    ]

