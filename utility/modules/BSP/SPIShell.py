import time
from copy import copy


from modules.BSP.stm32f4xx import *
from modules.BSP.stm32f407xx import *

from modules.BSP.GPIO import *



class SPIShell:
    class PinType(Enum):
        SCK     = 0
        MISO    = 1
        MOSI    = 2
        NSS     = 3

    @dataclass
    class Pins:
        SCK:        PortPin | None = None
        MISO:       PortPin | None = None
        MOSI:       PortPin | None = None
        NSS:        PortPin | None = None


    def __init__(self, spi: SPIPeriph | None = None, pins: Pins | None = None):
        self._real_spi: SPIPeriph | None = None
        self._real_pins: SPIShell.Pins | None = None

        self._wish_spi = spi
        self._wish_pins = pins


# Validate
    def _validate_pin(self, spi: SPIPeriph, pin: PortPin | None, pinType: PinType):
        if not pin:
            raise ValueError("Pin is None!")

        if pin == PortPin(PORT_SWDIO, PIN_SWDIO) or pin == PortPin(PORT_SWCLK, PIN_SWCLK):
            raise ValueError(f"Cannot select a debug pin as SPI {pinType.name}")

        capability = SPI_CAPABILITIES[spi]

        if pinType == self.PinType.NSS:
            for pinType in (self.PinType.SCK, self.PinType.MISO, self.PinType.MOSI):
                if pin == getattr(self._wish_pins, pinType.name):
                    raise ValueError(f"NSS cannot use the same pin as {pinType.name}")
        else:
            if not pin in getattr(capability, pinType.name, None):
                raise ValueError(f"Cannot select unsupported value for {pinType.name}")


    def _validate_all_pins(self, spi: SPIPeriph, pins: Pins | None):
        if not pins:
            raise ValueError("Pins is None!")
        self._validate_pin(spi, pins.SCK, self.PinType.SCK)
        self._validate_pin(spi, pins.MISO, self.PinType.MISO)
        self._validate_pin(spi, pins.MOSI, self.PinType.MOSI)
        self._validate_pin(spi, pins.NSS, self.PinType.NSS)

    def _validate_spi(self, spi: SPIPeriph | None):
        if not spi:
            raise ValueError("Pins is None!")


# Begin
    def _begin_spi(self, wish_spi: SPIPeriph, real_spi: SPIPeriph | None):
        if (real_spi is not None) and (real_spi == wish_spi):
            return
    
        spi = wish_spi

        if not RCC_IS_CLK_ENABLED_SPI(spi):
            RCC_CLK_ENABLE_SPI(spi)

        # 1. BR = 0b111 - Slowest speed
        spi.CR1 |= SPI_CR1_BR_MSK

        # 2. CPOL = 0 && CPHA = 0
        spi.CR1 &= ~(SPI_CR1_CPOL_MSK | SPI_CR1_CPHA_MSK)

        # 3. DFF = 0
        spi.CR1 &= ~SPI_CR1_DFF_MSK

        # 4. LSBFIRST = 0
        spi.CR1 &= ~SPI_CR1_LSBFIRST_MSK

        # 5. Software NSS
        spi.CR1 |= SPI_CR1_SSM_MSK
        spi.CR1 |= SPI_CR1_SSI_MSK

        # 6. MSTR = 1 && SPE = 1
        spi.CR1 |= SPI_CR1_MSTR_MSK
        spi.CR1 |= SPI_CR1_SPE_MSK


    def _begin_gpio(self, wish_pins: Pins, real_pins: Pins | None):
        self._configure_pin_if_needed(wish_pins, real_pins, self.PinType.SCK)
        self._configure_pin_if_needed(wish_pins, real_pins, self.PinType.MISO)
        self._configure_pin_if_needed(wish_pins, real_pins, self.PinType.MOSI)
        self._configure_pin_if_needed(wish_pins, real_pins, self.PinType.NSS)

    def _configure_pin_if_needed(self, wish_pins: Pins, real_pins: Pins | None, pinType: PinType):
        p_wish = getattr(wish_pins, pinType.name, None)
        p_real = None

        if real_pins is not None:
            p_real = getattr(real_pins, pinType.name, [])

        if (p_real is None) or (p_real != p_wish):
            capability = SPI_CAPABILITIES[self._wish_spi]

            if pinType == self.PinType.NSS:
                p = Pin(p_wish.port, p_wish.pin, PinMode.OUTPUT_PP, None, None)

                if not RCC_IS_CLK_ENABLED_GPIO(p.port):
                    RCC_CLK_ENABLE_GPIO(p.port)

                GPIO_Pin_Set(PortPin(p.port, p.pin), True)
            else:
                alter = capability.ALTER
                p = Pin(p_wish.port, p_wish.pin, PinMode.ALTERNATE, PinPull.PULL_UP, alter)
            
            GPIO_Pin_Begin(p)





