"""
Budget Blast – GUI con pestañas (Perforación / Explosivos / Detonadores)
========================================================================

Propósito
---------
Prototipo de evaluación de presupuesto de una voladura subterránea,
con separación por categorías de costo y lectura opcional desde
un archivo UGMM (.txt/.json).

Cálculos implementados (sólidos y trazables):
- Perforación: C_perf = m_perforados * Cp            [moneda]
- Explosivos:  C_expl = masa_explosivo * Ce          [moneda]
               masa_explosivo = volumen * densidad
               volumen = (pi/4) * (D_carga_m)^2 * L_cargada   [m^3]
               densidad [kg/m^3] (si viene g/cc => *1000)
- Detonadores: C_det = N_detonadores * Cd            [moneda]

Extracción de UGMM (si existen esas secciones):
- holes:   calcula metros desde geometry [[A...],[B...]] sumando |A[i]-B[i]|
- charges: autollenado de D_carga, densidad y longitud cargada
           (se asume geometry también con dos listas A/B de puntos por tiro)
- blasts:  no se usa aún; los detonadores se calculan con #tiros * primas.

Notas importantes
-----------------
- No usa “tarifario”. Todos los precios se introducen en la interfaz.
- Si el archivo UGMM no trae algún dato, la pestaña permite editarlo a mano.
- Todo está separado por pestañas para que sea fácil de integrar luego en UGMM.

"""

from __future__ import annotations

import json
import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Iterable, List, Optional, Tuple, Union

Number = Union[int, float]


# ---------------------------------------------------------------------------
# Utilidades geométricas y de IO
# ---------------------------------------------------------------------------

def calculate_distance(p1: Iterable[Number], p2: Iterable[Number]) -> float:
    """Distancia euclídea en 2D entre dos puntos (x, y).

    Si el formato es inválido, devuelve 0.0.
    """
    if not p1 or not p2:
        return 0.0
    p1 = list(p1)
    p2 = list(p2)
    if len(p1) >= 2 and len(p2) >= 2:
        dx = float(p2[0]) - float(p1[0])
        dy = float(p2[1]) - float(p1[1])
        return math.hypot(dx, dy)
    return 0.0


def calculate_largo_total_hole(geometry: List[List[Iterable[Number]]]) -> float:
    """Suma de longitudes |A[i]-B[i]| a partir de geometry = [[A...], [B...]] (2D).

    - Espera dos listas internas A y B con igual cantidad de puntos.
    - Si el formato es inválido, retorna 0.0.
    """
    if (
        not geometry
        or len(geometry) != 2
        or not geometry[0]
        or not geometry[1]
        or len(geometry[0]) != len(geometry[1])
    ):
        return 0.0

    total = 0.0
    a_list, b_list = geometry[0], geometry[1]
    for a, b in zip(a_list, b_list):
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            total += calculate_distance(a, b)
    return total


def load_ugmm_file(path: str) -> Dict:
    """Carga un archivo UGMM (.txt/.json) a dict."""
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Pestaña: Perforación
# ---------------------------------------------------------------------------

class DrillTab(tk.Frame):
    """Pestaña de Perforación: metros, Cp y costo de perforación."""

    def __init__(self, master: tk.Misc, on_change_callback) -> None:
        super().__init__(master)
        self.on_change = on_change_callback  # para avisar al resumen

        # Estado
        self.meters: float = 0.0
        self.diameter_mm: Optional[int] = None
        self.price_cp: float = 0.0

        # Layout
        frm = tk.Frame(self)
        frm.pack(fill="x", padx=10, pady=8)

        tk.Label(frm, text="Metros perforados [m]:").grid(row=0, column=0, sticky="w")
        self.ent_m = tk.Entry(frm, width=12)
        self.ent_m.insert(0, "0.0")
        self.ent_m.grid(row=0, column=1, sticky="w", padx=(6, 20))

        tk.Label(frm, text="Diámetro [mm]:").grid(row=0, column=2, sticky="w")
        self.ent_d = tk.Entry(frm, width=8)
        self.ent_d.grid(row=0, column=3, sticky="w", padx=(6, 0))

        tk.Label(frm, text="Cp (moneda/m):").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.ent_cp = tk.Entry(frm, width=12)
        self.ent_cp.insert(0, "0.0")
        self.ent_cp.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(8, 0))

        # eventos para refrescar resumen cuando cambian entradas
        for w in (self.ent_m, self.ent_d, self.ent_cp):
            w.bind("<KeyRelease>", lambda _e: self.on_change())

    # API para leer/llenar desde UGMM
    def fill_from_holes(self, holes: Dict) -> None:
        """Toma el primer 'holes' y autollenar metros y diámetro."""
        if not holes:
            return
        name0 = list(holes.keys())[0]
        h0 = holes.get(name0, {}) or {}
        m = calculate_largo_total_hole(h0.get("geometry", []))
        self.ent_m.delete(0, tk.END)
        self.ent_m.insert(0, f"{m:.2f}")

        dia = h0.get("diameter", None)
        self.ent_d.delete(0, tk.END)
        if dia is not None:
            try:
                self.ent_d.insert(0, str(int(float(dia))))
            except Exception:
                pass

    # Lectura
    def get_meters(self) -> float:
        try:
            return max(float(self.ent_m.get()), 0.0)
        except Exception:
            return 0.0

    def get_cp(self) -> float:
        try:
            return max(float(self.ent_cp.get()), 0.0)
        except Exception:
            return 0.0

    def cost(self) -> float:
        return self.get_meters() * self.get_cp()


