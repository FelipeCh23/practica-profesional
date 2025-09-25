# main.py
import os

import customtkinter as ctk
from controller_vibration import VibrationAnalysisController
from model_vibration import Model
from view_vibration import VibrationAnalysisView

if __name__ == "__main__":
    DATA_PATH = os.path.join(os.path.dirname(__file__), "DATA.json")

    root = ctk.CTk()
    root.withdraw()  # <<< oculta la ventana raíz para que SOLO se vea el Toplevel

    model = Model(DATA_PATH)
    view = VibrationAnalysisView(root)
    ctrl = VibrationAnalysisController(model, view)

    # cuando cierres el Toplevel, cierra también la raíz “invisible”
    view.protocol("WM_DELETE_WINDOW", lambda: (view.destroy(), root.destroy()))

    root.mainloop()
