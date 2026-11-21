from dataclasses import dataclass
from enum import Enum
from collections.abc import Callable

from modules.BSP.stm32f407xx import *



@dataclass
class RegisterAccess:
    write: Callable[[int, int], None] | None = None
    read: Callable[[int], int] | None = None

class Register:
    access = RegisterAccess()

    def __init__(self, offset):
        self.offset = offset


    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.access.read is None:
            raise RuntimeError("Register read function is not configured")

        return self.access.read(instance.BASE + self.offset)

    def __set__(self, instance, value):
        if self.access.write is None:
            raise RuntimeError("Register write function is not configured")

        self.access.write(instance.BASE + self.offset, value)





# *******************************************************************************
#
#	Peripheral registers
#
# *******************************************************************************

class RCCControl:
    CR          = Register(0x00)
    PLLCFGR     = Register(0x04)
    CFGR        = Register(0x08)
    CIR         = Register(0x0C)
    AHB1RSTR    = Register(0x10)
    AHB2RSTR    = Register(0x14)
    AHB3RSTR    = Register(0x18)
    APB1RSTR    = Register(0x20)
    APB2RSTR    = Register(0x24)
    AHB1ENR     = Register(0x30)
    AHB2ENR     = Register(0x34)
    AHB3ENR     = Register(0x38)
    APB1ENR     = Register(0x40)
    APB2ENR     = Register(0x44)
    AHB1LPENR   = Register(0x50)
    AHB2LPENR   = Register(0x54)
    AHB3LPENR   = Register(0x58)
    APB1LPENR   = Register(0x60)
    APB2LPENR   = Register(0x64)
    BDCR        = Register(0x70)
    CSR         = Register(0x74)
    SSCGR       = Register(0x80)
    PLLI2SCFGR  = Register(0x84)

    def __init__(self, base):
        self.BASE = base


class GPIOPort:
    MODER   = Register(0x00)
    OTYPER  = Register(0x04)
    OSPEEDR = Register(0x08)
    PUPDR   = Register(0x0C)
    IDR     = Register(0x10)
    ODR     = Register(0x14)
    BSRR    = Register(0x18)
    LCKR    = Register(0x1C)
    AFRL    = Register(0x20)
    AFRH    = Register(0x24)

    def __init__(self, base):
        self.BASE = base


class SPIPeriph:
    CR1     = Register(0x00)
    CR2     = Register(0x04)
    SR      = Register(0x08)
    DR      = Register(0x0C)
    CRCPR   = Register(0x10)
    RXCRCR  = Register(0x14)
    TXCRCR  = Register(0x18)
    I2SCFGR = Register(0x1C)
    I2SPR   = Register(0x20)
    
    def __init__(self, base):
        self.BASE = base



RCC = RCCControl(AHB1.RCC)

GPIOA = GPIOPort(AHB1.GPIOA)
GPIOB = GPIOPort(AHB1.GPIOB)
GPIOC = GPIOPort(AHB1.GPIOC)
GPIOD = GPIOPort(AHB1.GPIOD)
GPIOE = GPIOPort(AHB1.GPIOE)
GPIOF = GPIOPort(AHB1.GPIOF)
GPIOG = GPIOPort(AHB1.GPIOG)
GPIOH = GPIOPort(AHB1.GPIOH)

SPI1 = SPIPeriph(APB2.SPI1)
SPI2 = SPIPeriph(APB1.SPI2)
SPI3 = SPIPeriph(APB1.SPI3)





# *******************************************************************************
#
#	Clock
#
# *******************************************************************************

# **********************************************************
#	GPIO
# **********************************************************

def RCC_CLK_ENABLE_GPIO(port: GPIOPort):
    clock_mask = {
        GPIOA: RCC_AHB1ENR_GPIOAEN,
        GPIOB: RCC_AHB1ENR_GPIOBEN,
        GPIOC: RCC_AHB1ENR_GPIOCEN,
        GPIOD: RCC_AHB1ENR_GPIODEN,
        GPIOE: RCC_AHB1ENR_GPIOEEN,
        GPIOF: RCC_AHB1ENR_GPIOFEN,
        GPIOG: RCC_AHB1ENR_GPIOGEN,
        GPIOH: RCC_AHB1ENR_GPIOHEN,
    }

    mask = clock_mask.get(port)
    if mask is None:
        return

    RCC.AHB1ENR |= mask

def RCC_IS_CLK_ENABLED_GPIO(port: GPIOPort) -> bool:
    clock_mask = {
        GPIOA: RCC_AHB1ENR_GPIOAEN,
        GPIOB: RCC_AHB1ENR_GPIOBEN,
        GPIOC: RCC_AHB1ENR_GPIOCEN,
        GPIOD: RCC_AHB1ENR_GPIODEN,
        GPIOE: RCC_AHB1ENR_GPIOEEN,
        GPIOF: RCC_AHB1ENR_GPIOFEN,
        GPIOG: RCC_AHB1ENR_GPIOGEN,
        GPIOH: RCC_AHB1ENR_GPIOHEN,
    }

    mask = clock_mask.get(port)
    if mask is None:
        return False

    return bool(RCC.AHB1ENR & mask)

