import pylink


class JLinkController:
    def __init__(self, device: str, interface=pylink.enums.JLinkInterfaces.SWD):
        self._device = device
        self._interface = interface
        self._jlink: pylink.JLink | None = None


    def write(self, address: int, value: int):
        if self._jlink is None:
            raise RuntimeError("J-Link is not connected")
                
        self._jlink.memory_write32(address, [value & 0xFFFFFFFF])

    def read(self, address: int) -> int:
        if self._jlink is None:
            raise RuntimeError("J-Link is not connected")
        
        return self._jlink.memory_read32(address, 1)[0]


# HALT / RESET
    def halt(self):
        if self._jlink is not None:
            return

        jlink = pylink.JLink()
        opened = False

        try:
            jlink.open()
            opened = True

            jlink.set_tif(self._interface)
            jlink.connect(self._device)

            jlink.reset(halt=True)

            self._jlink = jlink

        except Exception:
            if opened:
                jlink.close()
            raise


    def reset(self):
        if self._jlink is None:
            raise RuntimeError("J-Link is not connected")

        try:
            self._jlink.reset(halt=False)

        finally:
            self.disconnect()



# Connection state
    @property
    def connected(self) -> bool:
        return self._jlink is not None


    def disconnect(self):
        if self._jlink is None:
            return

        jlink = self._jlink
        self._jlink = None

        jlink.close()