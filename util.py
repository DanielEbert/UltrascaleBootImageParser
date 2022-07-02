def to_int(b: bytes):
    return int.from_bytes(b, byteorder='little')

def to_hex(b: bytes):
    return hex(to_int(b))