"""
Budget Blast – Evaluación de presupuesto por pestañas
=====================================================

Propósito
---------
Prototipo para evaluar el costo total de una tronadura subterránea separando
en tres categorías: Perforación, Explosivos y Detonadores. Permite cargar
un archivo UGMM (.txt/.json) para autollenar campos o ingresar todo a mano.

Costos calculados
-----------------
- Perforación:  C_perf = m_perforados * Cp
- Explosivos:   C_expl = masa_explosivo * Ce
                masa = volumen * densidad
                volumen = (π/4) * (D_carga_m)^2 * L_cargada
- Detonadores:  C_det = N_detonadores * Cd

Notas
-----
- Unidades esperadas: coordenadas (m), diámetros (mm), densidad (g/cc o kg/m3),
  precios en “moneda” configurable.
- UGMM esperado con secciones: "holes" (perforación) y/o "charges" (cargas).
"""


from __future__ import annotations

import json
import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Iterable, List, Optional, Union

# Definición de tipo para claridad en las funciones.
Number = Union[int, float]


# ---------------------------------------------------------------------------
# SECCIÓN 1: Funciones de Utilidad
# ---------------------------------------------------------------------------

def calculate_2d_distance(point1: Iterable[Number], point2: Iterable[Number]) -> float:
    """
    Calcula la distancia euclidiana entre dos puntos 2D.

    Args:
        point1 (Iterable[Number]): Punto inicial [x1, y1] en metros.
        point2 (Iterable[Number]): Punto final [x2, y2] en metros.

    Returns:
        float: Longitud del segmento en metros (0.0 si no es válido).
    """
    if not point1 or not point2:
        return 0.0
    
    p1 = list(point1)
    p2 = list(point2)
    
    if len(p1) >= 2 and len(p2) >= 2:
        dx = float(p2[0]) - float(p1[0])
        dy = float(p2[1]) - float(p1[1])
        return math.hypot(dx, dy)
    return 0.0


def get_total_length_from_geometry(geometry: List[List[Iterable[Number]]]) -> float:
    """
    Suma las longitudes Ai<->Bi para una geometría de perforación/carga.

    Args:
        geometry (list): Dos listas internas (A y B) con coordenadas 2D en metros.

    Returns:
        float: Metros totales (sumatoria de distancias Ai<->Bi).
    """
    if (
        not geometry or len(geometry) != 2 or not geometry[0] or 
        not geometry[1] or len(geometry[0]) != len(geometry[1])
    ):
        return 0.0

    total_length = 0.0
    start_points, end_points = geometry[0], geometry[1]
    for start, end in zip(start_points, end_points):
        total_length += calculate_2d_distance(start, end)
    return total_length


def load_ugmm_file(path: str) -> Dict:
    """
    Lee un archivo UGMM (.txt/.json) y devuelve su contenido como dict.

    Args:
        path (str): Ruta al archivo.

    Returns:
        dict: Estructura UGMM cargada.
    """
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)

# ---------------------------------------------------------------------------
# SECCIÓN 2: Pestañas de la Interfaz
# ---------------------------------------------------------------------------

class DrillingTab(tk.Frame):
    """Pestaña para gestionar los costos de perforación."""

    def __init__(self, master: tk.Misc, on_change: callable) -> None:
        """
        Inicializa la UI de la pestaña de Perforación.

        Args:
            master (tk.Misc): Contenedor padre (el Notebook).
            on_change (callable): Función a llamar cuando un valor cambia.
        """
        super().__init__(master)
        self.on_change = on_change

        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10, pady=8)

        tk.Label(frame, text="Metros perforados [m]:").grid(row=0, column=0, sticky="w")
        self.entry_meters = tk.Entry(frame, width=12)
        self.entry_meters.insert(0, "0.0")
        self.entry_meters.grid(row=0, column=1, sticky="w", padx=(6, 20))

        tk.Label(frame, text="Diámetro perforación [mm]:").grid(row=0, column=2, sticky="w")
        self.entry_diameter = tk.Entry(frame, width=10)
        self.entry_diameter.grid(row=0, column=3, sticky="w", padx=(6, 0))

        tk.Label(frame, text="Costo por metro [moneda/m]:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.entry_cost_per_meter = tk.Entry(frame, width=12)
        self.entry_cost_per_meter.insert(0, "0.0")
        self.entry_cost_per_meter.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(8, 0))

        for widget in (self.entry_meters, self.entry_diameter, self.entry_cost_per_meter):
            widget.bind("<KeyRelease>", lambda event: self.on_change())

    def populate_from_holes(self, holes_data: Dict) -> None:
        """
        Autocompleta los campos desde la sección "holes" de un UGMM.

        Args:
            holes_data (dict): Diccionario que contiene la clave "geometry" y "diameter".
        """
        if not holes_data:
            return
        
        first_hole_name = next(iter(holes_data))
        hole = holes_data.get(first_hole_name, {}) or {}

        meters = get_total_length_from_geometry(hole.get("geometry", []))
        self.entry_meters.delete(0, tk.END)
        self.entry_meters.insert(0, f"{meters:.2f}")

        diameter = hole.get("diameter")
        self.entry_diameter.delete(0, tk.END)
        if diameter is not None:
            try:
                self.entry_diameter.insert(0, str(int(float(diameter))))
            except (ValueError, TypeError):
                pass

    def get_meters(self) -> float:
        """Obtiene y valida los metros perforados (m) desde la UI."""
        try:
            return max(float(self.entry_meters.get()), 0.0)
        except ValueError:
            return 0.0

    def get_cost_per_meter(self) -> float:
        """Obtiene y valida el costo por metro (moneda/m) desde la UI."""
        try:
            return max(float(self.entry_cost_per_meter.get()), 0.0)
        except ValueError:
            return 0.0

    def calculate_cost(self) -> float:
        """Calcula el costo total de perforación."""
        return self.get_meters() * self.get_cost_per_meter()


