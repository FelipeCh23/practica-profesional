
# main_vibration

# Arranca la app y conecta MVC de Vibrations.

# main_vibration.py
import os
import customtkinter as ctk
from model_vibration import Model
from view_vibration import VibrationView
from controller_vibration import VibrationController

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "DATA.json")

if __name__ == "__main__":
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.withdraw()

    model = Model(DATA_PATH)   # ahora sí encuentra DATA.json
    view  = VibrationView(root)
    ctrl  = VibrationController(model, view)

    view.mainloop()
