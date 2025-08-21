"""
Vista (UI) de EnergyAnalysis.

Responsabilidad:
- Definir los controles (StringVar) con los mismos nombres de parámetros.
- Armar el layout en español (similar al original).
- Exponer callbacks que el Controller registra.
- Renderizar el resultado 2D con matplotlib (contourf + colorbar).

No realiza cálculos: solo recoge entradas y muestra salidas.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt


class View(ctk.CTk):
    def __init__(self, parent_app=None):
        super().__init__()
        self.title("Análisis de Energía (Kleine)")
        self.geometry("700x480")

        # Variables de la vista (nombres preservados)
        self.pattern = ctk.StringVar(value="PatronDemo")
        self.section = ctk.StringVar(value="Transversal")
        self.type    = ctk.StringVar(value="Volumen")

        self.resol   = ctk.StringVar(value="50")
        self.xmin = ctk.StringVar(value="0.0"); self.xmax = ctk.StringVar(value="10.0")
        self.ymin = ctk.StringVar(value="0.0"); self.ymax = ctk.StringVar(value="10.0")
        self.zmin = ctk.StringVar(value="0.0"); self.zmax = ctk.StringVar(value="10.0")
        self.cutoff  = ctk.StringVar(value="1.0")
        self.levels  = ctk.StringVar(value="10")
        self.diameter= ctk.StringVar(value="0.0")
        self.density = ctk.StringVar(value="0.0")
        self.K_const = ctk.StringVar(value="200.0")
        self.a_const = ctk.StringVar(value="0.9")

        # Callbacks (los registrará el Controller)
        self.on_compute_grid = None
        self.on_compute_iso  = None

        self._build_ui()

    # ----------------------- UI ------------------------------------------------

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}
        f = ctk.CTkFrame(self)
        f.pack(fill="both", expand=True, padx=10, pady=10)

        row = 0
        # Patrón / Sección
        ctk.CTkLabel(f, text="Patrón:").grid(row=row, column=0, sticky="e", **pad)
        ctk.CTkEntry(f, textvariable=self.pattern, width=160).grid(row=row, column=1, **pad)
        ctk.CTkLabel(f, text="Sección:").grid(row=row, column=2, sticky="e", **pad)
        ctk.CTkOptionMenu(f, values=["Transversal","Longitudinal","Planta"],
                          variable=self.section, width=140).grid(row=row, column=3, **pad)

        # Tipo / Resolución
        row += 1
        ctk.CTkLabel(f, text="Tipo:").grid(row=row, column=0, sticky="e", **pad)
        ctk.CTkOptionMenu(f, values=["Volumen","Tonelaje"],
                          variable=self.type, width=140).grid(row=row, column=1, **pad)
        ctk.CTkLabel(f, text="Resolución:").grid(row=row, column=2, sticky="e", **pad)
        ctk.CTkEntry(f, textvariable=self.resol, width=100).grid(row=row, column=3, **pad)

        # xmin/xmax
        row += 1
        ctk.CTkLabel(f, text="xmin:").grid(row=row, column=0, sticky="e", **pad)
        ctk.CTkEntry(f, textvariable=self.xmin, width=100).grid(row=row, column=1, **pad)
        ctk.CTkLabel(f, text="xmax:").grid(row=row, column=2, sticky="e", **pad)
        ctk.CTkEntry(f, textvariable=self.xmax, width=100).grid(row=row, column=3, **pad)

        # ymin/ymax
        row += 1
        ctk.CTkLabel(f, text="ymin:").grid(row=row, column=0, sticky="e", **pad)
        ctk.CTkEntry(f, textvariable=self.ymin, width=100).grid(row=row, column=1, **pad)
        ctk.CTkLabel(f, text="ymax:").grid(row=row, column=2, sticky="e", **pad)
        ctk.CTkEntry(f, textvariable=self.ymax, width=100).grid(row=row, column=3, **pad)

        # zmin/zmax
        row += 1
        ctk.CTkLabel(f, text="zmin:").grid(row=row, column=0, sticky="e", **pad)
        ctk.CTkEntry(f, textvariable=self.zmin, width=100).grid(row=row, column=1, **pad)
        ctk.CTkLabel(f, text="zmax:").grid(row=row, column=2, sticky="e", **pad)
        ctk.CTkEntry(f, textvariable=self.zmax, width=100).grid(row=row, column=3, **pad)

        # Botones
        row += 1
        b1 = ctk.CTkButton(f, text="Contornos 2D",    command=self._on_btn_grid)
        b2 = ctk.CTkButton(f, text="Isosuperficie 3D", command=self._on_btn_iso)
        b1.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        b2.grid(row=row, column=2, columnspan=2, sticky="ew", **pad)

        # Área de salida textual
        row += 1
        self.output = ctk.CTkTextbox(f, height=140)
        self.output.grid(row=row, column=0, columnspan=4, sticky="nsew", padx=8, pady=(4, 0))

        for c in range(4):
            f.grid_columnconfigure(c, weight=1)
        f.grid_rowconfigure(row, weight=1)

    # ----------------------- Botones -> Controller -----------------------------

    def _on_btn_grid(self):
        if callable(self.on_compute_grid):
            self.on_compute_grid()

    def _on_btn_iso(self):
        if callable(self.on_compute_iso):
            self.on_compute_iso()

    # ----------------------- API para Controller -------------------------------

    def get_form_data(self):
        """
        Devuelve un dict de strings con los valores actuales del formulario.
        El Controller lo pasa al Model sin modificar las claves.
        """
        return {
            "pattern": self.pattern.get(),
            "section": self.section.get(),
            "type":    self.type.get(),
            "xmin": self.xmin.get(), "xmax": self.xmax.get(),
            "ymin": self.ymin.get(), "ymax": self.ymax.get(),
            "zmin": self.zmin.get(), "zmax": self.zmax.get(),
            "cutoff": self.cutoff.get(),
            "resol":  self.resol.get(),
            "levels": self.levels.get(),
            "diameter": self.diameter.get(),
            "density":  self.density.get(),
            "K_const":  self.K_const.get(),
            "a_const":  self.a_const.get(),
        }

    def show_error(self, msg):
        """Muestra un mensaje de error en el área de salida."""
        self.output.delete("1.0", "end")
        self.output.insert("end", f"[ERROR] {msg}\n")

    def show_grid_plot(self, meta):
        """
        Dibuja el contorno 2D con matplotlib.
        meta: dict con x, y, values, xlabel, ylabel, title.
        """
        X, Y, Z = meta["x"], meta["y"], meta["values"]
        plt.figure()
        cs = plt.contourf(X, Y, Z, levels=20)
        plt.colorbar(cs, label="u")
        plt.xlabel(meta["xlabel"]); plt.ylabel(meta["ylabel"])
        plt.title(meta["title"])
        plt.axis("equal"); plt.tight_layout()
        plt.show()

        # Resumen en texto
        self.output.delete("1.0", "end")
        self.output.insert("end", f"{meta['title']}\n")
        self.output.insert("end", f"malla: {X.shape}  valores: {Z.shape}\n")
        self.output.insert("end", f"ejes: {meta['xlabel']} | {meta['ylabel']}\n")

    def show_iso_info(self, meta):
        """
        Muestra un resumen textual para 3D (placeholder).
        Cuando se implemente el render 3D, se reemplaza aquí.
        """
        npts = len(meta["energy"])
        self.output.delete("1.0", "end")
        self.output.insert("end", "Isosuperficie 3D: placeholder listo (agregar render 3D).\n")
        self.output.insert("end", f"puntos: {npts}  cutoff: {meta['cutoff']}\n")

    def set_handlers(self, on_grid, on_iso):
        """Registra los handlers del Controller para los botones."""
        self.on_compute_grid = on_grid
        self.on_compute_iso  = on_iso