class ExplosivesTab(tk.Frame):
    """Pestaña para gestionar los costos de explosivos."""

    def __init__(self, master: tk.Misc, on_change: callable) -> None:
        """
        Inicializa la UI de la pestaña de Explosivos.

        Args:
            master (tk.Misc): Contenedor padre (el Notebook).
            on_change (callable): Función a llamar cuando un valor cambia.
        """
        super().__init__(master)
        self.on_change = on_change

        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10, pady=8)

        tk.Label(frame, text="Longitud cargada [m]:").grid(row=0, column=0, sticky="w")
        self.entry_length = tk.Entry(frame, width=12)
        self.entry_length.insert(0, "0.0")
        self.entry_length.grid(row=0, column=1, sticky="w", padx=(6, 20))

        tk.Label(frame, text="Diámetro de carga [mm]:").grid(row=0, column=2, sticky="w")
        self.entry_diameter = tk.Entry(frame, width=10)
        self.entry_diameter.grid(row=0, column=3, sticky="w", padx=(6, 0))

        tk.Label(frame, text="Densidad explosivo:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.combo_density_unit = ttk.Combobox(frame, width=10, state="readonly", values=["kg/m³", "g/cc"])
        self.combo_density_unit.set("g/cc")
        self.combo_density_unit.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(8, 0))

        self.entry_density = tk.Entry(frame, width=10)
        self.entry_density.insert(0, "1.10")
        self.entry_density.grid(row=1, column=2, sticky="w", padx=(6, 0), pady=(8, 0))

        tk.Label(frame, text="Costo por kg [moneda/kg]:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.entry_cost_per_kg = tk.Entry(frame, width=12)
        self.entry_cost_per_kg.insert(0, "0.0")
        self.entry_cost_per_kg.grid(row=2, column=1, sticky="w", padx=(6, 0), pady=(8, 0))

        for widget in (self.entry_length, self.entry_diameter, self.entry_density, self.entry_cost_per_kg):
            widget.bind("<KeyRelease>", lambda event: self.on_change())
        self.combo_density_unit.bind("<<ComboboxSelected>>", lambda event: self.on_change())

    def populate_from_charges(self, charges_data: Dict) -> None:
        """
        Autocompleta los campos desde la sección "charges" de un UGMM.

        Args:
            charges_data (dict): Diccionario que contiene "geometry", "diameter" y "explosive".
        """
        if not charges_data:
            return

        first_charge_name = next(iter(charges_data))
        charge = charges_data.get(first_charge_name, {}) or {}

        length = get_total_length_from_geometry(charge.get("geometry", []))
        self.entry_length.delete(0, tk.END)
        self.entry_length.insert(0, f"{length:.2f}")

        diameter = charge.get("diameter")
        self.entry_diameter.delete(0, tk.END)
        if diameter is not None:
            try:
                self.entry_diameter.insert(0, str(int(float(diameter))))
            except (ValueError, TypeError):
                pass
        
        explosive = charge.get("explosive", {}) or {}
        density = explosive.get("density")
        if isinstance(density, (int, float)):
            self.combo_density_unit.set("g/cc")
            self.entry_density.delete(0, tk.END)
            self.entry_density.insert(0, f"{float(density):.3f}")

    def get_charged_length_m(self) -> float:
        """Obtiene y valida la longitud de la columna de explosivo (m)."""
        try:
            return max(float(self.entry_length.get()), 0.0)
        except ValueError:
            return 0.0

    def get_charge_diameter_m(self) -> float:
        """Obtiene el diámetro de carga y lo convierte a metros."""
        try:
            return max(float(self.entry_diameter.get()) / 1000.0, 0.0)
        except ValueError:
            return 0.0

    def get_density_kg_m3(self) -> float:
        """Obtiene la densidad y la convierte a kg/m³, si es necesario."""
        try:
            value = float(self.entry_density.get())
        except ValueError:
            return 0.0
        
        if self.combo_density_unit.get() == "g/cc":
            return max(value * 1000.0, 0.0)
        return max(value, 0.0)

    def get_cost_per_kg(self) -> float:
        """Obtiene y valida el costo del explosivo (moneda/kg)."""
        try:
            return max(float(self.entry_cost_per_kg.get()), 0.0)
        except ValueError:
            return 0.0

    def calculate_mass_kg(self) -> float:
        """Calcula la masa total de explosivo (kg) usando la fórmula del cilindro."""
        diameter = self.get_charge_diameter_m()
        length = self.get_charged_length_m()
        density = self.get_density_kg_m3()
        
        volume = (math.pi / 4.0) * (diameter ** 2) * length
        return volume * density

    def calculate_cost(self) -> float:
        """Calcula el costo total del explosivo."""
        return self.calculate_mass_kg() * self.get_cost_per_kg()


class DetonatorsTab(tk.Frame):
    """Pestaña para gestionar los costos de detonadores."""

    def __init__(self, master: tk.Misc, on_change: callable) -> None:
        """
        Inicializa la UI de la pestaña de Detonadores.

        Args:
            master (tk.Misc): Contenedor padre (el Notebook).
            on_change (callable): Función a llamar cuando un valor cambia.
        """
        super().__init__(master)
        self.on_change = on_change

        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10, pady=8)

        tk.Label(frame, text="Número de detonadores:").grid(row=0, column=0, sticky="w")
        self.entry_count = tk.Entry(frame, width=12)
        self.entry_count.insert(0, "0")
        self.entry_count.grid(row=0, column=1, sticky="w", padx=(6, 20))

        tk.Label(frame, text="Costo unitario [moneda/unid]:").grid(row=0, column=2, sticky="w")
        self.entry_cost_per_unit = tk.Entry(frame, width=12)
        self.entry_cost_per_unit.insert(0, "0.0")
        self.entry_cost_per_unit.grid(row=0, column=3, sticky="w", padx=(6, 0))

        for widget in (self.entry_count, self.entry_cost_per_unit):
            widget.bind("<KeyRelease>", lambda event: self.on_change())

    def estimate_from_holes(self, holes_data: Dict, primes_per_hole: int = 1) -> None:
        """
        Estima N = n_tiros * primas_por_tiro usando la sección "holes".

        Args:
            holes_data (dict): Diccionario que contiene la clave "geometry".
            primes_per_hole (int): Número de detonadores por tiro (default: 1).
        """
        if not holes_data:
            return

        first_hole_name = next(iter(holes_data))
        hole = holes_data.get(first_hole_name, {}) or {}
        geometry = hole.get("geometry", [])
        
        num_holes = 0
        if isinstance(geometry, list) and len(geometry) == 2 and len(geometry[0]) == len(geometry[1]):
            num_holes = len(geometry[0])
            
        total_detonators = max(num_holes * max(int(primes_per_hole), 1), 0)
        self.entry_count.delete(0, tk.END)
        self.entry_count.insert(0, str(total_detonators))

    def get_count(self) -> int:
        """Obtiene y valida la cantidad de detonadores."""
        try:
            return max(int(float(self.entry_count.get())), 0)
        except ValueError:
            return 0

    def get_cost_per_unit(self) -> float:
        """Obtiene y valida el costo por detonador."""
        try:
            return max(float(self.entry_cost_per_unit.get()), 0.0)
        except ValueError:
            return 0.0

    def calculate_cost(self) -> float:
        """Calcula el costo total de los detonadores."""
        return self.get_count() * self.get_cost_per_unit()


