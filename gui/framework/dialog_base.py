import customtkinter as ctk

class DialogHandler(ctk.CTkToplevel):
    def __init__(self, master=None, app_modes=None):
        super().__init__(master)
        self.app_modes = app_modes
    
    def configure_window(self, title=None, resizable=None, width=None, height=None):
        if title: self.title(title)
        if width and height: self.geometry(f"{width}x{height}")
        if resizable is not None: self.resizable(resizable, resizable)