# **************************************************
#  API
# **************************************************

# Begin
    def Begin(self):
        self._validate_spi(self._wish_spi)
        self._validate_all_pins(self._wish_spi, self._wish_pins)

        self._begin_gpio(self._wish_pins, self._real_pins)
        self._begin_spi(self._wish_spi, self._real_spi)

        self._real_pins = copy(self._wish_pins)
        self._real_spi = self._wish_spi

# Reset
    def Reset(self):
        if self._real_spi is not None:
            RCC_RESET_SPI(self._real_spi)
            self._real_spi = None

        if self._real_pins is not None:
            for pin_type in self.PinType:
                pin = getattr(self._real_pins, pin_type.name)
                if pin is not None:
                    GPIO_Pin_Reset(pin)
                    setattr(self._real_pins, pin_type.name, None)


# Interaction with World
    def _wait_flag(self, spi: SPIPeriph, mask: int, state: bool = True, timeout: float = 1.0):
        start = time.monotonic()
        while bool(spi.SR & mask) != state:
            time.sleep(0)
            if time.monotonic() - start > timeout:
                raise TimeoutError(f"SPI timeout, SR=0x{spi.SR:08X}")


    def Transfer(self, tx_data: bytes = b"", rx_size: int = 0) -> bytes:
        self._validate_spi(self._real_spi)
        self._validate_all_pins(self._real_spi, self._real_pins)

        if rx_size < 0:
            raise ValueError("rx_size must be non-negative")

        res = bytearray()
        spi = self._real_spi

        for i in range(max(len(tx_data), rx_size)):
            tx_byte = tx_data[i] if i < len(tx_data) else 0xFF

            self._wait_flag(spi, SPI_SR_TXE_MSK)
            spi.DR = tx_byte

            self._wait_flag(spi, SPI_SR_RXNE_MSK)
            rx_byte = spi.DR & 0xFF

            if i < rx_size:
                res.append(rx_byte)

        self._wait_flag(spi, SPI_SR_TXE_MSK)
        self._wait_flag(spi, SPI_SR_BSY_MSK, False)
        return bytes(res)


    def SelectChip(self, state: bool):
        self._validate_spi(self._real_spi)
        self._validate_all_pins(self._real_spi, self._real_pins)
    
        GPIO_Pin_Set(self._real_pins.NSS, False if state else True)



# Setters
    def SetSPI(self, spi: SPIPeriph):
        self._wish_spi = spi


    def SetAllPins(self, pins: Pins):
        self._wish_pins = pins

    def SetSCK(self, pin: PortPin):
        self._set_pin(pin, self.PinType.SCK)
        
    def SetMISO(self, pin: PortPin):
        self._set_pin(pin, self.PinType.MISO)
        
    def SetMOSI(self, pin: PortPin):
        self._set_pin(pin, self.PinType.MOSI)

    def SetNSS(self, pin: PortPin):
        self._set_pin(pin, self.PinType.NSS)

    def _set_pin(self, pin: PortPin, pinType: PinType):
        if self._wish_pins is None:
            self._wish_pins = self.Pins()
        setattr(self._wish_pins, pinType.name, pin)        

        
# Properties
    @property
    def SPI(self) -> SPIPeriph:
        return self._wish_spi


    @property
    def AllPins(self) -> Pins | None:
        return self._wish_pins

    @property
    def SCK(self):
        return self._wish_pins.SCK

    @property
    def MISO(self):
        return self._wish_pins.MISO

    @property
    def MOSI(self):
        return self._wish_pins.MOSI

    @property
    def NSS(self):
        return self._wish_pins.NSS