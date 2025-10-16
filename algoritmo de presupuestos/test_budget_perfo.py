"""
Budget Blast Solver - Step 1 (Drilling only, minimal)
=====================================================

Ventana de evaluación de presupuesto para PERFORACIÓN (prototipo, minimalista):
- Importa un archivo UGMM (.txt/.json) con sección "holes" y su "geometry".
- Calcula metros perforados (m) usando la misma lógica geométrica que tu app (2D).
- El usuario ingresa Cp manualmente (moneda/m).
- Compara contra un presupuesto y muestra si cumple o excede.

FÓRMULA UTILIZADA
-----------------
1) Metros perforados (2D):
   - UGMM: holes[*].geometry = [A_list, B_list], len(A_list) == len(B_list).
   - Longitud del i-ésimo barreno = distancia euclídea A[i] ↔ B[i].
     sqrt((x2 - x1)^2 + (y2 - y1)^2)
   - Metros totales = suma de las longitudes.

2) Costo de perforación:
   costo_perforación = metros * Cp
   donde Cp es el costo por metro (moneda/m), ingresado manualmente.

ARCHIVO UGMM SOPORTADO
----------------------
Se espera .txt o .json con estructura:
{
  "holes": {
    "<nombre>": {
      "diameter": <mm>,
      "geometry": [[A...],[B...]]
    },
    ...
  }
}

Requisitos:
- Python 3.8+
- Tkinter

Autor: Guillermo (prototipo para integrarlo luego a UGMM)
Fecha: 2025-05-XX
"""

from __future__ import annotations

import json
import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Iterable, List, Optional, Tuple, Union

Number = Union[int, float]


# ============================================================================
# Utilidades geométricas y de I/O (2D solamente)
# ============================================================================

def calculate_distance_2d(p1: Iterable[Number], p2: Iterable[Number]) -> float:
    """
    Calcula distancia euclídea 2D entre p1=(x1,y1) y p2=(x2,y2).

    Parameters
    ----------
    p1 : Iterable[Number]
        Punto 2D (x, y).
    p2 : Iterable[Number]
        Punto 2D (x, y).

    Returns
    -------
    float
        Distancia euclídea entre p1 y p2. Devuelve 0.0 si el formato es inválido.
    """
    if not p1 or not p2:
        return 0.0
    p1 = list(p1)
    p2 = list(p2)
    if len(p1) != 2 or len(p2) != 2:
        return 0.0
    dx = float(p2[0]) - float(p1[0])
    dy = float(p2[1]) - float(p1[1])
    return math.hypot(dx, dy)


