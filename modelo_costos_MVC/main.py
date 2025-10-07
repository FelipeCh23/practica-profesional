# main.py
import os
import tkinter as tk

from model.costos_model import CostosModel
from view.costos_view import CostsAnalysisis
from controller.costos_controller import CostosController

def main():
    # base_path: carpeta del proyecto (donde están /Modelo, /databases, etc.)
    base_path = os.path.dirname(os.path.abspath(__file__))

    # 1) crear model
    model = CostosModel(base_path)

    # 2) crear root y view (sin arrancar aquí)
    root = tk.Tk()
    view = CostsAnalysisis(root, controller=None, model=model)

    # 3) crear controller y enchufarlo a la view
    controller = CostosController(model, view)
    view.controller = controller

    # 4) arrancar desde el controller (ya no en la view)
    controller.start()

    view.pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
