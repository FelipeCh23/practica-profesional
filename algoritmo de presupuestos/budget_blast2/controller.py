# controller.py
"""
Controlador: conecta la vista con el modelo.

Responsabilidades:
- Leer y validar parámetros desde la vista.
- Actualizar las geometrías en el modelo.
- Ejecutar la optimización en un hilo (para no bloquear la UI).
- Mostrar resultados y exportar el mejor diseño a JSON.
- Proveer a la vista acceso a una alternativa por índice (tabla).
"""

from __future__ import annotations

import json
import threading
from tkinter import filedialog, messagebox

from model import Model


class Controller:
    """Controlador del patrón MVC."""

    def __init__(self, model: Model, view) -> None:
        self.model = model
        self.view = view
        self.view.set_controller(self)

        # Resultados de la última corrida:
        # {"best": {...}, "trials": [ ... ]}
        self.results = None

    # ---------------- Acciones principales ----------------

    def run_optimization(self) -> None:
        params = self.view.get_parameters()
        if params is None:
            self.view.run_button.configure(state="normal", text="Buscar diseño óptimo")
            return

        try:
            geoms = params.pop("geometries")
            self.model.update_geometry(geoms["stope"], geoms["drift"], geoms["pivot"])
            self.view.log_message("Geometrías cargadas correctamente.")
        except Exception as exc:
            self.view.log_message(f"❌ Error al cargar geometrías: {exc}")
            self.view.run_button.configure(state="normal", text="Buscar diseño óptimo")
            return

        def task():
            try:
                # Ejecutar optimizador (bloque principal)
                out = self.model.optimizer.run(params, log=lambda msg: 
                                            self.view.after(0, self.view.log_message, msg))

                # Salida nula o vacía
                if not out:
                    self.view.after(0, self.view.log_message, "✖ No se encontró diseño válido.")
                    self.view.after(0, self.view.run_button.configure,
                                    {"state": "normal", "text": "Buscar diseño óptimo"})
                    return

                # Mostrar resultados
                self.results = out
                self.view.after(0, self.view.show_results, out)

                # Mostrar métricas del mejor diseño
                best = out.get("best", {})
                metrics = best.get("metrics", {}) or {}
                design = best.get("design", {}) or {}
                frag_data = design.get("frag_data", {}) or {}
                p80 = frag_data.get("P80", 0.0)

                def _print_summary():
                    if metrics:
                        self.view.log_message("\n--- Métricas del mejor diseño ---")
                        self.view.log_message(
                            f"  • Energía específica efectiva: {metrics.get('energia_especifica_efectiva', 0):.3f} MJ/m³")
                        self.view.log_message(
                            f"  • Volumen volado: {metrics.get('volumen', 0):.1f} m³")
                        self.view.log_message(
                            f"  • Costo por m³: ${metrics.get('costo_por_m3', 0):.2f}")
                        if p80 > 0:
                            self.view.log_message(
                                f"  • Fragmentación P80 estimada: {p80:.1f} mm")

                    self.view.run_button.configure(state="normal", text="Buscar diseño óptimo")

                self.view.after(0, _print_summary)

            except Exception as exc:
                # Captura global del hilo
                self.view.after(0, self.view.log_message, f"❌ Error en optimización: {exc}")
                self.view.after(0, self.view.run_button.configure,
                                {"state": "normal", "text": "Buscar diseño óptimo"})

        import threading
        threading.Thread(target=task, daemon=True).start()


    # ---------------- Soporte para la vista ----------------

    def get_trial_by_index(self, idx: int):
        """
        Devuelve la alternativa (trial) por índice de fila (tabla de la vista).
        """
        if not self.results or not self.results.get("trials"):
            return None
        trials = self.results["trials"]
        if 0 <= idx < len(trials):
            return trials[idx]
        return None

    def export_best_design(self) -> None:
        """
        Exporta a JSON la geometría (holes + charges) del mejor por costo.
        """
        if not self.results or not self.results.get("best"):
            messagebox.showwarning("Exportar", "No hay diseño para exportar.")
            return

        best = self.results["best"]

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            title="Guardar diseño (mejor costo) como..."
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(best["design"], f, indent=2, ensure_ascii=False)
            self.view.log_message(f"✅ Diseño exportado: {path}")
        except Exception as exc:
            self.view.log_message(f"❌ Error al exportar: {exc}")
