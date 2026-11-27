import re
from enum import Enum
from typing import Callable
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


INFORMATION_LABEL_FONT = ("Cascadia Code", 11, "bold")


def PlaceOnCenter(window: tk.Toplevel):
        window.update_idletasks()

        parent_x = window.master.winfo_rootx()
        parent_y = window.master.winfo_rooty()

        parent_width = window.master.winfo_width()
        parent_height = window.master.winfo_height()

        window_width = window.winfo_width()
        window_height = window.winfo_height()

        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        window.geometry(f"+{x}+{y}")
        window.update()





# ****************************************************************************************************
#
#  Widgets
#
# ****************************************************************************************************

# **************************************************
#  Information label
# **************************************************

class InformationLabel(ttk.Frame):
    def __init__(self, parent, text: str, value: str = "-"):
        super().__init__(parent)

        self._text = text
        self._value = value

        self._label = tk.Label(self, text=f"{self._text}: {self._value}", font=INFORMATION_LABEL_FONT)
        self._label.pack()

# API
    def set(self, value: str):
        self._value = value
        self._label.config(text=f"{self._text}: {self._value}")

    @property
    def value(self) -> str:
        return self._value


# **************************************************
#  Number entry
# **************************************************

# DEC or HEX
class EntryNumber(ttk.Entry):
    def __init__(self, parent, vmax: int | None, *args, **kwargs):
        self._vmax = vmax
        super().__init__(parent, *args, **kwargs)

        self._validate_cmd = (self.register(self._validate_number), "%P")
        self.configure(validate="key", validatecommand=self._validate_cmd)

    def _validate_number(self, value):
        if not (value == ""
            or re.fullmatch(r"[0-9]+", value) is not None
            or re.fullmatch(r"0[xX][0-9a-fA-F]*", value) is not None):
            return False

        try:
            if int(value, 0) > self._vmax:
                return False
        except Exception:
            return True

        return True





# ****************************************************************************************************
#
#  Windows
#
# ****************************************************************************************************

class WindowError(tk.Toplevel):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)

        self.title(title)
        self.resizable(False, False)
        self.geometry("300x100")

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.transient(parent)
        self.grab_set()
        
        self._frame_message = tk.Frame(self)
        tk.Label(self._frame_message, image="::tk::icons::error").pack(side="left")
        tk.Label(self._frame_message, text=message).pack(side="right")
        self._frame_message.pack(side="top", pady=(10, 0))

        ttk.Button(self, text="OK", command=self._close).pack(anchor="e", side="bottom", padx=15, pady=15)

        PlaceOnCenter(self)
        self.focus_force()

    def _close(self):
        self.destroy()

class WindowWarning(tk.Toplevel):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)

        self.title(title)
        self.resizable(False, False)
        self.geometry("300x100")

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.transient(parent)
        self.grab_set()
        
        self._frame_message = tk.Frame(self)
        tk.Label(self._frame_message, image="::tk::icons::warning").pack(side="left")
        tk.Label(self._frame_message, text=message).pack(side="right")
        self._frame_message.pack(side="top", pady=(10, 0))

        ttk.Button(self, text="OK", command=self._close).pack(anchor="e", side="bottom", padx=15, pady=15)

        PlaceOnCenter(self)
        self.focus_force()

    def _close(self):
        self.destroy()

class WindowInformation(tk.Toplevel):
    def __init__(self, parent, title: str, message: str, interactive: bool = False):
        super().__init__(parent)

        self.title(title)
        self.resizable(False, False)
        self.geometry("300x100" if interactive else "300x80")

        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.transient(parent)
        self.grab_set()
        
        self._frame_message = tk.Frame(self)
        tk.Label(self._frame_message, image="::tk::icons::information").pack(side="left")
        tk.Label(self._frame_message, text=message).pack(side="right")
        self._frame_message.pack(side="top", pady=(10, 0))

        if interactive:
            ttk.Button(self, text="OK", command=self.close).pack(anchor="e", side="bottom", padx=15, pady=15)

        PlaceOnCenter(self)
        self.focus_force()

    def close(self):
        self.destroy()





# ****************************************************************************************************
#
#  Fields
#
# ****************************************************************************************************

# **************************************************
#  SPI Selection
# **************************************************

