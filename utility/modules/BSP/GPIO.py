from dataclasses import dataclass

from modules.BSP.stm32f4xx import *
from modules.BSP.stm32f407xx import *


def _gpio_get_mode_mask_by_enum(mode: PinMode) -> int:
    if mode == PinMode.INPUT:
        return 0
    if mode == PinMode.OUTPUT_PP or mode == PinMode.OUTPUT_OD:
        return 1
    elif mode == PinMode.ALTERNATE:
        return 2
    elif mode == PinMode.ANALOG:
        return 3
    return 0

def _gpio_check_pin_num(num: int):
    if not 0 <= num <= 15:
        raise ValueError("Pin number must be in range 0..15")





# *******************************************************************************
#
#	API
#
# *******************************************************************************

@dataclass
class Pin:
    port:   GPIOPort
    pin:    int
    mode:   PinMode
    pull:   PinPull | None = None
    alter:  PinAlter | None  = None



# **************************************************
#  Begin
# **************************************************

def GPIO_Pin_Begin(pin: Pin):
    _gpio_check_pin_num(pin.pin)

    if PortPin(pin.port, pin.pin) == PortPin(PORT_SWCLK, PIN_SWCLK) or \
    PortPin(pin.port, pin.pin) == PortPin(PORT_SWDIO, PIN_SWDIO):
        raise ValueError("Selected pin reserved for SWD functions!")

    # Clocking the port
    if not RCC_IS_CLK_ENABLED_GPIO(pin.port):
        RCC_CLK_ENABLE_GPIO(pin.port)

    # Output type
    if pin.mode == PinMode.OUTPUT_PP or pin.mode == PinMode.ALTERNATE:
        pin.port.OTYPER &= ~(GPIO_OTYPER_OT0 << pin.pin)
    elif pin.mode == PinMode.OUTPUT_OD:
        pin.port.OTYPER |= (GPIO_OTYPER_OT0 << pin.pin)

    # Pull
    pin.port.PUPDR &= ~(GPIO_PUPDR_PUPD0_MSK << (pin.pin * 2))
    if not pin.pull is None:
        pin.port.PUPDR |= (pin.pull.value << (pin.pin * 2))

    # Speed
    pin.port.OSPEEDR |= (GPIO_OSPEEDER_OSPEEDR0_MSK << (pin.pin * 2))

    # Alternate functions
    if pin.mode == PinMode.ALTERNATE and pin.alter is None:
        raise ValueError("Alternate function must be specified")

    if pin.mode == PinMode.ALTERNATE and pin.alter is not None:
        shift = (pin.pin % 8) * 4
        mask = (GPIO_AFRL_AFSEL0_MSK << shift)

        if pin.pin < 8:
            pin.port.AFRL = ((pin.port.AFRL & ~mask) | (pin.alter.value << shift))
        else:
            pin.port.AFRH = ((pin.port.AFRH & ~mask) | (pin.alter.value << shift))

    # Pin mode
    pin.port.MODER = ((pin.port.MODER & ~(GPIO_MODER_MODER0_MSK << (pin.pin * 2))) | (_gpio_get_mode_mask_by_enum(pin.mode) << (pin.pin * 2)))

def GPIO_Pin_Reset(portPin: PortPin):
    GPIO_Pin_Begin(Pin(port=portPin.port,pin=portPin.pin,mode=PinMode.ANALOG))



# **************************************************
#  Setters / Getters
# **************************************************

def GPIO_Pin_Set(portPin: PortPin, state: bool):
    _gpio_check_pin_num(portPin.pin)
    mask = GPIO_BSRR_BS0 if state else GPIO_BSRR_BR0
    portPin.port.BSRR = (mask << portPin.pin)

def GPIO_Pin_Get(portPin: PortPin) -> bool:
    _gpio_check_pin_num(portPin.pin)
    return (portPin.port.IDR & (GPIO_IDR_ID0 << portPin.pin)) != 0