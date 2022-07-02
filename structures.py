from __future__ import annotations

import pprint as pp

def to_int(b: bytes):
    return int.from_bytes(b, byteorder='little')

def to_hex(b: bytes):
    return hex(to_int(b))


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
    

class Image:
    def __init__(self, bin: bytes):
        self.bootHeader = BootHeader(ConsumableBytes(bin[:0xb8]))
        self.registerInitializationTable = RegisterInitializationTable(bin[0xb8:0x8b8])
        self.pufHelperData = PUFHelperData(b'')
        self.imageHeaderTable = ImageHeaderTable(ConsumableBytes(bin[
            int(self.bootHeader.imageHeaderTableOffset, 16):
            int(self.bootHeader.imageHeaderTableOffset, 16) + 0x40
        ]))
        self.imageHeaders: list[ImageHeader] = self.getImageHeaders(
            bin, 
            int(self.imageHeaderTable.firstImageHeaderOffset, 16) * 4
        )
        self.partitionHeaders: list[PartitionHeader] = self.getPartitionHeaders(
            bin,
            int(self.imageHeaderTable.firstPartitionHeaderOffset, 16) * 4
        )

        headerACOffset = int(self.imageHeaderTable.headerAuthenticationCertificate, 16) * 4
        if headerACOffset == 0:
            self.headerAuthenticationCertificate = None
        else:
            self.headerAuthenticationCertificate = AuthenticationCertificate(
                ConsumableBytes(bin[headerACOffset:headerACOffset + 0xec0])
            )

        self.partitions: list[tuple[Partition, AuthenticationCertificate]] = self.getPartitions(
            bin, self.partitionHeaders
        )
        # check num images in list


    def getPartitions(self, bin: bytes, partitionHeaders: list[PartitionHeader]):
        partitions: list[tuple[Partition, AuthenticationCertificate]] = []
        for partitionHeader in partitionHeaders:
            partitionOffset = int(partitionHeader.actualPartitionWordOffset, 16) * 4
            # TODO: check if correct
            partition: Partition = Partition(
                bin[partitionOffset:partitionOffset+int(partitionHeader.unencryptedDataWordLength, 16)],
                partitionHeader.partitionID
            )
            AC: AuthenticationCertificate | None = None
            acOffset = int(partitionHeader.acOffset, 16) * 4
            if acOffset != 0:
                AC = AuthenticationCertificate(ConsumableBytes(bin[acOffset:acOffset+0xec0]))
            partitions.append((partition, AC))
        return partitions

        
    def getImageHeaders(self, bin: bytes, firstImageHeaderOffset: int) -> list[ImageHeader]:
        imageHeaders: list[ImageHeader] = []
        nextImageHeaderOffset: int = firstImageHeaderOffset
        while nextImageHeaderOffset != 0:
            # TODO: length is wrong
            imageHeader = ImageHeader(ConsumableBytes(bin[nextImageHeaderOffset:nextImageHeaderOffset + 0x20]))
            imageHeaders.append(imageHeader)
            # nextImageHeaderOffset is 0 if its the last image header
            nextImageHeaderOffset = int(imageHeader.nextImageHeaderOffset, 16) * 4
        return imageHeaders

    def getPartitionHeaders(self, bin: bytes, firstPartitionHeaderOffset: int) -> list[PartitionHeader]:
        partitionHeaders: list[PartitionHeader] = []
        nextPartitionHeaderOffset: int = firstPartitionHeaderOffset
        while nextPartitionHeaderOffset != 0:
            partitionHeader = PartitionHeader(ConsumableBytes(bin[nextPartitionHeaderOffset:nextPartitionHeaderOffset+0x40]))
            partitionHeaders.append(partitionHeader)
            # nextPartititonheaderOffset is 0 if its the last partition header
            nextPartitionHeaderOffset = int(partitionHeader.nextPartitionHeaderOffset, 16) * 4
        return partitionHeaders


class BootHeader:
    def __init__(self, bin: ConsumableBytes):
        self.armVectorTable = bin.consume(0x20)
        self.widthDetectionWord = to_hex(bin.consume(4))
        self.headerSignature = bin.consume(4)
        assert self.headerSignature == b'XNLX', f'{self.headerSignature=}'
        self.keySource = to_hex(bin.consume(4))
        self.fsblExecutionAddress = to_hex(bin.consume(4))
        self.sourceOffset = to_hex(bin.consume(4))
        self.pmuImageLength = to_hex(bin.consume(4))
        self.totalPMUFWLength = to_hex(bin.consume(4))
        self.fsblImageLength = to_hex(bin.consume(4))
        self.totalFSBLLength = to_hex(bin.consume(4))
        self.fsblImageAttributes = BootHeaderAttributes(ConsumableBits(bin.consume(4)))
        self.bootHeaderChecksum = bin.consume(4)
        self.obfuscatedBlackKeyStorage = bin.consume(32)
        self.shutterValue = bin.consume(4)
        self.userDefinedFields = bin.consume(40)
        self.imageHeaderTableOffset = to_hex(bin.consume(4))
        self.partitionTableHeaderOffset = to_hex(bin.consume(4))
        self.secureHeaderIV = bin.consume(12)
        self.obfuscatedBlackKeyIV = bin.consume(12)
        assert bin.pos == len(bin.data)
        assert bin.pos == 0xb8


class BootHeaderAttributes:
    def __init__(self, bin: ConsumableBits):
        assert bin.consume(16) == 0
        self.BHDR_RSA = bin.consume(2)
        assert bin.consume(2) == 0
        self.cpuSelect = bin.consume(2)
        self.hashingSelect = bin.consume(2)
        self.PUF_HD = bin.consume(2)
        assert bin.consume(6) == 0

        assert bin.pos == 32, f'{bin.pos=}'
        


