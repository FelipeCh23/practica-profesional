"""
controller energy_analysis:
- Lee la vista, actualiza el modelo y ordena la representación.
- No contiene cálculo numérico (eso vive en model.py).
"""

from model import Model


def _f(s, default=0.0):
    try:
        return float(s)
    except Exception:
        return default


def _i(s, default=0):
    try:
        return int(float(s))  # permite "50.0"
    except Exception:
        return default


class Controller:
    def __init__(self, model: Model, view, parent_app):
        self.model = model
        self.view = view
        self.parent_app = parent_app

        # La vista no tiene lógica: inyectamos callbacks acá
        self.view.bind_actions(self.on_plot2d, self.on_plot3d)

        # Si conectas con el app real, puedes enlazarlo así:
        # self.model.bind_parent(parent_app)

    def _sync_model_from_view(self):
        """
        Lee strings de la vista, los castea y los pasa al model.
        Devuelve (ok, msg).
        """
        data = self.view.get_form_data()

        # Normalizamos números como texto para set_from_view_strings
        safe = data.copy()
        for k in ("xmin","xmax","ymin","ymax","zmin","zmax","cutoff","diameter","density","K_const","a_const"):
            safe[k] = str(_f(data.get(k, ""), 0.0))
        for k in ("resol","levels"):
            safe[k] = str(_i(data.get(k, ""), 0))

        self.model.set_from_view_strings(safe)
        return self.model.validate()

    # --------- Callbacks de la UI ---------
    def on_plot2d(self):
        ok, err = self._sync_model_from_view()
        if not ok:
            return self.view.render_error(err)
        meta = self.model.compute_energy_grid()      # cálculo en el MODEL
        levels = _i(self.view.levels.get(), 10)
        self.view.render_contours(meta, levels)

    def on_plot3d(self):
        ok, err = self._sync_model_from_view()
        if not ok:
            return self.view.render_error(err)
        # Placeholder 3D: el model ya calcula; falta implementar render 3D en la vista
        _ = self.model.compute_energy_isosurface()
        self.view.render_error("Isosuperficie 3D: placeholder listo (agregar render en la vista).")
