"""
Vista (MVC) para EnergyAnalysis.
- Solo UI: define StringVar con los mismos nombres del app original.
- No hace cálculos ni validaciones.
- Expone: bind_actions(on_plot2d, on_plot3d), get_form_data(), render_contours(), render_error().
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from tkinter import messagebox


class View(ctk.CTkToplevel):
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app

        self.title('Análisis de Energía (Kleine)')
        self.geometry('560x240')
        self.grab_set()

        # === Variables (mismos nombres que en EnergyAnalysis) ===
        self.pattern = ctk.StringVar()
        self.section = ctk.StringVar(value='Transversal')
        self.type    = ctk.StringVar(value='Volumen')
        self.xmin = ctk.StringVar(value='0.0'); self.xmax = ctk.StringVar(value='10.0')
        self.ymin = ctk.StringVar(value='0.0'); self.ymax = ctk.StringVar(value='10.0')
        self.zmin = ctk.StringVar(value='0.0'); self.zmax = ctk.StringVar(value='10.0')
        self.cutoff = ctk.StringVar(value='1.0')
        self.resol  = ctk.StringVar(value='50')
        self.levels = ctk.StringVar(value='10')
        self.diameter = ctk.StringVar(value='0.0')
        self.density  = ctk.StringVar(value='0.0')
        self.K_const  = ctk.StringVar(value='200')
        self.a_const  = ctk.StringVar(value='0.9')

        self._build_ui()

    def _build_ui(self):
        list_patterns = list(getattr(self.parent_app, "designs", {}).get("charges", {"PatronDemo":{}}).keys())
        list_sections = ['Transversal', 'Longitudinal', 'Planta']
        list_types    = ['Volumen', 'Tonelaje']

        row = 0
        ctk.CTkLabel(self, text='Patrón:').grid(row=row, column=0, padx=6, pady=6, sticky='e')
        cb = ctk.CTkComboBox(self, values=list_patterns, variable=self.pattern, state='readonly', width=180)
        cb.grid(row=row, column=1, padx=6, pady=6, sticky='w')
        if list_patterns: cb.set(list_patterns[0])

        ctk.CTkLabel(self, text='Sección:').grid(row=row, column=2, padx=6, pady=6, sticky='e')
        ctk.CTkComboBox(self, values=list_sections, variable=self.section, state='readonly', width=140)\
            .grid(row=row, column=3, padx=6, pady=6, sticky='w')

        row += 1
        ctk.CTkLabel(self, text='Tipo:').grid(row=row, column=0, padx=6, pady=6, sticky='e')
        ctk.CTkComboBox(self, values=list_types, variable=self.type, state='readonly', width=180)\
            .grid(row=row, column=1, padx=6, pady=6, sticky='w')

        ctk.CTkLabel(self, text='Resolución:').grid(row=row, column=2, padx=6, pady=6, sticky='e')
        ctk.CTkEntry(self, textvariable=self.resol, width=140).grid(row=row, column=3, padx=6, pady=6, sticky='w')

        row += 1
        for i, (lab, var) in enumerate([('xmin', self.xmin), ('xmax', self.xmax), ('ymin', self.ymin), ('ymax', self.ymax)]):
            ctk.CTkLabel(self, text=lab + ':').grid(row=row + i//2, column=(i%2)*2, padx=6, pady=6, sticky='e')
            ctk.CTkEntry(self, textvariable=var, width=180).grid(row=row + i//2, column=(i%2)*2 + 1, padx=6, pady=6, sticky='w')
        row += 2

        self.btn_plot2d = ctk.CTkButton(self, text='Contornos 2D')
        self.btn_plot2d.grid(row=row, column=0, columnspan=2, pady=(10,6))

        self.btn_plot3d = ctk.CTkButton(self, text='Isosuperficie 3D')
        self.btn_plot3d.grid(row=row, column=2, columnspan=2, pady=(10,6))

    # ---------- API pública de la vista ----------
    def bind_actions(self, on_plot2d, on_plot3d):
        """El Controller inyecta aquí los callbacks (la vista no contiene lógica de negocio)."""
        self.btn_plot2d.configure(command=on_plot2d)
        self.btn_plot3d.configure(command=on_plot3d)

    def get_form_data(self):
        """Devuelve los valores de los controles como strings (el Controller hará el casteo)."""
        return {
            "pattern": self.pattern.get(),
            "section": self.section.get(),
            "type":    self.type.get(),
            "xmin":    self.xmin.get(), "xmax": self.xmax.get(),
            "ymin":    self.ymin.get(), "ymax": self.ymax.get(),
            "zmin":    self.zmin.get(), "zmax": self.zmax.get(),
            "cutoff":  self.cutoff.get(),
            "resol":   self.resol.get(),
            "levels":  self.levels.get(),
            "diameter": self.diameter.get(),
            "density":  self.density.get(),
            "K_const":  self.K_const.get(),
            "a_const":  self.a_const.get(),
        }

    def render_contours(self, meta: dict, levels: int):
        """Dibuja el contour con matplotlib (solo presentación)."""
        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        cont = ax.contourf(meta["x"], meta["y"], meta["values"], levels=levels)
        ax.set_title(meta["title"])\
        
        ax.set_xlabel(meta["xlabel"]) ; ax.set_ylabel(meta["ylabel"])
        fig.colorbar(cont).ax.set_title('u', loc='left')
        plt.show(block=False)

    def render_error(self, msg: str):
        """Muestra un mensaje de error (responsabilidad de la vista)."""
        messagebox.showerror('Análisis de Energía', msg)
