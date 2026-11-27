from modules.BSP.stm32f4xx import *
from modules.BSP.stm32f407xx import *

from modules.BSP.GPIO import * 
from modules.BSP.SPIShell import * 

from modules.JLink import * 
from modules.Flash import * 
from modules.GUI import * 




class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.jlink = JLinkController("STM32F407VG")
        self.flash = Flash(FlashAccess(self._transfer, self._select_chip))
        
        self.root.protocol("WM_DELETE_WINDOW", self.OnClose)
        Register.access = RegisterAccess(self.jlink.write, self.jlink.read)

        self.spi = SPIShell()
        spi_selections = [  FieldSPISelection.Represent("SPI1", ["PA5", "PB3"], ["PA6","PB4"], ["PA7","PB5"]),  
                            FieldSPISelection.Represent("SPI2", ["PB10", "PB13"], ["PB15","PC3"], ["PB14","PC2"]),
                            FieldSPISelection.Represent("SPI3", ["PB3", "PC10"], ["PB5","PC12"], ["PB4","PC11"]) ]
        nss_ports = [ "GPIOA", "GPIOB", "GPIOC", "GPIOD", "GPIOE", "GPIOF", "GPIOG", "GPIOH" ]

        self.fieldSPI = FieldSPISelection(self.root, spi_selections, nss_ports)
        self.fieldFlash = FieldFlashCommands(self.root, self._cb_flash_ID, self._cb_flash_ERASE, self._cb_flash_STATUS)
        self.fieldJLink = FieldJLinkCommands(self.root, self._cb_JLink_HALT, self._cb_JLink_RESET)

        self.GUI()
        self._config_gui_by_jlink_state(False)

    def mainloop(self):
        self.root.mainloop()

    def OnClose(self):
        try:
            self.jlink.disconnect()
        finally:
            self.root.destroy()        

        
    def GUI(self):
        self.root.title("SPI Flash Proxy")

        self.root.geometry("500x250")
        self.root.resizable(True, True)

        self.fieldSPI.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        ttk.Separator(self.root, orient=tk.VERTICAL).grid(row=0, column=1, rowspan=1, sticky="ns", pady=(20, 20))
        self.fieldFlash.grid(row=0, column=2, sticky="ew", padx=15, pady=(10, 5))
        ttk.Separator(self.root, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky="ew", padx=35)
        self.fieldJLink.grid(row=2, column=0, columnspan=3, sticky="ew", padx=15, pady=(5, 5))

        self.root.columnconfigure(0, weight=1, uniform="fields")
        self.root.columnconfigure(2, weight=1, uniform="fields")

    def _config_gui_by_jlink_state(self, halted: bool):
        self.fieldFlash.SetState(halted)
        if halted:
            self.fieldJLink.SetStateRESET(True)
            self.fieldJLink.SetStateHALT(False)
        else:
            self.fieldJLink.SetStateHALT(True)
            self.fieldJLink.SetStateRESET(False)



    def _parse_pin(self, port_letter: str, pin_part: str) -> PortPin:
        PORTS = { "A": GPIOA, "B": GPIOB, "C": GPIOC, "D": GPIOD, "E": GPIOE, "F": GPIOF, "G": GPIOG, "H": GPIOH }
        return PortPin(PORTS[port_letter], int(pin_part, 0))
    
    def _get_spi_by_name(self, name: str) -> SPIPeriph | None:
        if name == "SPI1":
            return SPI1
        elif name == "SPI2":
            return SPI2
        elif name == "SPI3":
            return SPI3
        return None

    def _configure_spi(self):
        self.spi.Reset() # TODO: Resetting the configuration before each operation is a bad solution
        self.spi.SetSPI(self._get_spi_by_name(self.fieldSPI.spi))
        self.spi.SetAllPins(SPIShell.Pins(
            SCK = self._parse_pin(self.fieldSPI.sck[1], self.fieldSPI.sck[2:]),
            MISO = self._parse_pin(self.fieldSPI.miso[1], self.fieldSPI.miso[2:]),
            MOSI = self._parse_pin(self.fieldSPI.mosi[1], self.fieldSPI.mosi[2:]),
            NSS = self._parse_pin(self.fieldSPI.nss_port[4], self.fieldSPI.nss_pin)))
        self.spi.Begin()


# Callbacks:
# JLink
    def _cb_JLink_HALT(self):
        try:
            self.jlink.halt()
            print("Target halted")

        except pylink.errors.JLinkException as e:
            print(f"JLink HALT error: {e}")
            return

        self._config_gui_by_jlink_state(True)

    def _cb_JLink_RESET(self):
        try:
            self.jlink.reset()
            print("Target reset")

        except pylink.errors.JLinkException as e:
            print(f"JLink RESET error: {e}")
            return

        self._config_gui_by_jlink_state(False)


# SPI
    def _transfer(self, tx_data: bytes = b"", rx_size: int = 0) -> bytes:
        return self.spi.Transfer(tx_data, rx_size)

    def _select_chip(self, state: bool): 
        self.spi.SelectChip(state)


# Flash
    def _cb_flash_ID(self):
        try:
            self._configure_spi()
            res =  self.flash.ID()
        except Exception as e:
            print(f"Read flash ID failed: {e}")
            return

        print(f"{''.join('{:02X} '.format(x) for x in res)}")


    def _cb_flash_ERASE(self):
        try:
            self._configure_spi()
            self.flash.WriteEnable()
            self.flash.Erase()
        except Exception as e:
            print(f"Erase flash failed: {e}")
            return
        
        print(f"Erase command was sended to flash")


    def _cb_flash_STATUS(self):
        try:
            self._configure_spi()
            res = self.flash.Status_1()
            print(f"{''.join('{:02X} '.format(x) for x in bytes([res]))}")
        except Exception as e:
            print(f"Read flash Status 1 failed: {e}")
            return





app = Application()
app.mainloop()