def RCC_RESET_GPIO(port: GPIOPort) -> bool:
    clock_mask = {
        GPIOA: RCC_AHB1RSTR_GPIOARST,
        GPIOB: RCC_AHB1RSTR_GPIOBRST,
        GPIOC: RCC_AHB1RSTR_GPIOCRST,
        GPIOD: RCC_AHB1RSTR_GPIODRST,
        GPIOE: RCC_AHB1RSTR_GPIOERST,
        GPIOF: RCC_AHB1RSTR_GPIOFRST,
        GPIOG: RCC_AHB1RSTR_GPIOGRST,
        GPIOH: RCC_AHB1RSTR_GPIOHRST,
    }

    mask = clock_mask.get(port)
    if mask is None:
        return False

    return bool(RCC.AHB1RSTR & mask)


# **********************************************************
#	SPI
# **********************************************************

def RCC_CLK_ENABLE_SPI(spi: SPIPeriph):
    if spi == SPI1:
        RCC.APB2ENR |= RCC_APB2ENR_SPI1EN
    elif spi == SPI2:
        RCC.APB1ENR |= RCC_APB1ENR_SPI2EN
    elif spi == SPI3:
        RCC.APB1ENR |= RCC_APB1ENR_SPI3EN
    else:
        raise ValueError("Invalid SPI instance")        

def RCC_IS_CLK_ENABLED_SPI(spi: SPIPeriph) -> bool:
    if spi == SPI1:
        return bool(RCC.APB2ENR & RCC_APB2ENR_SPI1EN)
    elif spi == SPI2:
        return bool(RCC.APB1ENR & RCC_APB1ENR_SPI2EN)
    elif spi == SPI3:
        return bool(RCC.APB1ENR & RCC_APB1ENR_SPI3EN)
    else:
        raise ValueError("Invalid SPI instance")    

def RCC_RESET_SPI(spi: SPIPeriph):
    if spi == SPI1:
        reg = RCC.APB2RSTR
        mask = RCC_APB2RSTR_SPI1RST

    elif spi == SPI2:
        reg = RCC.APB1RSTR
        mask = RCC_APB1RSTR_SPI2RST

    elif spi == SPI3:
        reg = RCC.APB1RSTR
        mask = RCC_APB1RSTR_SPI3RST

    else:
        raise ValueError("Invalid SPI instance")

    reg |= mask
    reg &= ~mask





# *******************************************************************************
#
#	Peripheral description
#
# *******************************************************************************

# **********************************************************
#	GPIO
# **********************************************************

# SWD Pins
PORT_SWCLK  = GPIOA
PIN_SWCLK   = 14

PORT_SWDIO  = GPIOA
PIN_SWDIO   = 13


class PinMode(Enum):
    INPUT       = 0
    OUTPUT_PP   = 1
    OUTPUT_OD   = 2
    ALTERNATE   = 3
    ANALOG      = 4

class PinPull(Enum):
    PULL_UP     = 1
    PULL_DOWN   = 2

class PinAlter(Enum):
    AF0     = 0
    AF1     = 1
    AF2     = 2
    AF3     = 3
    AF4     = 4
    AF5     = 5
    AF6     = 6
    AF7     = 7
    AF8     = 8
    AF9     = 9
    AF10    = 10
    AF11    = 11
    AF12    = 12
    AF13    = 13
    AF14    = 14
    AF15    = 15

@dataclass
class PortPin:
    port: GPIOPort
    pin: int


# **********************************************************
#	SPI
# **********************************************************

@dataclass
class SPICapability:
    PERIPRH:    SPIPeriph
    ALTER:      PinAlter
    SCK:        list[PortPin]
    MISO:       list[PortPin]
    MOSI:       list[PortPin]

SPI1_CAPABILITY = SPICapability(
    PERIPRH = SPI1,
    ALTER = PinAlter.AF5,

    SCK =  [PortPin(GPIOA, 5),
            PortPin(GPIOB, 3) ],

    MISO = [PortPin(GPIOA, 6), 
            PortPin(GPIOB, 4) ],

    MOSI = [PortPin(GPIOA, 7), 
            PortPin(GPIOB, 5) ])


SPI2_CAPABILITY = SPICapability(
    PERIPRH = SPI2,
    ALTER = PinAlter.AF5,

    SCK =  [PortPin(GPIOB, 10),
            PortPin(GPIOB, 13) ],

    MISO = [PortPin(GPIOB, 15), 
            PortPin(GPIOC, 3) ],

    MOSI = [PortPin(GPIOB, 14), 
            PortPin(GPIOC, 2) ])


SPI3_CAPABILITY = SPICapability(
    PERIPRH = SPI3,
    ALTER = PinAlter.AF6,

    SCK =  [PortPin(GPIOB, 3),
            PortPin(GPIOC, 10) ],

    MISO = [PortPin(GPIOB, 5), 
            PortPin(GPIOC, 12) ],

    MOSI = [PortPin(GPIOB, 4), 
            PortPin(GPIOC, 11) ])

SPI_CAPABILITIES = {
    SPI1: SPI1_CAPABILITY,
    SPI2: SPI2_CAPABILITY,
    SPI3: SPI3_CAPABILITY}