# ---------------------------------------------------------------------------
# Pestaña: Explosivos
# ---------------------------------------------------------------------------

class ExplosiveTab(tk.Frame):
    """Pestaña de Explosivos: longitud cargada, diámetro de carga, densidad y costo."""

    def __init__(self, master: tk.Misc, on_change_callback) -> None:
        super().__init__(master)
        self.on_change = on_change_callback

        frm = tk.Frame(self)
        frm.pack(fill="x", padx=10, pady=8)

        tk.Label(frm, text="Longitud cargada [m]:").grid(row=0, column=0, sticky="w")
        self.ent_len = tk.Entry(frm, width=12)
        self.ent_len.insert(0, "0.0")
        self.ent_len.grid(row=0, column=1, sticky="w", padx=(6, 20))

        tk.Label(frm, text="Diámetro de carga [mm]:").grid(row=0, column=2, sticky="w")
        self.ent_d = tk.Entry(frm, width=8)
        self.ent_d.grid(row=0, column=3, sticky="w", padx=(6, 0))

        tk.Label(frm, text="Densidad del explosivo:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.cmb_d_unit = ttk.Combobox(frm, width=10, state="readonly",
                                       values=["kg/m3", "g/cc"])
        self.cmb_d_unit.set("g/cc")
        self.cmb_d_unit.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(8, 0))

        self.ent_density = tk.Entry(frm, width=10)
        self.ent_density.insert(0, "1.10")  # típico emulsión
        self.ent_density.grid(row=1, column=2, sticky="w", padx=(6, 0), pady=(8, 0))

        tk.Label(frm, text="Ce (precio explosivo) [moneda/kg]:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.ent_ce = tk.Entry(frm, width=12)
        self.ent_ce.insert(0, "0.0")
        self.ent_ce.grid(row=2, column=1, sticky="w", padx=(6, 0), pady=(8, 0))

        for w in (self.ent_len, self.ent_d, self.cmb_d_unit, self.ent_density, self.ent_ce):
            if hasattr(w, "bind"):
                w.bind("<KeyRelease>", lambda _e: self.on_change())
        self.cmb_d_unit.bind("<<ComboboxSelected>>", lambda _e: self.on_change())

    def fill_from_charges(self, charges: Dict) -> None:
        """Autollenar si hay 'charges' en el UGMM."""
        if not charges:
            return
        name0 = list(charges.keys())[0]
        c0 = charges.get(name0, {}) or {}

        # Longitud cargada desde geometry [[A...],[B...]]
        L = calculate_largo_total_hole(c0.get("geometry", []))
        self.ent_len.delete(0, tk.END)
        self.ent_len.insert(0, f"{L:.2f}")

        # Diámetro de carga
        d = c0.get("diameter", None)
        self.ent_d.delete(0, tk.END)
        if d is not None:
            try:
                self.ent_d.insert(0, str(int(float(d))))
            except Exception:
                pass

        # Densidad desde explosivo.density (asumimos viene en g/cc)
        exp = c0.get("explosive", {}) or {}
        dens = exp.get("density", None)
        if isinstance(dens, (int, float)):
            self.cmb_d_unit.set("g/cc")
            self.ent_density.delete(0, tk.END)
            self.ent_density.insert(0, f"{float(dens):.3f}")

    # Lecturas y cálculos
    def get_len(self) -> float:
        try:
            return max(float(self.ent_len.get()), 0.0)
        except Exception:
            return 0.0

    def get_diameter_m(self) -> float:
        """Devuelve el diámetro de carga en metros."""
        try:
            return max(float(self.ent_d.get()) / 1000.0, 0.0)
        except Exception:
            return 0.0

    def get_density_kg_m3(self) -> float:
        """Convierte densidad a kg/m3 según unidad seleccionada."""
        try:
            val = float(self.ent_density.get())
        except Exception:
            return 0.0
        unit = self.cmb_d_unit.get()
        if unit == "g/cc":
            return max(val * 1000.0, 0.0)
        return max(val, 0.0)

    def get_ce(self) -> float:
        try:
            return max(float(self.ent_ce.get()), 0.0)
        except Exception:
            return 0.0

    def mass_kg(self) -> float:
        """Masa = volumen_cilindro * densidad."""
        d = self.get_diameter_m()
        L = self.get_len()
        rho = self.get_density_kg_m3()
        volume = (math.pi / 4.0) * d * d * L  # m^3
        return volume * rho  # kg

    def cost(self) -> float:
        return self.mass_kg() * self.get_ce()


# ---------------------------------------------------------------------------
# Pestaña: Detonadores
# ---------------------------------------------------------------------------

class DetonatorTab(tk.Frame):
    """Pestaña de Detonadores: unidades, primas por tiro, costo."""

    def __init__(self, master: tk.Misc, on_change_callback) -> None:
        super().__init__(master)
        self.on_change = on_change_callback

        frm = tk.Frame(self)
        frm.pack(fill="x", padx=10, pady=8)

        tk.Label(frm, text="Número de detonadores (N):").grid(row=0, column=0, sticky="w")
        self.ent_N = tk.Entry(frm, width=12)
        self.ent_N.insert(0, "0")
        self.ent_N.grid(row=0, column=1, sticky="w", padx=(6, 20))

        tk.Label(frm, text="Cd (moneda/unidad):").grid(row=0, column=2, sticky="w")
        self.ent_Cd = tk.Entry(frm, width=10)
        self.ent_Cd.insert(0, "0.0")
        self.ent_Cd.grid(row=0, column=3, sticky="w", padx=(6, 0))

        for w in (self.ent_N, self.ent_Cd):
            w.bind("<KeyRelease>", lambda _e: self.on_change())

    def prime_from_holes(self, holes: Dict, primas_por_tiro: int = 1) -> None:
        """Autollenar N = #tiros * primas_por_tiro a partir de holes."""
        if not holes:
            return
        name0 = list(holes.keys())[0]
        h0 = holes.get(name0, {}) or {}
        geo = h0.get("geometry", [])
        n_tiros = 0
        if isinstance(geo, list) and len(geo) == 2 and len(geo[0]) == len(geo[1]):
            n_tiros = len(geo[0])
        N = max(n_tiros * max(int(primas_por_tiro), 1), 0)
        self.ent_N.delete(0, tk.END)
        self.ent_N.insert(0, str(N))

    def get_N(self) -> int:
        try:
            return max(int(float(self.ent_N.get())), 0)
        except Exception:
            return 0

    def get_Cd(self) -> float:
        try:
            return max(float(self.ent_Cd.get()), 0.0)
        except Exception:
            return 0.0

    def cost(self) -> float:
        return self.get_N() * self.get_Cd()


# ---------------------------------------------------------------------------
# Ventana principal con pestañas y resumen
# ---------------------------------------------------------------------------

class BudgetBlastGUI(tk.Toplevel):
    """Ventana principal con pestañas y resumen de costo total."""

    def __init__(self, master: Optional[tk.Misc] = None, base_path: str = ".") -> None:
        super().__init__(master)
        self.title("Budget Blast - Prototipo")
        self.resizable(False, False)

        self.base_path = os.path.abspath(base_path)
        self.ugmm: Dict = {}

        # Presupuesto + moneda
        header = tk.Frame(self)
        header.pack(fill="x", padx=10, pady=(10, 6))
        tk.Label(header, text="Presupuesto total:").pack(side="left")
        self.ent_budget = tk.Entry(header, width=14)
        self.ent_budget.insert(0, "100000.0")
        self.ent_budget.pack(side="left", padx=(6, 12))
        tk.Label(header, text="Moneda:").pack(side="left")
        self.cmb_currency = ttk.Combobox(header, width=8, state="readonly",
                                         values=["CLP", "USD", "EUR"])
        self.cmb_currency.set("CLP")
        self.cmb_currency.pack(side="left")

        # Carga de archivo UGMM
        grp_src = tk.LabelFrame(self, text="Archivo UGMM")
        grp_src.pack(fill="x", padx=10, pady=(0, 6))
        frm_file = tk.Frame(grp_src); frm_file.pack(fill="x", pady=6)
        ttk.Button(frm_file, text="Cargar archivo UGMM...",
                   command=self._on_load_ugmm).pack(side="left")
        self.lbl_file = tk.Label(frm_file, text="(ninguno)", fg="gray")
        self.lbl_file.pack(side="left", padx=10)

        # Notebook de pestañas
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.drill_tab = DrillTab(nb, self._refresh_summary)
        self.expl_tab = ExplosiveTab(nb, self._refresh_summary)
        self.det_tab = DetonatorTab(nb, self._refresh_summary)

        nb.add(self.drill_tab, text="Perforación")
        nb.add(self.expl_tab, text="Explosivos")
        nb.add(self.det_tab, text="Detonadores")

        # Resumen
        grp_sum = tk.LabelFrame(self, text="Resumen")
        grp_sum.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(grp_sum, columns=("k", "v"), show="headings", height=7)
        self.tree.heading("k", text="Concepto")
        self.tree.heading("v", text="Valor")
        self.tree.column("k", width=260, anchor="w")
        self.tree.column("v", width=220, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.lbl_status = tk.Label(self, text="", fg="blue")
        self.lbl_status.pack(pady=(0, 8))

        # Primer refresco
        self._refresh_summary()

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #

    def _on_load_ugmm(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar UGMM (.txt/.json)",
            filetypes=[("UGMM JSON", "*.txt;*.json"), ("Todos", "*.*")]
        )
        if not path:
            return
        try:
            data = load_ugmm_file(path)
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{exc}")
            return

        self.ugmm = data
        self.lbl_file.config(text=os.path.basename(path), fg="black")

        holes = data.get("holes", {}) or {}
        charges = data.get("charges", {}) or {}

        # Autollenar Perforación
        self.drill_tab.fill_from_holes(holes)

        # Autollenar Explosivos (si hay)
        self.expl_tab.fill_from_charges(charges)

        # Autollenar Detonadores: N = #tiros * 1 (editable)
        self.det_tab.prime_from_holes(holes, primas_por_tiro=1)

        self._refresh_summary()

    # ------------------------------------------------------------------ #
    # Resumen
    # ------------------------------------------------------------------ #

    def _get_budget(self) -> float:
        try:
            return max(float(self.ent_budget.get()), 0.0)
        except Exception:
            return 0.0

    def _clear_tree(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def _add_row(self, k: str, v: str) -> None:
        self.tree.insert("", "end", values=(k, v))

    def _refresh_summary(self) -> None:
        """Recalcula todos los costos y actualiza la tabla de resumen."""
        currency = self.cmb_currency.get() or "CLP"

        c_perf = self.drill_tab.cost()
        c_expl = self.expl_tab.cost()
        c_det = self.det_tab.cost()
        c_total = c_perf + c_expl + c_det

        self._clear_tree()
        self._add_row("Costo perforación", f"{c_perf:.2f} {currency}")
        self._add_row("Costo explosivos", f"{c_expl:.2f} {currency}")
        self._add_row("Costo detonadores", f"{c_det:.2f} {currency}")
        self._add_row("—", "—")
        self._add_row("Costo TOTAL", f"{c_total:.2f} {currency}")
        self._add_row("Presupuesto", f"{self._get_budget():.2f} {currency}")
        self._add_row("Margen", f"{(self._get_budget() - c_total):.2f} {currency}")

        if c_total <= self._get_budget():
            self.lbl_status.config(text="✅ Cumple presupuesto.", fg="green")
        else:
            self.lbl_status.config(text="❌ EXCEDE presupuesto.", fg="red")


# ---------------------------------------------------------------------------
# Ejecutar standalone
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = BudgetBlastGUI(master=root, base_path=".")
    app.mainloop()
