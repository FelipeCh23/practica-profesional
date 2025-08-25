# model_vibration
import json
import os
import numpy as np
import shapely.geometry as shp

class Model:
    def __init__(self, data_path):
        # Carga DATA.json (ruta absoluta para evitar FileNotFoundError)
        data_path = os.path.abspath(data_path)
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Estructuras tal como las usa la clase original
        designs = data.get("designs", {})
        self.charges = designs.get("charges", {})
        self.holes   = designs.get("holes",   {})
        self.drifts  = designs.get("drifts",  {})
        self.stopes  = designs.get("stopes",  {})

    # --- API para la Vista/Controlador ---
    def get_patterns(self):
        return list(self.charges.keys())

    def geometry_for_pattern(self, pattern_name):
        """Recupera exactamente las mismas piezas que usa la clase original."""
        ch = self.charges[pattern_name]
        holes_name = ch["holes"]
        drift_name = self.holes[holes_name]["drift"]
        stope_name = self.drifts[drift_name]["stope"]

        charges_collar = ch["geometry"][0]
        charges_toe    = ch["geometry"][1]
        charges_diam   = ch["diameter"]
        holes_burden   = self.holes[holes_name]["burden"]
        drift_geom     = self.drifts[drift_name]["geometry"]
        stope_geom     = self.stopes[stope_name]["geometry"]
        expl_dens      = ch["explosive"]["density"]

        return {
            "charges_collar": charges_collar,
            "charges_toe":    charges_toe,
            "diameter":       charges_diam,
            "holes_burden":   holes_burden,
            "drift_geom":     drift_geom,
            "stope_geom":     stope_geom,
            "expl_density":   expl_dens,
        }

    def stope_bounds(self, stope_geom):
        xmin, ymin, xmax, ymax = shp.Polygon(stope_geom).bounds
        return xmin, ymin, xmax, ymax

    # --- Fórmula original (copiada tal cual) ---
    def holmberg_persson(self, x, y, z,
                         charges_collar, charges_toe,
                         diameter, density, const_K, const_a, **_):
        """Calcula la vibración total en el punto (x,y,z) aportado por las cargas explosivas"""
        total_vibration = np.zeros(np.shape(x))
        q = (7.854e-4) * density * (diameter**2)

        for collar, toe in zip(charges_collar, charges_toe):
            collar = np.array(collar)
            toe    = np.array(toe)
            H = np.linalg.norm(toe - collar)
            v = (toe - collar) / H

            ux = x - collar[0]
            uy = y - collar[1]
            uz = z - collar[2]

            Z = ux*v[0] + uy*v[1] + uz*v[2]
            R = (np.abs(ux**2 + uy**2 + uz**2 - Z**2))**0.5
            R = np.where(R != 0, R, np.nan)

            vibration = (q/R) * (np.arctan(Z/R) + np.arctan((H - Z)/R))
            vibration = const_K * (vibration**const_a)
            total_vibration = total_vibration + vibration

        return total_vibration