# ---------------------------------------------------------------------------
# SECCIÓN 3: Ventana Principal de la Aplicación
# ---------------------------------------------------------------------------

class BudgetBlastApplication(tk.Toplevel):
    """Ventana principal: presupuesto, carga de archivo y resumen de costos."""

    def __init__(self, master: Optional[tk.Misc] = None) -> None:
        """
        Inicializa la ventana principal de la GUI.

        Args:
            master (tk.Misc | None): Ventana raíz (o None).
        """
        super().__init__(master)
        self.title("Budget Blast - Prototipo")
        self.resizable(False, False)

        # Encabezado: Presupuesto y Moneda
        header = tk.Frame(self)
        header.pack(fill="x", padx=10, pady=(10, 6))
        
        tk.Label(header, text="Presupuesto total:").pack(side="left")
        self.entry_budget = tk.Entry(header, width=14)
        self.entry_budget.insert(0, "100000.0")
        self.entry_budget.pack(side="left", padx=(6, 12))
        
        tk.Label(header, text="Moneda:").pack(side="left")
        self.combo_currency = ttk.Combobox(header, width=8, state="readonly", values=["CLP", "USD", "EUR"])
        self.combo_currency.set("CLP")
        self.combo_currency.pack(side="left")
        
        self.entry_budget.bind("<KeyRelease>", lambda e: self._update_summary())
        self.combo_currency.bind("<<ComboboxSelected>>", lambda e: self._update_summary())

        # Carga de archivo UGMM
        source_group = tk.LabelFrame(self, text="Archivo UGMM")
        source_group.pack(fill="x", padx=10, pady=(0, 6))
        file_frame = tk.Frame(source_group)
        file_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(file_frame, text="Cargar archivo...", command=self._handle_load_ugmm).pack(side="left")
        self.label_filename = tk.Label(file_frame, text="(ninguno)", fg="gray")
        self.label_filename.pack(side="left", padx=10)

        # Pestañas
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.drilling_tab = DrillingTab(notebook, self._update_summary)
        self.explosives_tab = ExplosivesTab(notebook, self._update_summary)
        self.detonators_tab = DetonatorsTab(notebook, self._update_summary)

        notebook.add(self.drilling_tab, text="Perforación")
        notebook.add(self.explosives_tab, text="Explosivos")
        notebook.add(self.detonators_tab, text="Detonadores")

        # Resumen de Costos
        summary_group = tk.LabelFrame(self, text="Resumen de Costos")
        summary_group.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.summary_tree = ttk.Treeview(summary_group, columns=("item", "value"), show="headings", height=7)
        self.summary_tree.heading("item", text="Concepto")
        self.summary_tree.heading("value", text="Valor")
        self.summary_tree.column("item", width=260, anchor="w")
        self.summary_tree.column("value", width=220, anchor="center")
        self.summary_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.label_status = tk.Label(self, text="", fg="blue")
        self.label_status.pack(pady=(0, 8))

        self._update_summary()

    def _handle_load_ugmm(self) -> None:
        """Muestra el diálogo para cargar un archivo y poblar las pestañas."""
        path = filedialog.askopenfilename(
            title="Seleccionar UGMM (.txt/.json)",
            filetypes=[("UGMM JSON", "*.txt;*.json"), ("Todos", "*.*")]
        )
        if not path:
            return

        try:
            data = load_ugmm_file(path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
            return

        self.label_filename.config(text=os.path.basename(path), fg="black")
        
        holes = data.get("holes", {}) or {}
        charges = data.get("charges", {}) or {}

        self.drilling_tab.populate_from_holes(holes)
        self.explosives_tab.populate_from_charges(charges)
        self.detonators_tab.estimate_from_holes(holes, primes_per_hole=1)

        self._update_summary()

    def _get_budget(self) -> float:
        """Obtiene y valida el presupuesto total ingresado."""
        try:
            return max(float(self.entry_budget.get()), 0.0)
        except ValueError:
            return 0.0

    def _clear_summary_table(self) -> None:
        """Elimina todas las filas de la tabla de resumen."""
        for iid in self.summary_tree.get_children():
            self.summary_tree.delete(iid)

    def _add_summary_row(self, item: str, value: str) -> None:
        """Añade una nueva fila a la tabla de resumen."""
        self.summary_tree.insert("", "end", values=(item, value))

    def _update_summary(self) -> None:
        """Recalcula todos los costos y actualiza la tabla y el estado del resumen."""
        currency = self.combo_currency.get() or "CLP"
        budget = self._get_budget()

        cost_drilling = self.drilling_tab.calculate_cost()
        cost_explosives = self.explosives_tab.calculate_cost()
        cost_detonators = self.detonators_tab.calculate_cost()
        total_cost = cost_drilling + cost_explosives + cost_detonators
        margin = budget - total_cost

        self._clear_summary_table()
        self._add_summary_row("Costo perforación", f"{cost_drilling:,.2f} {currency}")
        self._add_summary_row("Costo explosivos", f"{cost_explosives:,.2f} {currency}")
        self._add_summary_row("Costo detonadores", f"{cost_detonators:,.2f} {currency}")
        self._add_summary_row("—" * 25, "—" * 15)
        self._add_summary_row("Costo TOTAL", f"{total_cost:,.2f} {currency}")
        self._add_summary_row("Presupuesto", f"{budget:,.2f} {currency}")
        self._add_summary_row("Margen", f"{margin:,.2f} {currency}")

        if total_cost <= budget:
            self.label_status.config(text="✅ Cumple presupuesto.", fg="green")
        else:
            self.label_status.config(text="❌ EXCEDE presupuesto.", fg="red")


# ---------------------------------------------------------------------------
# SECCIÓN 4: Ejecución de la Aplicación
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    app = BudgetBlastApplication(master=root)
    app.mainloop()