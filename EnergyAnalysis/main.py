from model import EnergyModel
from view import EnergyView
from controller import EnergyController

def main():
    model = EnergyModel()
    view = EnergyView(None)  # Se asignará el controlador luego
    controller = EnergyController(model, view)
    view.controller = controller  # inyectar el controlador en la vista
    view.mainloop()

if __name__ == "__main__":
    main()
