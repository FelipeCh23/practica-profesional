# view.py
"""
Vista (UI) con CustomTkinter + matplotlib.

Mejoras clave:
- UI dinámica: si el método es 'angular' se piden N° de tiros (S_min/S_max),
  y si es 'directo/offset/aeci' se piden espaciamientos (m).
- Tabla de alternativas (S, Tiros, Costo) + botones:
  'Ver seleccionado', 'Ver todos', 'Exportar (mejor costo)'.
- Gráfico en tema oscuro con buen contraste.

Notas:
- No se cambian nombres de funciones del modelo; solo UI y docstrings.
"""

from __future__ import annotations

import json
from typing import Optional

import customtkinter as ctk
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class View(ctk.CTk):
    """Ventana principal de la aplicación (Vista del patrón MVC)."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Optimizador profesional de tronaduras")
        self.geometry("1400x900")
        self.controller = None  # se inyecta desde el Controller

        # Layout general (2 columnas)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Paneles
        self._create_left_panel()
        self._create_right_panel()

    # ---------------- Panel izquierdo (inputs) ----------------

    def _create_left_panel(self) -> None:
        left_frame = ctk.CTkFrame(self, width=480)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        left_frame.pack_propagate(False)

        ctk.CTkLabel(
            left_frame, text="Panel de configuración",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        self.input_tabs = ctk.CTkTabview(left_frame, border_width=1)
        self.input_tabs.pack(expand=True, fill="both", padx=5, pady=5)

        self._create_geom_tab(self.input_tabs.add("1. Geometría y Presupuesto"))
        self._create_design_tab(self.input_tabs.add("2. Parámetros de Diseño"))
        self._create_costs_tab(self.input_tabs.add("3. Costos Unitarios"))

        self.run_button = ctk.CTkButton(
            left_frame, text="Buscar diseño óptimo", command=self._on_run_clicked
        )
        self.run_button.pack(padx=10, pady=15, fill="x", ipady=10)

    def _create_geom_tab(self, tab) -> None:
        """Tab para ingresar geometrías y presupuesto."""
        ctk.CTkLabel(
            tab, text="Geometrías (lista de listas JSON):",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(tab, text="Caserón (stope):").pack(anchor="w", padx=10)
        self.stope_geom_entry = ctk.CTkTextbox(tab, height=80)
        self.stope_geom_entry.insert("1.0", "[[-5,-4],[6,-4],[6,4.0],[-5,4.0]]")
        self.stope_geom_entry.pack(fill="x", padx=10)

        ctk.CTkLabel(tab, text="Galería (drift):").pack(anchor="w", padx=10, pady=(6, 0))
        self.drift_geom_entry = ctk.CTkTextbox(tab, height=80)
        self.drift_geom_entry.insert("1.0", "[[-1.5,-2.5],[2.5,-2.5],[2.5,2.5],[-1.5,2.5]]")
        self.drift_geom_entry.pack(fill="x", padx=10)

        ctk.CTkLabel(tab, text="Pivote (x, y):").pack(anchor="w", padx=10, pady=(6, 0))
        self.pivot_geom_entry = ctk.CTkEntry(tab)
        self.pivot_geom_entry.insert(0, "[0.0, 1.5]")
        self.pivot_geom_entry.pack(fill="x", padx=10)

        ctk.CTkLabel(
            tab, text="Presupuesto máximo ($):", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(20, 0))
        self.budget_entry = ctk.CTkEntry(tab)
        self.budget_entry.insert(0, "20000.0")
        self.budget_entry.pack(fill="x", padx=10)

    def _create_design_tab(self, tab) -> None:
        """Tab para parámetros geométricos del abanico y carga."""
        ctk.CTkLabel(
            tab, text="Parámetros de perforación",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="x", padx=10)
        frame.grid_columnconfigure(1, weight=1)

        # Método
        ctk.CTkLabel(frame, text="Método:").grid(row=0, column=0, sticky="w", pady=2)
        self.method_combo = ctk.CTkComboBox(
            frame, values=["angular", "directo", "offset", "aeci"],
            command=self._update_ui_for_method
        )
        self.method_combo.set("aeci")
        self.method_combo.grid(row=0, column=1, columnspan=2, sticky="ew")

        # --- CAMPOS DINÁMICOS ---
        # 1) N° de tiros (solo angular)
        self.holes_label = ctk.CTkLabel(frame, text="N° Tiros (Min / Max):")
        self.s_frame_holes = ctk.CTkFrame(frame, fg_color="transparent")
        self.s_min_holes_entry = ctk.CTkEntry(self.s_frame_holes, width=70)
        self.s_min_holes_entry.insert(0, "5")
        self.s_min_holes_entry.pack(side="left", fill="x", expand=True)
        self.s_max_holes_entry = ctk.CTkEntry(self.s_frame_holes, width=70)
        self.s_max_holes_entry.insert(0, "15")
        self.s_max_holes_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # 2) Espaciamiento (directo/offset/aeci)
        self.spacing_label = ctk.CTkLabel(frame, text="Espaciamiento (Min / Max m):")
        self.s_frame_spacing = ctk.CTkFrame(frame, fg_color="transparent")
        self.s_min_spacing_entry = ctk.CTkEntry(self.s_frame_spacing, width=70)
        self.s_min_spacing_entry.insert(0, "2")
        self.s_min_spacing_entry.pack(side="left", fill="x", expand=True)
        self.s_max_spacing_entry = ctk.CTkEntry(self.s_frame_spacing, width=70)
        self.s_max_spacing_entry.insert(0, "5")
        self.s_max_spacing_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Colocar ambos (uno se ocultará según método)
        self.holes_label.grid(row=1, column=0, sticky="w", pady=2)
        self.s_frame_holes.grid(row=1, column=1, sticky="ew")
        self.spacing_label.grid(row=1, column=0, sticky="w", pady=2)
        self.s_frame_spacing.grid(row=1, column=1, sticky="ew")

        # --- RESTO DE PARÁMETROS (comunes) ---
        ctk.CTkLabel(frame, text="Ángulo (Min / Max °):").grid(row=2, column=0, sticky="w", pady=2)
        a_frame = ctk.CTkFrame(frame, fg_color="transparent")
        a_frame.grid(row=2, column=1, columnspan=2, sticky="ew")
        self.min_angle_entry = ctk.CTkEntry(a_frame, width=70)
        self.min_angle_entry.insert(0, "-90.0")
        self.min_angle_entry.pack(side="left", fill="x", expand=True)
        self.max_angle_entry = ctk.CTkEntry(a_frame, width=70)
        self.max_angle_entry.insert(0, "90.0")
        self.max_angle_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(frame, text="Long. Perfo (Min / Max m):").grid(row=3, column=0, sticky="w", pady=2)
        l_frame = ctk.CTkFrame(frame, fg_color="transparent")
        l_frame.grid(row=3, column=1, columnspan=2, sticky="ew")
        self.min_len_entry = ctk.CTkEntry(l_frame)
        self.min_len_entry.insert(0, "0.3")
        self.min_len_entry.pack(side="left", fill="x", expand=True)
        self.max_len_entry = ctk.CTkEntry(l_frame)
        self.max_len_entry.insert(0, "30.0")
        self.max_len_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            tab, text="Parámetros de carga", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(16, 5))
        c_frame = ctk.CTkFrame(tab, fg_color="transparent")
        c_frame.pack(fill="x", padx=10)
        c_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(c_frame, text="Taco en collar (m):").grid(row=0, column=0, sticky="w", pady=2)
        self.stemming_entry = ctk.CTkEntry(c_frame)
        self.stemming_entry.insert(0, "2.0")
        self.stemming_entry.grid(row=0, column=1, sticky="ew")

        # Configurar visibilidad inicial
        self._update_ui_for_method()

    def _create_costs_tab(self, tab) -> None:
        """Tab de costos unitarios y propiedades del explosivo."""
        ctk.CTkLabel(
            tab, text="Costos y propiedades", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        c_frame = ctk.CTkFrame(tab, fg_color="transparent")
        c_frame.pack(fill="x", padx=10)
        c_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(c_frame, text="Costo perforación ($/m):").grid(row=0, column=0, sticky="w", pady=2)
        self.drill_cost_entry = ctk.CTkEntry(c_frame)
        self.drill_cost_entry.insert(0, "30.0")
        self.drill_cost_entry.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(c_frame, text="Costo explosivo ($/kg):").grid(row=1, column=0, sticky="w", pady=2)
        self.expl_cost_entry = ctk.CTkEntry(c_frame)
        self.expl_cost_entry.insert(0, "2.2")
        self.expl_cost_entry.grid(row=1, column=1, sticky="ew")

        ctk.CTkLabel(c_frame, text="Densidad explosivo (g/cc):").grid(row=2, column=0, sticky="w", pady=2)
        self.expl_dens_entry = ctk.CTkEntry(c_frame)
        self.expl_dens_entry.insert(0, "1.1")
        self.expl_dens_entry.grid(row=2, column=1, sticky="ew")

        ctk.CTkLabel(c_frame, text="Diámetro carga (mm):").grid(row=3, column=0, sticky="w", pady=2)
        self.charge_diam_entry = ctk.CTkEntry(c_frame)
        self.charge_diam_entry.insert(0, "64.0")
        self.charge_diam_entry.grid(row=3, column=1, sticky="ew")

        ctk.CTkLabel(c_frame, text="Costo detonador ($/un):").grid(row=4, column=0, sticky="w", pady=2)
        self.det_cost_entry = ctk.CTkEntry(c_frame)
        self.det_cost_entry.insert(0, "18.0")
        self.det_cost_entry.grid(row=4, column=1, sticky="ew")

    # ---------------- Panel derecho (outputs) ----------------

    def _create_right_panel(self) -> None:
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right_frame, text="Resultados",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        self.output_tabs = ctk.CTkTabview(right_frame, border_width=1)
        self.output_tabs.pack(expand=True, fill="both", padx=5, pady=5)

        self._create_results_tab(self.output_tabs.add("Alternativas"))
        self._create_log_tab(self.output_tabs.add("Log de Proceso"))

    def _create_results_tab(self, tab) -> None:
        """Tab con tabla de alternativas, botones y gráfico."""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Tabla de alternativas
        cols = ("S", "Tiros", "Costo")
        self.trials_tree = ttk.Treeview(tab, columns=cols, show="headings", height=7)
        for c in cols:
            self.trials_tree.heading(c, text=c)
            self.trials_tree.column(c, anchor="center", width=100 if c != "Costo" else 150)
        self.trials_tree.grid(row=0, column=0, sticky="ew", padx=6, pady=6)

        # Botones de acción
        btns = ctk.CTkFrame(tab, fg_color="transparent")
        btns.grid(row=1, column=0, sticky="ew", padx=6)
        self.btn_plot_sel = ctk.CTkButton(btns, text="Ver seleccionado", command=self._on_plot_selected)
        self.btn_plot_all = ctk.CTkButton(btns, text="Ver todos", command=self._on_plot_all)
        self.btn_export = ctk.CTkButton(btns, text="Exportar (mejor costo)", command=self._on_export_clicked)
        self.btn_plot_sel.pack(side="left", padx=(0, 8))
        self.btn_plot_all.pack(side="left", padx=(0, 8))
        self.btn_export.pack(side="left")

        # Figura
        plot_frame = ctk.CTkFrame(tab, fg_color="transparent")
        plot_frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=6)

        self.fig, self.ax = plt.subplots(facecolor="#242424")
        self.ax.set_facecolor("#2B2B2B")
        self.ax.tick_params(axis="x", colors="white")
        self.ax.tick_params(axis="y", colors="white")
        for spine in ("left", "bottom", "right", "top"):
            self.ax.spines[spine].set_color("white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")

        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_widget.get_tk_widget().pack(side="top", fill="both", expand=True)

        self.trials_tree.bind("<Double-1>", lambda _e: self._on_plot_selected())

    def _create_log_tab(self, tab) -> None:
        """Tab con el log de proceso."""
        self.log_textbox = ctk.CTkTextbox(tab, wrap="word")
        self.log_textbox.pack(expand=True, fill="both")

    # ---------------- API con el controlador ----------------

    def set_controller(self, controller) -> None:
        """Inyección de dependencia del controlador."""
        self.controller = controller

    def _update_ui_for_method(self, method_name: Optional[str] = None) -> None:
        """
        Muestra/oculta los campos de S según el método elegido.

        - 'angular'  → pide N° de tiros (S_min/S_max) y oculta espaciamiento.
        - otros      → pide espaciamiento (m) y oculta N° de tiros.
        """
        if method_name is None:
            method_name = self.method_combo.get().strip().lower()

        if method_name == "angular":
            # Mostrar N° tiros
            self.holes_label.grid()
            self.s_frame_holes.grid()
            # Ocultar espaciamiento
            self.spacing_label.grid_remove()
            self.s_frame_spacing.grid_remove()
        else:
            # Mostrar espaciamiento
            self.spacing_label.grid()
            self.s_frame_spacing.grid()
            # Ocultar N° tiros
            self.holes_label.grid_remove()
            self.s_frame_holes.grid_remove()

    def get_parameters(self) -> Optional[dict]:
        """
        Recoge y valida todos los parámetros de la UI.

        Returns
        -------
        dict | None
            Diccionario listo para el modelo o None si hay error.
        """
        try:
            method = self.method_combo.get().strip().lower()

            if method == "angular":
                s_min_val = int(float(self.s_min_holes_entry.get()))
                s_max_val = int(float(self.s_max_holes_entry.get()))
            else:
                s_min_val = int(float(self.s_min_spacing_entry.get()))
                s_max_val = int(float(self.s_max_spacing_entry.get()))

            if s_min_val > s_max_val:
                messagebox.showwarning(
                    "Parámetros inválidos",
                    "'S mínimo' no puede ser mayor que 'S máximo'.",
                )
                return None

            params = {
                "geometries": {
                    "stope": json.loads(self.stope_geom_entry.get("1.0", "end-1c")),
                    "drift": json.loads(self.drift_geom_entry.get("1.0", "end-1c")),
                    "pivot": json.loads(self.pivot_geom_entry.get()),
                },
                "presupuesto_maximo": float(self.budget_entry.get()),
                "s_min": s_min_val,
                "s_max": s_max_val,
                "design_method": method,
                "min_angle": float(self.min_angle_entry.get()),
                "max_angle": float(self.max_angle_entry.get()),
                "min_length": float(self.min_len_entry.get()),
                "max_length": float(self.max_len_entry.get()),
                "stemming": float(self.stemming_entry.get()),
                "unit_costs": {
                    "perforacion_por_metro": float(self.drill_cost_entry.get()),
                    "explosivo_por_kg": float(self.expl_cost_entry.get()),
                    "densidad_explosivo_gcc": float(self.expl_dens_entry.get()),
                    "diametro_carga_mm": float(self.charge_diam_entry.get()),
                    "detonador_por_unidad": float(self.det_cost_entry.get()),
                },
            }
            return params

        except (json.JSONDecodeError, ValueError) as e:
            messagebox.showerror(
                "Error de entrada",
                f"Parámetros inválidos. Revisa los campos.\n\nError: {e}",
            )
            return None

    # ------------- Helpers UI de resultados -------------

    def reset_results_ui(self) -> None:
        """Limpia tabla, plot y log antes de una nueva corrida."""
        self.log_textbox.delete("1.0", "end")
        if hasattr(self, "trials_tree"):
            for i in self.trials_tree.get_children():
                self.trials_tree.delete(i)
        if hasattr(self, "ax"):
            self.ax.clear()
            self._restyle_axes()
            self.canvas_widget.draw()

    def show_results(self, result_dict) -> None:
        """
        Llena la tabla con todas las alternativas válidas y grafica por defecto
        la alternativa de mejor costo. Guarda la lista ORDENADA que se ve en UI.
        """
        for i in self.trials_tree.get_children():
            self.trials_tree.delete(i)

        self.ax.clear()
        self._restyle_axes()

        if not result_dict:
            self.log_message("No hay diseños válidos.")
            self.canvas_widget.draw()
            self.run_button.configure(state="normal", text="Buscar diseño óptimo")
            return

        trials = result_dict["trials"]
        best = result_dict["best"]

        # >>> GUARDAR lista ORDENADA para que índice de tabla == índice de lista
        self._table_trials = trials_sorted = sorted(trials, key=lambda d: d["cost"])

        for i, t in enumerate(trials_sorted):
            self.trials_tree.insert(
                "", "end", iid=str(i),
                values=(t["S"], t["num_holes"], f"${t['cost']:,.2f}")
            )

        best_index = trials_sorted.index(best)
        self.trials_tree.selection_set(str(best_index))
        self.trials_tree.see(str(best_index))
        self._plot_single(best["design"], label=f"S={best['S']} (mejor costo)")
        self.canvas_widget.draw()

        self.log_message("\nResumen:")
        self.log_message(
            f"  • Mejor costo: ${best['cost']:,.2f} | "
            f"S usado = {best['S']} | tiros = {best['num_holes']}"
        )
        self.run_button.configure(state="normal", text="Buscar diseño óptimo")


    def log_message(self, message: str) -> None:
        """Añade un mensaje al log y mantiene el scroll al final."""
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.update_idletasks()

    # ---------------- Gráfico ----------------

    def _restyle_axes(self) -> None:
        """Restaura estilo oscuro tras limpiar el eje."""
        self.ax.set_facecolor("#2B2B2B")
        self.ax.tick_params(axis="x", colors="white")
        self.ax.tick_params(axis="y", colors="white")
        for spine in ("left", "bottom", "right", "top"):
            self.ax.spines[spine].set_color("white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")

    def _plot_single(self, design, label: str = "", light: bool = False) -> None:
        """
        Dibuja caserón (azul), galería (naranja), tiros (blanco) y carga (ámbar).

        Parámetros
        ----------
        design : dict
            {"holes": {...}, "charges": {...}}
        label : str
            Texto para el título/leyenda.
        light : bool
            Si True, traza las líneas de tiros con menor grosor/alpha para superponer.
        """
        stope = self.controller.model.generator.stope
        drift = self.controller.model.generator.drift

        # contornos
        self.ax.plot(*stope.exterior.xy, color="#5eb3ff", label="Caserón")
        self.ax.plot(*drift.exterior.xy, color="#ff9d5c", label="Galería")

        # tiros
        holes = design.get("holes", {}).get("geometry", [[], []])
        if holes and holes[0]:
            for (cx, cy), (tx, ty) in zip(*holes):
                self.ax.plot(
                    [cx, tx], [cy, ty],
                    color="white",
                    linewidth=0.9 if not light else 0.7,
                    alpha=1.0 if not light else 0.65
                )

        # cargas
        charges = design.get("charges", {}).get("geometry", [[], []])
        if charges and charges[0]:
            first_label = True
            for (cx, cy), (tx, ty) in zip(*charges):
                self.ax.plot(
                    [cx, tx], [cy, ty],
                    color="#ffbf66",
                    linewidth=2.2 if not light else 1.5,
                    alpha=1.0 if not light else 0.65,
                    label="Carga" if first_label else None
                )
                first_label = False

        self.ax.set_aspect("equal", adjustable="box")
        if label:
            self.ax.set_title(label, color="white")
        self.ax.grid(True, linestyle="--", alpha=0.35, color="gray")
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.fig.tight_layout()

    # ---------------- Eventos ----------------

    def _on_run_clicked(self) -> None:
        """Handler del botón principal."""
        if self.controller:
            self.reset_results_ui()
            self.run_button.configure(state="disabled", text="Procesando...")
            self.controller.run_optimization()

    def _on_export_clicked(self) -> None:
        """Handler del botón Exportar (mejor costo)."""
        if self.controller:
            self.controller.export_best_design()

    def _on_plot_selected(self) -> None:
        """Grafica la alternativa seleccionada en la tabla."""
        sel = self.trials_tree.selection()
        if not sel or not hasattr(self, "_table_trials"):
            return
        idx = int(sel[0])
        if not (0 <= idx < len(self._table_trials)):
            return
        trial = self._table_trials[idx]

        self.ax.clear()
        self._restyle_axes()
        self._plot_single(
            trial["design"],
            label=f"S={trial['S']} (N={trial['num_holes']}, ${trial['cost']:,.0f})"
        )
        self.canvas_widget.draw()

    def _on_plot_all(self) -> None:
        """Superpone todas las alternativas válidas en el mismo gráfico."""
        if not hasattr(self, "_table_trials") or not self._table_trials:
            return

        self.ax.clear()
        self._restyle_axes()

        # Dibujar caserón y galería una sola vez
        stope = self.controller.model.generator.stope
        drift = self.controller.model.generator.drift
        self.ax.plot(*stope.exterior.xy, color="#5eb3ff", label="Caserón")
        self.ax.plot(*drift.exterior.xy, color="#ff9d5c", label="Galería")

        for t in self._table_trials:  # misma lista que ve el usuario
            self._plot_single(t["design"], label="", light=True)

        self.ax.set_title("Todas las alternativas válidas", color="white")
        self.canvas_widget.draw()
