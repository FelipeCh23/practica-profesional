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
                out = self.model.optimizer.run(params, log=self.view.log_message)
            except Exception as exc:
                # Log + reactivar UI aunque haya reventado Shapely por una geometría
                self.view.after(0, self.view.log_message, f"❌ Error en optimización: {exc}")
                self.view.after(0, self.view.run_button.configure,
                                {"state": "normal", "text": "Buscar diseño óptimo"})
                return

            self.results = out
            self.view.after(0, self.view.show_results, out)

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
