# controller.py
import json
import threading
import numpy as np
from tkinter import filedialog, messagebox


class Controller:
    """Conecta Vista y Modelo; maneja hilos, exportación y actualización de geometría."""

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.set_controller(self)
        self.last_best_design = None

    def run_optimization(self):
        """Inicia la optimización en un hilo para no congelar la UI."""
        params = self.view.get_parameters()
        if params is None:
            self.view.run_button.configure(state="normal", text="🚀 Iniciar Optimización")
            return

        # Configurar geometrías en el modelo
        try:
            geoms = params.pop('geometries')
            self.model.update_geometry(geoms['stope'], geoms['drift'], geoms['pivot'])
            self.view.log_message("Geometrías cargadas correctamente.")
        except Exception as e:
            self.view.log_message(f"❌ Error al cargar geometrías: {e}")
            self.view.run_button.configure(state="normal", text="🚀 Iniciar Optimización")
            return

        # Limpiar vistas previas
        self.view.log_textbox.delete("1.0", "end")
        for i in self.view.results_tree.get_children():
            self.view.results_tree.delete(i)
        self.view.export_button.configure(state="disabled")

        def task():
            best = self.model.optimizer.run(params, log=self.view.log_message)
            self.last_best_design = best
            self.view.after(0, self.view.show_results, best)

        threading.Thread(target=task, daemon=True).start()

    def export_best_design(self):
        """Exporta el mejor diseño a JSON (tiros y cargas)."""
        if not self.last_best_design:
            messagebox.showwarning("Exportar", "No hay diseño para exportar. Ejecuta primero.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            title="Guardar diseño como..."
        )
        if not path:
            return

        try:
            # Asegurar serialización (por si hay arrays numpy)
            def _default(o):
                if isinstance(o, np.ndarray):
                    return o.tolist()
                return o

            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.last_best_design["design"], f, indent=2, ensure_ascii=False, default=_default)

            self.view.log_message(f"✅ Diseño exportado: {path}")
        except Exception as e:
            self.view.log_message(f"❌ Error al exportar: {e}")
