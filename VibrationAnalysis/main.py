# main.py
import os
<<<<<<< HEAD

import customtkinter as ctk
from controller_vibration import VibrationAnalysisController
from model_vibration import Model
from view_vibration import VibrationAnalysisView
=======
import customtkinter as ctk
from model_vibration import Model
from view_vibration import VibrationAnalysisView
from controller_vibration import VibrationAnalysisController
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

if __name__ == "__main__":
    DATA_PATH = os.path.join(os.path.dirname(__file__), "DATA.json")

    root = ctk.CTk()
    root.withdraw()  # <<< oculta la ventana raíz para que SOLO se vea el Toplevel

    model = Model(DATA_PATH)
<<<<<<< HEAD
    view = VibrationAnalysisView(root)
    ctrl = VibrationAnalysisController(model, view)
=======
    view  = VibrationAnalysisView(root)
    ctrl  = VibrationAnalysisController(model, view)
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

    # cuando cierres el Toplevel, cierra también la raíz “invisible”
    view.protocol("WM_DELETE_WINDOW", lambda: (view.destroy(), root.destroy()))

    root.mainloop()
