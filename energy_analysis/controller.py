"""
Controlador de EnergyAnalysis.

Responsabilidad:
- Leer valores desde la vista.
- Actualizar/validar el modelo.
- Ejecutar cálculos y actualizar la vista con el resultado.
- Manejar errores de validación.

No realiza cálculos numéricos ni dibuja.
"""

from model import Model as ModelBase


class Controller:
    def __init__(self, model: ModelBase, view, parent_app=None):
        self.model = model
        self.view  = view
        self.parent_app = parent_app
        # Conectar botones a handlers
        self.view.set_handlers(self._on_compute_grid, self._on_compute_iso)

    # ----------------------- Operaciones internas -----------------------------

    def _sync_model_from_view(self):
        """
        Lee el formulario, actualiza el modelo y valida.
        Devuelve (ok: bool, msg: str).
        """
        data = self.view.get_form_data()
        self.model.set_from_view_strings(data)
        ok, msg = self.model.validate()
        return ok, msg

    # ----------------------- Handlers de botones -------------------------------

    def _on_compute_grid(self):
        ok, msg = self._sync_model_from_view()
        if not ok:
            self.view.show_error(msg)
            return
        meta = self.model.compute_energy_grid()
        self.view.show_grid_plot(meta)

    def _on_compute_iso(self):
        ok, msg = self._sync_model_from_view()
        if not ok:
            self.view.show_error(msg)
            return
        meta = self.model.compute_energy_isosurface()
        self.view.show_iso_info(meta)
