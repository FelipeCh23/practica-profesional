# view.py
import json
import customtkinter as ctk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class View(ctk.CTk):
    """Interfaz con pestañas: Geometría/Presupuesto, Parámetros de Diseño y Costos."""

    def __init__(self):
        super().__init__()
        self.title("Optimizador Profesional de Tronaduras")
        self.geometry("1200x850")
        self.controller = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: CONTROLES ---
        left = ctk.CTkFrame(self, width=420)
        left.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        ctk.CTkLabel(left, text="Panel de Configuración",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        self.input_tabs = ctk.CTkTabview(left, border_width=1)
        self.input_tabs.pack(expand=True, fill="both", padx=5, pady=5)
        self._create_geom_tab(self.input_tabs.add("1. Geometría y Presupuesto"))
        self._create_design_tab(self.input_tabs.add("2. Parámetros de Diseño"))
        self._create_costs_tab(self.input_tabs.add("3. Costos Unitarios"))

        self.run_button = ctk.CTkButton(left, text="🚀 Iniciar Optimización",
                                        command=self._on_run_clicked)
        self.run_button.pack(padx=10, pady=15, fill="x", ipady=10)

        # --- PANEL DERECHO: RESULTADOS ---
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Resultados de la Optimización",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        self.output_tabs = ctk.CTkTabview(right, border_width=1)
        self.output_tabs.pack(expand=True, fill="both", padx=5, pady=5)
        self._create_results_tab(self.output_tabs.add("Mejor Diseño"))
        self._create_log_tab(self.output_tabs.add("Log de Proceso"))

    # ---------- Pestaña 1: Geometría y Presupuesto ----------
    def _create_geom_tab(self, tab):
        ctk.CTkLabel(tab, text="Geometrías (formato JSON):",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(tab, text="Polígono del Caserón (Stope):").pack(anchor="w", padx=10, pady=(6, 0))
        self.stope_geom_entry = ctk.CTkTextbox(tab, height=80)
        self.stope_geom_entry.insert("1.0", "[[0,0], [25,0], [25,35], [0,35]]")
        self.stope_geom_entry.pack(fill="x", padx=10)

        ctk.CTkLabel(tab, text="Polígono de la Galería (Drift):").pack(anchor="w", padx=10, pady=(6, 0))
        self.drift_geom_entry = ctk.CTkTextbox(tab, height=80)
        self.drift_geom_entry.insert("1.0", "[[10,12], [15,12], [15,16], [10,16]]")
        self.drift_geom_entry.pack(fill="x", padx=10)

        ctk.CTkLabel(tab, text="Punto Pivote (Perforadora):").pack(anchor="w", padx=10, pady=(6, 0))
        self.pivot_geom_entry = ctk.CTkEntry(tab)
        self.pivot_geom_entry.insert(0, "[12.5, 14.0]")
        self.pivot_geom_entry.pack(fill="x", padx=10)

        ctk.CTkLabel(tab, text="Presupuesto Máximo ($):",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(14, 0))
        self.budget_entry = ctk.CTkEntry(tab)
        self.budget_entry.insert(0, "20000.0")
        self.budget_entry.pack(fill="x", padx=10)

    # ---------- Pestaña 2: Parámetros de Diseño ----------
    def _create_design_tab(self, tab):
        ctk.CTkLabel(tab, text="Perforación:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        frm = ctk.CTkFrame(tab, fg_color="transparent")
        frm.pack(fill="x", padx=10)
        frm.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frm, text="Método:").grid(row=0, column=0, sticky="w", pady=2)
        self.method_combo = ctk.CTkComboBox(frm, values=["angular", "directo", "offset", "aeci"],
                                            command=self._update_ui_for_method)
        self.method_combo.set("angular")
        self.method_combo.grid(row=0, column=1, sticky="ew", pady=2)

        ctk.CTkLabel(frm, text="Iterar 'S' (Min/Max):").grid(row=1, column=0, sticky="w", pady=2)
        frm_s = ctk.CTkFrame(frm, fg_color="transparent")
        frm_s.grid(row=1, column=1, sticky="ew")
        self.s_min_entry = ctk.CTkEntry(frm_s, width=70); self.s_min_entry.insert(0, "5")
        self.s_min_entry.pack(side="left", fill="x", expand=True)
        self.s_max_entry = ctk.CTkEntry(frm_s, width=70); self.s_max_entry.insert(0, "15")
        self.s_max_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.s_label = ctk.CTkLabel(frm, text="N° Tiros", width=90, anchor="w")
        self.s_label.grid(row=1, column=2, sticky="w", padx=6)

        ctk.CTkLabel(frm, text="Ángulo (Min/Max °):").grid(row=2, column=0, sticky="w", pady=2)
        frm_a = ctk.CTkFrame(frm, fg_color="transparent")
        frm_a.grid(row=2, column=1, sticky="ew")
        self.min_angle_entry = ctk.CTkEntry(frm_a, width=70); self.min_angle_entry.insert(0, "-45.0")
        self.min_angle_entry.pack(side="left", fill="x", expand=True)
        self.max_angle_entry = ctk.CTkEntry(frm_a, width=70); self.max_angle_entry.insert(0, "45.0")
        self.max_angle_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(frm, text="Longitud Perfo (Min/Max m):").grid(row=3, column=0, sticky="w", pady=2)
        frm_l = ctk.CTkFrame(frm, fg_color="transparent")
        frm_l.grid(row=3, column=1, sticky="ew")
        self.min_len_entry = ctk.CTkEntry(frm_l); self.min_len_entry.insert(0, "1.0")
        self.min_len_entry.pack(side="left", fill="x", expand=True)
        self.max_len_entry = ctk.CTkEntry(frm_l); self.max_len_entry.insert(0, "30.0")
        self.max_len_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(tab, text="Cargas:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(18, 5))
        frm_c = ctk.CTkFrame(tab, fg_color="transparent")
        frm_c.pack(fill="x", padx=10)
        frm_c.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frm_c, text="Taco en Collar (m):").grid(row=0, column=0, sticky="w")
        self.stemming_entry = ctk.CTkEntry(frm_c); self.stemming_entry.insert(0, "2.0")
        self.stemming_entry.grid(row=0, column=1, sticky="ew")

        self._update_ui_for_method()

    # ---------- Pestaña 3: Costos ----------
    def _create_costs_tab(self, tab):
        ctk.CTkLabel(tab, text="Costos/Propiedades Unitarias:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        frm = ctk.CTkFrame(tab, fg_color="transparent")
        frm.pack(fill="x", padx=10)
        frm.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frm, text="Costo Perforación ($/m):").grid(row=0, column=0, sticky="w", pady=2)
        self.drill_cost_entry = ctk.CTkEntry(frm); self.drill_cost_entry.insert(0, "30.0")
        self.drill_cost_entry.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(frm, text="Costo Explosivo ($/kg):").grid(row=1, column=0, sticky="w", pady=2)
        self.expl_cost_entry = ctk.CTkEntry(frm); self.expl_cost_entry.insert(0, "2.2")
        self.expl_cost_entry.grid(row=1, column=1, sticky="ew")

        ctk.CTkLabel(frm, text="Densidad Explosivo (g/cc):").grid(row=2, column=0, sticky="w", pady=2)
        self.expl_dens_entry = ctk.CTkEntry(frm); self.expl_dens_entry.insert(0, "1.1")
        self.expl_dens_entry.grid(row=2, column=1, sticky="ew")

        ctk.CTkLabel(frm, text="Diámetro Carga (mm):").grid(row=3, column=0, sticky="w", pady=2)
        self.charge_diam_entry = ctk.CTkEntry(frm); self.charge_diam_entry.insert(0, "64.0")
        self.charge_diam_entry.grid(row=3, column=1, sticky="ew")

        ctk.CTkLabel(frm, text="Costo Detonador ($/un):").grid(row=4, column=0, sticky="w", pady=2)
        self.det_cost_entry = ctk.CTkEntry(frm); self.det_cost_entry.insert(0, "18.0")
        self.det_cost_entry.grid(row=4, column=1, sticky="ew")

    # ---------- Pestaña Resultados + gráfico ----------
    def _create_results_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        self.results_tree = ttk.Treeview(tab, columns=("param", "value"),
                                         show="headings", height=5)
        self.results_tree.heading("param", text="Parámetro")
        self.results_tree.heading("value", text="Valor")
        self.results_tree.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.export_button = ctk.CTkButton(tab, text="Exportar a JSON",
                                           command=self._on_export_clicked, state="disabled")
        self.export_button.grid(row=0, column=1, padx=10, pady=5)

        plot_frame = ctk.CTkFrame(tab, fg_color="transparent")
        plot_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.fig, self.ax = plt.subplots()
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_widget.get_tk_widget().pack(side="top", fill="both", expand=True)

    def _create_log_tab(self, tab):
        self.log_textbox = ctk.CTkTextbox(tab, wrap="word")
        self.log_textbox.pack(expand=True, fill="both")

    # ---------- API controlador ----------
    def set_controller(self, controller):  # tipo: (Controller) -> None
        self.controller = controller

    def _update_ui_for_method(self, method_name: str | None = None):
        if method_name is None:
            method_name = self.method_combo.get()
        self.s_label.configure(text="N° Tiros" if method_name == "angular" else "m (spacing)")

    def _on_run_clicked(self):
        if self.controller:
            self.run_button.configure(state="disabled", text="Procesando...")
            self.controller.run_optimization()

    def _on_export_clicked(self):
        if self.controller:
            self.controller.export_best_design()

    # ---------- IO parámetros ----------
    def get_parameters(self) -> dict | None:
        try:
            params = {
                "geometries": {
                    "stope": json.loads(self.stope_geom_entry.get("1.0", "end-1c")),
                    "drift": json.loads(self.drift_geom_entry.get("1.0", "end-1c")),
                    "pivot": json.loads(self.pivot_geom_entry.get()),
                },
                "presupuesto_maximo": float(self.budget_entry.get()),

                "design_method": self.method_combo.get().strip().lower(),
                "s_min": int(self.s_min_entry.get()),
                "s_max": int(self.s_max_entry.get()),
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
            if params["s_min"] > params["s_max"]:
                messagebox.showwarning("Parámetros inválidos", "'S min' no puede ser mayor que 'S max'.")
                return None
            return params
        except (json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Error de entrada", f"Parámetros inválidos. Revisa los campos.\n\n{e}")
            return None

    # ---------- Log y Resultados ----------
    def log_message(self, msg: str):
        self.log_textbox.insert("end", msg + "\n")
        self.log_textbox.see("end")
        self.update_idletasks()

    def show_results(self, best_design: dict | None):
        # limpiar tabla
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        self.ax.clear()
        if best_design:
            num_tiros = len(best_design['design']['holes']['geometry'][0])
            cost = best_design['cost']
            meta = best_design.get('meta', {})
            metodo = meta.get('method', '—')
            s_label = meta.get('S_label', 'S')
            s_used = meta.get('S_used', '—')

            self.results_tree.insert("", "end", values=("Estado", "🏆 Éxito"))
            self.results_tree.insert("", "end", values=("Costo Óptimo", f"${cost:,.2f}"))
            self.results_tree.insert("", "end", values=("Método", metodo))
            self.results_tree.insert("", "end", values=(s_label, s_used))
            self.results_tree.insert("", "end", values=("Número de Tiros", num_tiros))

            self.export_button.configure(state="normal")
            self.plot_design(best_design['design'])
            self.output_tabs.set("Mejor Diseño")
        else:
            self.results_tree.insert("", "end", values=("Estado", "❌ Sin resultados"))
            self.export_button.configure(state="disabled")
            self.ax.set_title("No se encontraron diseños válidos")
            self.canvas_widget.draw()

        self.run_button.configure(state="normal", text="🚀 Iniciar Optimización")

    def plot_design(self, design: dict):
        """Dibuja caserón (azul), galería (rojo) y tiros (negro)."""
        stope = self.controller.model.generator.stope
        drift = self.controller.model.generator.drift

        self.ax.plot(*stope.exterior.xy, color="blue", label="Caserón")
        self.ax.plot(*drift.exterior.xy, color="red", label="Galería")

        holes = design.get("holes", {})
        geo = holes.get("geometry", [[], []])
        if geo and len(geo) == 2:
            collars, toes = geo
            for (cx, cy), (tx, ty) in zip(collars, toes):
                self.ax.plot([cx, tx], [cy, ty], color="black", linewidth=0.9)

        charges = design.get("charges", {})
        geo_c = charges.get("geometry", [[], []])
        if geo_c and len(geo_c) == 2 and len(geo_c[0]) > 0:
            for (cx, cy), (tx, ty) in zip(geo_c[0], geo_c[1]):
                self.ax.plot([cx, tx], [cy, ty], color="#ff9800", linewidth=2.2,
                             label="Carga" if "Carga" not in self.ax.get_legend_handles_labels()[1] else "")

        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_title("Diseño Óptimo Generado")
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.ax.legend()
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.fig.tight_layout()
        self.canvas_widget.draw()
