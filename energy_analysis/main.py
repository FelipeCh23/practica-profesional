<<<<<<< HEAD
# Ruta al DATA.json (está en la misma carpeta)
import os

import customtkinter as ctk
from controller import EnergyAnalysisController
from model import Model
from view import EnergyAnalysisView

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # carpeta donde está main.py
DATA_PATH = os.path.join(BASE_DIR, "DATA.json")
=======
import customtkinter as ctk
from model import Model
from view import EnergyAnalysisView
from controller import EnergyAnalysisController

# Ruta al DATA.json (está en la misma carpeta)
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # carpeta donde está main.py
DATA_PATH = os.path.join(BASE_DIR, "DATA.json")    
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

<<<<<<< HEAD
    root = ctk.CTk()  # ventana principal “dummy”
    root.withdraw()  # ocultarla; la View es un Toplevel

    model = Model(DATA_PATH)  # Carga DATA.json
    view = EnergyAnalysisView(root)  # Solo UI
    ctrl = EnergyAnalysisController(model, view)  # Conecta y corre
=======
    root = ctk.CTk()          # ventana principal “dummy”
    root.withdraw()           # ocultarla; la View es un Toplevel

    model = Model(DATA_PATH)  # Carga DATA.json
    view  = EnergyAnalysisView(root)  # Solo UI
    ctrl  = EnergyAnalysisController(model, view)  # Conecta y corre
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

    view.mainloop()