def calculate_largo_total_hole(geometry: List[List[Iterable[Number]]]) -> float:
    """
    Calcula el total de metros perforados (2D) desde geometría UGMM.

    La geometría debe ser una lista con dos listas internas (A y B), donde:
    - A[i] y B[i] son los extremos del i-ésimo barreno (2D).
    - len(A) == len(B)

    Parameters
    ----------
    geometry : List[List[Iterable[Number]]]
        Geometría UGMM del conjunto de barrenos: [[A...], [B...]].

    Returns
    -------
    float
        Suma de longitudes A[i] ↔ B[i] en metros. 0.0 si el formato es inválido.
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
            total += calculate_distance_2d(a, b)
    return total


def load_ugmm_file(path: str) -> Dict:
    """
    Carga un archivo UGMM exportado (.txt o .json) y devuelve su contenido como dict.

    Parameters
    ----------
    path : str
        Ruta del archivo.

    Returns
    -------
    dict
        Estructura UGMM como diccionario Python.

    Raises
    ------
    FileNotFoundError
        Si el archivo no existe.
    json.JSONDecodeError
        Si el contenido no es JSON válido.
    """
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


# ============================================================================
# UI: BudgetBlastSolverStep1 (solo perforación, sin tarifario)
# ============================================================================

class BudgetBlastSolverStep1(tk.Toplevel):
    """
    Ventana de evaluación de presupuesto para perforación (sin tarifario).

    Flujo:
    1) Cargar UGMM → calcula metros perforados y lee diámetro (si existe).
    2) Ingresar Cp manualmente (moneda/m).
    3) Calcular costo = m * Cp y comparar contra presupuesto.

    Parameters
    ----------
    master : tk.Misc | None
        Ventana raíz o padre. Se acepta `None` si se ejecuta standalone.
    base_path : str
        Carpeta base (no se usa en esta versión, se deja para integración futura).
    """

    def __init__(self, master: Optional[tk.Misc] = None, base_path: str = ".") -> None:
        super().__init__(master)
        self.title("Budget Blast - Perforación (prototipo)")
        self.resizable(width=False, height=False)

        # Estado interno
        self.ugmm: Dict = {}
        self.metros: float = 0.0
        self.diametro_mm: Optional[int] = None

        # UI: encabezado
        tk.Label(
            self,
            text="Evaluación de presupuesto: PERFORACIÓN",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(pady=(10, 6), padx=10)

        # Presupuesto + moneda
        frm_budget = tk.Frame(self)
        frm_budget.pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(frm_budget, text="Presupuesto perforación:").pack(side="left")
        self.ent_presupuesto = tk.Entry(frm_budget, width=12)
        self.ent_presupuesto.insert(0, "100000.0")
        self.ent_presupuesto.pack(side="left", padx=6)

        tk.Label(frm_budget, text="Moneda:").pack(side="left", padx=(10, 2))
        self.cmb_moneda = ttk.Combobox(
            frm_budget, width=8, values=["CLP", "USD", "EUR", "JPY"], state="readonly"
        )
        self.cmb_moneda.set("CLP")
        self.cmb_moneda.pack(side="left")

        # Fuente: archivo UGMM
        grp_source = tk.LabelFrame(self, text="Datos de perforación (UGMM)")
        grp_source.pack(fill="x", padx=10, pady=(0, 6))

        frm_file = tk.Frame(grp_source)
        frm_file.pack(fill="x", pady=(6, 4))

        ttk.Button(frm_file, text="Cargar archivo UGMM...", command=self._on_load_ugmm).pack(side="left")
        self.lbl_archivo = tk.Label(frm_file, text="(ninguno)", fg="gray")
        self.lbl_archivo.pack(side="left", padx=10)

        # Datos leídos / manuales
        frm_data = tk.Frame(self)
        frm_data.pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(frm_data, text="Metros perforados [m]:").grid(row=0, column=0, sticky="w", pady=2)
        self.ent_metros = tk.Entry(frm_data, width=12)
        self.ent_metros.insert(0, "0.0")
        self.ent_metros.grid(row=0, column=1, sticky="w", padx=(6, 20))

        tk.Label(frm_data, text="Diámetro [mm]:").grid(row=0, column=2, sticky="w", pady=2)
        self.ent_diametro = tk.Entry(frm_data, width=8)
        self.ent_diametro.grid(row=0, column=3, sticky="w", padx=(6, 0))

        # Cp por metro (manual)
        grp_cp = tk.LabelFrame(self, text="Costo por metro (Cp)")
        grp_cp.pack(fill="x", padx=10, pady=(0, 6))

        frm_cp2 = tk.Frame(grp_cp)
        frm_cp2.pack(fill="x", pady=(0, 6))

        tk.Label(frm_cp2, text="Cp (moneda/m):").pack(side="left")
        self.ent_cp = tk.Entry(frm_cp2, width=12)
        self.ent_cp.insert(0, "0.0")
        self.ent_cp.pack(side="left", padx=6)

        # Botonera
        frm_btns = tk.Frame(self)
        frm_btns.pack(pady=(4, 6))
        ttk.Button(frm_btns, text="Calcular costo", command=self._on_calculate).pack(side="left", padx=6)
        ttk.Button(frm_btns, text="Sugerencias", command=self._on_suggest).pack(side="left", padx=6)

        # Resultado
        grp_out = tk.LabelFrame(self, text="Resultado")
        grp_out.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(grp_out, columns=("k", "v"), show="headings", height=7)
        self.tree.heading("k", text="Parámetro")
        self.tree.heading("v", text="Valor")
        self.tree.column("k", width=260, anchor="w")
        self.tree.column("v", width=220, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.lbl_status = tk.Label(self, text="", fg="blue")
        self.lbl_status.pack(pady=(0, 6))

    # ------------------------------------------------------------------ #
    # Acciones de UI
    # ------------------------------------------------------------------ #

    def _on_load_ugmm(self) -> None:
        """Cargar UGMM (.txt/.json), leer metros y diámetro."""
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
        self.lbl_archivo.config(text=os.path.basename(path), fg="black")

        holes = data.get("holes", {}) or {}
        if not isinstance(holes, dict) or not holes:
            self._set_status("Archivo cargado sin sección 'holes' válida.", "red")
            return

        # Tomar el primer holes
        name0 = list(holes.keys())[0]
        hole0 = holes.get(name0, {}) or {}

        # Geometría → metros perforados (2D)
        m = calculate_largo_total_hole(hole0.get("geometry", []))
        self.metros = max(float(m), 0.0)
        self.ent_metros.delete(0, tk.END)
        self.ent_metros.insert(0, f"{self.metros:.2f}")

        # Diámetro (opcional, solo informativo)
        dia = hole0.get("diameter", None)
        self.ent_diametro.delete(0, tk.END)
        if dia is not None:
            try:
                self.diametro_mm = int(float(dia))
                self.ent_diametro.insert(0, str(self.diametro_mm))
            except Exception:
                self.diametro_mm = None

        self._set_status(f"Holes: {len(holes)} | Se tomó '{name0}' para m y diámetro.", "blue")

    def _on_calculate(self) -> None:
        """
        Calcula costo de perforación y muestra resultado.

        Fórmula:
        costo_perforación = metros * Cp
        """
        metros = self._get_metros()
        cp = self._get_cp()
        presupuesto = self._get_presupuesto()
        moneda = self.cmb_moneda.get().strip() or "CLP"

        costo = metros * cp
        margen = presupuesto - costo

        # Salida en tabla
        self._clear_tree()
        self._add_row("Moneda", moneda)
        self._add_row("Metros perforados [m]", f"{metros:.2f}")
        self._add_row("Cp (moneda/m)", f"{cp:.4f}")
        self._add_row("Costo perforación", f"{costo:.2f} {moneda}")
        self._add_row("Presupuesto", f"{presupuesto:.2f} {moneda}")
        self._add_row("Margen", f"{margen:.2f} {moneda}")

        if costo <= presupuesto:
            self._set_status("✅ Cumple presupuesto (solo perforación).", "green")
        else:
            self._set_status("❌ EXCEDE presupuesto (solo perforación).", "red")

    def _on_suggest(self) -> None:
        """
        Propone un ajuste simple para cumplir presupuesto:
        - Reducir metros manteniendo Cp actual.
        """
        metros = self._get_metros()
        cp = self._get_cp()
        presupuesto = self._get_presupuesto()
        moneda = self.cmb_moneda.get().strip() or "CLP"

        if metros <= 0.0 or cp <= 0.0:
            messagebox.showinfo("Sugerencias", "Ingresa metros y Cp válidos.")
            return

        costo = metros * cp
        if costo <= presupuesto:
            messagebox.showinfo(
                "Sugerencias",
                "Ya cumples el presupuesto en perforación.\n"
                "Puedes aumentar metros si el diseño lo requiere."
            )
            return

        m_max = presupuesto / cp
        messagebox.showinfo(
            "Sugerencias",
            "Sugerencia (solo perforación):\n"
            f"- Reducir metros a ≤ {m_max:.2f} m manteniendo Cp actual ({cp:.4f} {moneda}/m)."
        )

    # ------------------------------------------------------------------ #
    # Helpers (UI y cálculo interno)
    # ------------------------------------------------------------------ #

    def _get_metros(self) -> float:
        """Lee los metros perforados desde la UI."""
        try:
            m = float(self.ent_metros.get())
            return max(m, 0.0)
        except Exception:
            return 0.0

    def _get_cp(self) -> float:
        """Lee Cp (moneda/m) desde la UI."""
        try:
            c = float(self.ent_cp.get())
            return max(c, 0.0)
        except Exception:
            return 0.0

    def _get_presupuesto(self) -> float:
        """Lee el presupuesto (moneda) desde la UI."""
        try:
            b = float(self.ent_presupuesto.get())
            return max(b, 0.0)
        except Exception:
            return 0.0

    def _clear_tree(self) -> None:
        """Limpia la tabla de resultados."""
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def _add_row(self, key: str, value: str) -> None:
        """Inserta una fila (clave, valor) en la tabla de resultados."""
        self.tree.insert("", "end", values=(key, value))

    def _set_status(self, text: str, color: str = "blue") -> None:
        """Actualiza la etiqueta de estado inferior."""
        self.lbl_status.config(text=text, fg=color)


# ============================================================================
# Main 
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # ocultar raíz
    app = BudgetBlastSolverStep1(master=root, base_path=".")
    app.mainloop()
