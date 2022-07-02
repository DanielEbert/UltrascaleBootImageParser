class ConsumableBytes:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def consume(self, num_bytes: int) -> bytes:
        if self.pos + num_bytes > len(self.data):
            raise Exception(f'not enough bytes to consume {self.pos=} {self.num_bytes=} {self.data=}')
        ret = self.data[self.pos:self.pos + num_bytes]
        self.pos += num_bytes
        return ret


class ConsumableBits:
    def __init__(self, data: bytes):
        self.bits = []
        self.pos = 0
        for byte in data:
            self.bits = [int(i) for i in "{0:08b}".format(byte)] + self.bits
    
    def consume(self, num_bits: int) -> int:
        if self.pos + num_bits > len(self.bits):
            raise Exception(f'not enough bits to consume {self.pos=} {self.num_bits=} {self.bits=}')
        ret = 0
        for _ in range(num_bits):
            ret <<= 1;
            ret += self.bits[self.pos]
            self.pos += 1
        return ret