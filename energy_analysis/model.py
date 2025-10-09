# model.py
import json
<<<<<<< HEAD

=======
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
import numpy as np


class Model:
    """
    Modelo de EnergyAnalysis.
    - Carga y entrega datos desde DATA.json.
    - Expone utilidades para recuperar patrones y geometrías.
    - Contiene la función 'kleine' tal cual desde la appRing original.
    """

    def __init__(self, data_path="DATA.json"):
        # Cargar el archivo de datos
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    # ---------------------------
    # Lectura de datos (DATA.json)
    # ---------------------------

    def get_patterns(self):
        """Devuelve la lista de patrones disponibles en charges."""
        return list(self.data.get("charges", {}).keys())

    def get_geometry(self, pattern):
        """Recupera parámetros y geometrías de un patrón dado."""
        charges = self.data.get("charges", {})
<<<<<<< HEAD
        holes = self.data.get("holes", {})
        drifts = self.data.get("drifts", {})
        stopes = self.data.get("stopes", {})
=======
        holes   = self.data.get("holes", {})
        drifts  = self.data.get("drifts", {})
        stopes  = self.data.get("stopes", {})
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

        ch = charges.get(pattern, {})

        # Formato A (geometry: dict con collars/toes)
        if "geometry" in ch and isinstance(ch["geometry"], dict):
            collars = ch["geometry"].get("collars", [])
<<<<<<< HEAD
            toes = ch["geometry"].get("toes", [])
=======
            toes    = ch["geometry"].get("toes", [])
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        # Formato B (lines: lista de pares)
        elif "lines" in ch:
            collars, toes = [], []
            for seg in ch.get("lines", []):
                if isinstance(seg, (list, tuple)) and len(seg) == 2:
                    c, t = seg
                    collars.append(c)
                    toes.append(t)
        else:
            collars, toes = [], []

<<<<<<< HEAD
        diameter = ch.get("diameter")
        expl_dens = (ch.get("explosive") or {}).get("density")

        hole_name = ch.get("holes")
        burden = None
        drift_name = None
        if hole_name and hole_name in holes:
            hinfo = holes[hole_name]
            burden = hinfo.get("burden")
=======
        diameter  = ch.get("diameter")
        expl_dens = (ch.get("explosive") or {}).get("density")

        hole_name  = ch.get("holes")
        burden     = None
        drift_name = None
        if hole_name and hole_name in holes:
            hinfo      = holes[hole_name]
            burden     = hinfo.get("burden")
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
            drift_name = hinfo.get("drift")

        drift_geom = None
        stope_geom = None
<<<<<<< HEAD
        rock_dens = None
        stope_name = None

        if drift_name and drift_name in drifts:
            dinfo = drifts[drift_name]
=======
        rock_dens  = None
        stope_name = None

        if drift_name and drift_name in drifts:
            dinfo      = drifts[drift_name]
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
            drift_geom = dinfo.get("geometry")
            stope_name = dinfo.get("stope")

        if stope_name and stope_name in stopes:
<<<<<<< HEAD
            sinfo = stopes[stope_name]
            stope_geom = sinfo.get("geometry")
            rock = sinfo.get("rock") or {}
            rock_dens = rock.get("density")

        return dict(
            collars=collars,
            toes=toes,
            diameter=diameter,
            expl_dens=expl_dens,
            rock_dens=rock_dens,
            stope_geom=stope_geom,
            drift_geom=drift_geom,
            burden=burden,
=======
            sinfo      = stopes[stope_name]
            stope_geom = sinfo.get("geometry")
            rock       = sinfo.get("rock") or {}
            rock_dens  = rock.get("density")

        return dict(
            collars=collars, toes=toes,
            diameter=diameter, expl_dens=expl_dens,
            rock_dens=rock_dens,
            stope_geom=stope_geom, drift_geom=drift_geom,
            burden=burden
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        )

    # ---------------------------
    # Cálculo (KLEINE original)
    # ---------------------------

    def kleine(self, x, y, z, collars, toes, diameter, expl_dens):
        """
        Función original 'kleine' desde la clase EnergyAnalysis (appRing).
        Calcula la energía en el espacio dada la geometría de cargas.
        """

        E = np.zeros_like(x, dtype=float)

        for (cx, cy, cz), (tx, ty, tz) in zip(collars, toes):
            dx = x - cx
            dy = y - cy
            dz = z - cz
            r2 = dx**2 + dy**2 + dz**2

            # Distancia entre collar y toe = longitud de la carga
<<<<<<< HEAD
            L = np.sqrt((tx - cx) ** 2 + (ty - cy) ** 2 + (tz - cz) ** 2)
=======
            L = np.sqrt((tx - cx)**2 + (ty - cy)**2 + (tz - cz)**2)
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

            # Volumen de la carga
            V = np.pi * (0.25 * diameter**2) * L

            # Energía por densidad explosiva
            Q = V * expl_dens

            # Suma gaussiana en cada punto
            E += Q * np.exp(-r2 / (0.5 * L**2 + 1e-6))

        return E