class RegisterInitializationTable:
    def __init__(self, bin: bytes):
        self.bin = bin


class PUFHelperData:
    def __init__(self, bin: bytes):
        self.bin = bin


class ImageHeaderTable:
    def __init__(self, bin: ConsumableBytes):
        # TODO: check if little or big endian
        self.version = to_hex(bin.consume(4))
        self.countImageHeader = to_int(bin.consume(4))
        # word offset
        self.firstPartitionHeaderOffset = to_hex(bin.consume(4))
        # word offset
        self.firstImageHeaderOffset = to_hex(bin.consume(4))
        # word offset
        self.headerAuthenticationCertificate = to_hex(bin.consume(4))
        self.bootDeviceForFSBL = to_int(bin.consume(4))
        # 36 bytes padding
        assert bin.consume(36) == b'\x00' * 36
        self.checksum = bin.consume(4)
        assert bin.pos == len(bin.data)
        assert bin.pos == 0x40


class ImageHeader:
    def __init__(self, bin: ConsumableBytes):
        # word offset
        self.nextImageHeaderOffset = to_hex(bin.consume(4))
        # word offset
        self.correspondingPartitionHeader = to_hex(bin.consume(4))
        # reserved
        assert bin.consume(4) == b'\x00' * 4
        self.partitionCount = to_int(bin.consume(4))
        # length varies 
        # also includes string terminator and padding
        self.imageName = bin.consume(len(bin.data) - bin.pos)  


class PartitionHeader:
    def __init__(self, bin: ConsumableBytes):
        self.encryptedPartitionDataWordLength = to_hex(bin.consume(4))
        self.unencryptedDataWordLength = to_hex(bin.consume(4))
        # includes authentication certificate
        self.totalPartitionWordLength = to_hex(bin.consume(4))
        # word offset
        self.nextPartitionHeaderOffset = to_hex(bin.consume(4))
        self.destionationExecutionAddress = to_hex(bin.consume(4))
        self.destionationExecutionAddressHI = to_hex(bin.consume(4))
        self.destionationLoadAddressLO = to_hex(bin.consume(4))
        self.destionationLoadAddressHI = to_hex(bin.consume(4))
        self.actualPartitionWordOffset = to_hex(bin.consume(4))
        self.attributes = PartitionAttributes(ConsumableBits(bin.consume(4)))
        self.sectionCount = to_int(bin.consume(4))
        self.checksumWordOffset = to_hex(bin.consume(4))
        self.imageHeaderWordOffset = to_hex(bin.consume(4))
        self.acOffset = to_hex(bin.consume(4))
        self.partitionID = to_int(bin.consume(4))
        self.headerChecksum = bin.consume(4)
        assert bin.pos == 0x40, f'{bin.pos=}'
        assert bin.pos == len(bin.data)


class PartitionAttributes:
    def __init__(self, bin: ConsumableBits):
        assert bin.consume(8) == 0
        self.vectorLocation = bin.consume(1)
        assert bin.consume(3) == 0
        self.earlyHandoff = bin.consume(1)
        self.endianness = bin.consume(1)
        self.partitionOwner = bin.consume(2)
        self.rsaAuthCertPresent = bin.consume(1)
        self.checksumType = bin.consume(3)
        self.destinationCPU = bin.consume(4)
        self.encryptionPresent = bin.consume(1)
        self.destinationDevice = bin.consume(3)
        self.a5xExecState = bin.consume(1)
        self.exeptionLevel = bin.consume(2)
        self.trustzone = bin.consume(1)

        bin.pos == 32
        


class Partition:
    def __init__(self, bin: bytes, id: int):
        self.id = id
        self.bin = bin


class AuthenticationCertificate:
    def __init__(self, bin: ConsumableBytes):
        self.authenticationHeader = AuthenticationHeader(ConsumableBits(bin.consume(4)))
        self.spkID = to_int(bin.consume(4))
        self.UDF = bin.consume(56)
        self.PPK = Key(ConsumableBytes(bin.consume(0x440)))
        self.SPK = Key(ConsumableBytes(bin.consume(0x440)))
        self.spkSignature = bin.consume(0x200)
        self.bootHeaderSignature = bin.consume(0x200)
        self.partitionSignature = bin.consume(0x200)
        assert bin.pos == len(bin.data)
        assert bin.pos == 0xec0


class AuthenticationHeader:
    # TODO: likely reverse bits order
    def __init__(self, bin: ConsumableBits):
        assert bin.consume(12) == 0
        self.spkUserEfuseSelect = bin.consume(2)
        self.ppkKeySelect = bin.consume(2)
        self.acFormat = bin.consume(2)
        self.acVersion = bin.consume(2)
        self.ppkKeyType = bin.consume(1)
        self.ppkKeySource = bin.consume(2)
        self.spkEnable = bin.consume(1)
        self.publicStrength = bin.consume(4)
        self.hashAlgorithm = bin.consume(2)
        self.publicAlgorithm = bin.consume(2)

        assert bin.pos == 32


class Key:
    def __init__(self, bin: ConsumableBytes):
        self.mod = bin.consume(512).hex()
        self.mod_ext = bin.consume(512).hex()
        self.exp = bin.consume(4).hex()
        assert bin.consume(60) == b'\x00' * 60
        assert bin.pos == len(bin.data)
        assert bin.pos == 0x440
