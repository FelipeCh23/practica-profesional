"""
Punto de entrada de EnergyAnalysis (demo).

- Crea un 'parent_app' mínimo con estructuras similares a appRing.designs,
  para permitir ejecutar y validar el MVC sin la app real.
"""

import customtkinter as ctk
from model import Model
from view import View
from controller import Controller


class _ParentAppStub:
    """Simulación mínima de appRing para pruebas locales."""
    def __init__(self):
        self.designs = {
            "charges": {
                "PatronDemo": {
                    "holes": "h1", "drift": "d1", "stope": "s1",
                    "lines": [((2,0,2),(2,4,2)), ((5,0,2),(5,4,2)), ((8,0,2),(8,4,2))],
                    "explosive": {"density": 0.85, "VOD": 4500, "RWS": 100},
                }
            },
            "stopes": {"s1": {"geometry": [(0,0),(10,0),(10,4),(0,4)], "rock": {"density": 2700}}},
            "drifts": {"d1": {"geometry": [(0,-1),(10,-1),(10,0),(0,0)]}},
        }


def main():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    parent = _ParentAppStub()
    model  = Model(parent_app=parent)
    view   = View(parent_app=parent)
    Controller(model, view, parent_app=parent)

    view.mainloop()


if __name__ == "__main__":
    main()