class FieldSPISelection(ttk.Frame):
    @dataclass
    class Represent:
        spi:    str
        sck:    list[str]
        miso:   list[str]
        mosi:   list[str]

    def __init__(self, parent, selections: list[Represent], nss_ports: list[str]):
        super().__init__(parent)
        self._parent = parent
        self._nss_ports = nss_ports
        self._selections = selections
        self._selections_map = { s.spi: s for s in selections }

        self._val_spi       = tk.StringVar(value=self._selections[0].spi)
        self._val_sck       = tk.StringVar(value=self._selections[0].sck[0])
        self._val_miso      = tk.StringVar(value=self._selections[0].miso[0])
        self._val_mosi      = tk.StringVar(value=self._selections[0].mosi[0])
        self._val_nss_port  = tk.StringVar(value=self._nss_ports[0])
        self._val_nss_pin   = tk.StringVar(value="0")

        self._cbox_spi      = ttk.Combobox(self, state="readonly", textvariable=self._val_spi, values=[selection.spi for selection in self._selections])
        self._cbox_spi.bind("<<ComboboxSelected>>", self._changed_cbox_spi)
        
        self._cbox_sck      = ttk.Combobox(self, state="readonly", textvariable=self._val_sck, values=self._selections[0].sck)
        self._cbox_miso     = ttk.Combobox(self, state="readonly", textvariable=self._val_miso, values=self._selections[0].miso)
        self._cbox_mosi     = ttk.Combobox(self, state="readonly", textvariable=self._val_mosi, values=self._selections[0].mosi)
        self._cbox_nss_port = ttk.Combobox(self, state="readonly", textvariable=self._val_nss_port, values=self._nss_ports)
        self._entry_nss_pin = EntryNumber(self, vmax=15, textvariable=self._val_nss_pin)

        self._draw()


    def _draw(self):
        self._draw_text_cbox_field(self, self._cbox_spi, "SPI: ", 0)
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky="ew", padx=15, pady=(0, 10))
        self._draw_text_cbox_field(self, self._cbox_sck, "SCK: ", 2)
        self._draw_text_cbox_field(self, self._cbox_miso, "MISO: ", 3)
        self._draw_text_cbox_field(self, self._cbox_mosi, "MOSI: ", 4)
        self._draw_text_cbox_entry_field(self, self._cbox_nss_port, self._entry_nss_pin, "NSS: ", 5)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)


    def _draw_text_cbox_field(self, root, cbox: ttk.Combobox, name: str, row: int):
        ttk.Label(root, text=name).grid(row=row, column=0, sticky="ew", pady=(0, 10))
        cbox.grid(row=row, column=1, sticky="ew", columnspan=3, pady=(0, 10))

    def _draw_text_cbox_entry_field(self, root, cbox: ttk.Combobox, entry: ttk.Entry, name: str, row: int):
        ttk.Label(root, text=name).grid(row=row, column=0, sticky="ew", pady=(0, 10))
        cbox.grid(row=row, column=1, padx=(0, 10), sticky="ew", pady=(0, 10))  
        entry.grid(row=row, column=2, sticky="ew", pady=(0, 10))  


    def _changed_cbox_spi(self, event):
        selection = self._selections_map.get(self._val_spi.get())

        if selection is None:
            return

        self._cbox_sck["values"] = selection.sck
        self._cbox_miso["values"] = selection.miso
        self._cbox_mosi["values"] = selection.mosi

        self._val_sck.set(selection.sck[0])
        self._val_miso.set(selection.miso[0])
        self._val_mosi.set(selection.mosi[0])

# API
    @property
    def spi(self) -> str:
        return self._val_spi.get()

    @property
    def sck(self) -> str:
        return self._val_sck.get()

    @property
    def miso(self) -> str:
        return self._val_miso.get()

    @property
    def mosi(self) -> str:
        return self._val_mosi.get()


    @property
    def nss_port(self) -> str:
        return self._val_nss_port.get()

    @property
    def nss_pin(self) -> str:
        return self._val_nss_pin.get()        


# **************************************************
#  Flash Information
# **************************************************    

class FieldFlashInformation(ttk.Frame):
    class InfoType(Enum):
        Manufacturer    = 0
        MemoryType      = 1
        Capacity        = 2
        UniqueID        = 3

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent


        self._manufacturer = InformationLabel(self, "Manufacturer")
        self._manufacturer.grid(row=0, column=0, sticky="ew")

        self._memory_type = InformationLabel(self, "Memory Type")
        self._memory_type.grid(row=1, column=0, sticky="ew")

        self._capacity = InformationLabel(self, "Capacity")
        self._capacity.grid(row=2, column=0, sticky="ew")

        self._unique_id = InformationLabel(self, "Unique ID")
        self._unique_id.grid(row=3, column=0, sticky="ew")
        
        self.columnconfigure(0, weight=1)

    def SetField(self, info: InfoType, val: str):
        if info == self.InfoType.Manufacturer:
            self._manufacturer.set(val)
        elif info == self.InfoType.MemoryType:
            self._memory_type.set(val)
        elif info == self.InfoType.Capacity:
            self._capacity.set(val)
        elif info == self.InfoType.UniqueID:
            self._unique_id.set(val)                                    
        else:
            raise ValueError("Unknown info type for Flash Information!")


# **************************************************
#  Flash commands
# **************************************************    

class FieldFlashCommands(ttk.Frame):
    def __init__(self, parent, cb_ID: Callable[[None], None], cb_ERASE: Callable[[None], None], cb_STATUS: Callable[[None], None]):
        super().__init__(parent)
        self._parent = parent

        self._btn_ID = ttk.Button(self, text="ID", command=cb_ID, padding=(0, 8, 0, 8))
        self._btn_ID.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self._btn_ERASE = ttk.Button(self, text="ERASE", command=cb_ERASE, padding=(0, 8, 0, 8))
        self._btn_ERASE.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        self._btn_STATUS = ttk.Button(self, text="STATUS", command=cb_STATUS, padding=(0, 8, 0, 8))
        self._btn_STATUS.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        self.columnconfigure(0, weight=1)

    def SetState(self, state: bool):
        self._btn_ID.configure(state="normal" if state else "disabled")
        self._btn_ERASE.configure(state="normal" if state else "disabled")
        self._btn_STATUS.configure(state="normal" if state else "disabled")


# **************************************************
#  JLink commands
# **************************************************    

class FieldJLinkCommands(ttk.Frame):
    def __init__(self, parent, cb_HALT: Callable[[None], None], cb_RESET: Callable[[None], None]):
        super().__init__(parent)
        self._parent = parent

        self._halt = ttk.Button(self, text="HALT", command=cb_HALT, padding=(0, 8, 0, 8))
        self._halt.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(10, 0))
        
        self._reset = ttk.Button(self, text="RESET", command=cb_RESET, padding=(0, 8, 0, 8))
        self._reset.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(10, 0))
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

# API
    def SetStateHALT(self, state: bool):
        self._halt.configure(state="normal" if state else "disabled")

    def SetStateRESET(self, state: bool):
        self._reset.configure(state="normal" if state else "disabled")