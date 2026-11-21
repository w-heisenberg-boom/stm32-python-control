from typing import Callable
from dataclasses import dataclass



@dataclass
class FlashAccess:
    transfer: Callable[[bytes, int], bytes]
    select_chip: Callable[[bool], None]


class Flash:
    def __init__(self, access: FlashAccess):
        self._access = access


    def ID(self) -> bytes:
        self._access.select_chip(True)

        try:
            self._access.transfer(bytes([0x9F]))
            res = self._access.transfer(rx_size=3)
        except:
            self._access.select_chip(False)
            raise

        self._access.select_chip(False)
        return res

