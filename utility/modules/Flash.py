from typing import Callable
from dataclasses import dataclass



MANUFACTURER = {
    0xEF: "Winbond",
    0xC8: "GigaDevice",
    0xC2: "Macronix",
    0x9D: "ISSI",
    0x20: "Micron",
    0x5E: "Zbit",
    0x85: "Puya" }

MEMORY_TYPE = {
    0x40: "SPI",
    0x60: "QPI" }

CAPACITY = {
    0x12: "256 kB",
    0x13: "512 kB",
    0x14: "1 MB",
    0x15: "2 MB",
    0x16: "4 MB",
    0x17: "8 MB",
    0x18: "16 MB" }



# ****************************************************************************************************
#
#  COMMANDS
#
# ****************************************************************************************************

# Configuration and Status Commands
FLASH_READ_STATUS_1 =                 0x05
FLASH_READ_STATUS_2 =                 0x35
FLASH_READ_STATUS_3 =                 0x15

FLASH_WRITE_ENABLE =                  0x06
FLASH_VOLATILE_SR_WRITE_ENABLE =      0x50
FLASH_WRITE_DISABLE =                 0x04

FLASH_WRITE_STATUS_1 =                0x01
FLASH_WRITE_STATUS_2 =                0x31
FLASH_WRITE_STATUS_3 =                0x11

FLASH_ENTER_QPI_MODE =                0x38
FLASH_EXIT_QPI_MODE =                 0xFF


# Program and Erase Commands
FLASH_PAGE_PROGRAM =                  0x02
FLASH_QUAD_INPUT_PAGE_PROGRAM =       0x32

FLASH_SECTOR_ERASE =                  0x20
FLASH_BLOCK_ERASE =                   0xD8
FLASH_HALF_BLOCK_ERASE =              0x52

FLASH_CHIP_ERASE =                    0xC7
FLASH_ERASE_PROGRAM_SUSPEND =         0x75
FLASH_ERASE_PROGRAM_RESUME =          0x7A


# Read Commands
FLASH_READ_DATA =                     0x03

FLASH_FAST_READ =                     0x0B
FLASH_FAST_READ_DUAL_OUTPUT =         0x3B
FLASH_FAST_READ_QUAD_OUTPUT =         0x6B

FLASH_FAST_READ_DUAL_IO =             0xBB
FLASH_FAST_READ_QUAD_IO =             0xEB
FLASH_WORD_READ_QUAD_IO =             0xE7
FLASH_OCTAL_WORD_READ_QUAD_IO =       0xE3

FLASH_SET_READ_PARAMETERS =           0xC0
FLASH_BURST_READ_WITH_WRAP =          0x0C
FLASH_SET_BURST_WITH_WRAP =           0x77


# Reset Commands
FLASH_SOFTWARE_RESET_ENABLE =         0x66
FLASH_SOFTWARE_RESET =                0x99


# ID and Security Commands
FLASH_DEEP_POWER_DOWN =               0xB9
FLASH_RELEASE_POWER_DOWN =             0xAB

FLASH_DEVICE_ID =                     0xAB

FLASH_READ_IDENTIFICATION =            0x9F
FLASH_ID_MANUFACTURER_IDX =            0
FLASH_ID_MEMORY_TYPE_IDX =             1
FLASH_ID_CAPACITY_IDX =                2

FLASH_READ_SFDP_REGISTERS =           0x5A
FLASH_MANUFACTURER_DEVICE_ID =        0x90

FLASH_ERASE_SECURITY_REGISTERS =      0x44
FLASH_PROGRAM_SECURITY_REGISTERS =    0x42
FLASH_READ_SECURITY_REGISTERS =       0x48

FLASH_MANUFACTURER_DEVICE_ID_DUAL =   0x92
FLASH_MANUFACTURER_DEVICE_ID_QUAD =   0x94

FLASH_UNIQUE_ID_NUMBER =              0x4B


# Lock Commands
FLASH_INDIVIDUAL_BLOCK_SECTOR_LOCK =   0x36
FLASH_INDIVIDUAL_BLOCK_SECTOR_UNLOCK = 0x39

FLASH_READ_BLOCK_SECTOR_LOCK =         0x3D

FLASH_GLOBAL_BLOCK_SECTOR_LOCK =       0x7E
FLASH_GLOBAL_BLOCK_SECTOR_UNLOCK =     0x98





@dataclass
class FlashAccess:
    transfer: Callable[[bytes, int], bytes]
    select_chip: Callable[[bool], None]


class Flash:
    @dataclass
    class Descriptor:
        Manufacturer: int
        MemoryType: int
        Capacity: int
        UniqueID: bytes


    def __init__(self, access: FlashAccess):
        self._access = access

    def _transfer(self, tx: bytes, rx_size: int) -> bytes:
        self._access.select_chip(True)
        res = b""

        try:
            self._access.transfer(tx)
            res = self._access.transfer(rx_size=rx_size)
        except:
            self._access.select_chip(False)
            raise

        self._access.select_chip(False)
        return res



    def GetDescriptor(self) -> Descriptor:
        main = self._transfer(bytes([FLASH_READ_IDENTIFICATION]), 3)
        id = self._transfer(bytes([FLASH_UNIQUE_ID_NUMBER]), 12)

        return self.Descriptor(
            Manufacturer    = main[FLASH_ID_MANUFACTURER_IDX],
            MemoryType      = main[FLASH_ID_MEMORY_TYPE_IDX],
            Capacity        = main[FLASH_ID_CAPACITY_IDX],
            UniqueID        = id[4:] )



    def WriteEnable(self):
        self._transfer(bytes([FLASH_WRITE_ENABLE]), 0)

    def EraseChip(self): 
        self._transfer(bytes([FLASH_CHIP_ERASE]), 0)


    def IsChipBusy(self) -> bool:
        status = self._transfer(bytes([FLASH_READ_STATUS_1]), 1)[0]
        return bool(status & 0x01)
