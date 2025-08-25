
# model_vibration

# Model único (sin UI). Carga DATA.json y expone:
# - get_patterns()
# - get_geometry(pattern)
# - holmberg_persson(x, y, z, **params)   ← cálculo central (HP)

from __future__ import annotations
import json
import math
from typing import Dict, List, Tuple, Any
import numpy as np

Point3 = Tuple[float, float, float]
Point2 = Tuple[float, float]

class Model:
    def __init__(self, data_path: str = "DATA.json"):
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    # -------- DATA helpers (sin defaults raros, fiel a DATA.json) --------
    def get_patterns(self) -> List[str]:
        charges = self.data.get("charges", {})
        # Profe pidió que pueda existir un patrón vacío "" al inicio en UI
        return list(charges.keys())

    def get_geometry(self, pattern: str) -> Dict[str, Any]:
        """
        Devuelve:
          - charges_collar: [(x,y,z), ...]
          - charges_toe   : [(x,y,z), ...]
          - diameter (mm)
          - density  (g/cc)
          - K_const  (mm/s)
          - a_const  (adim)
          - drift_geom: [(x,y), ...] (opcional)
          - stope_geom: [(x,y), ...]
          - burden (m) si está en holes
        Lee exactamente los mismos campos que usa la vista original.
        """
        all_ch = self.data.get("charges", {})
        all_hl = self.data.get("holes", {})
        all_dr = self.data.get("drifts", {})
        all_st = self.data.get("stopes", {})

        ch = all_ch.get(pattern, {})
        # geometry esperado en Energy/Vibration: [collars, toes] (tal cual muestras)
        collars = ch.get("geometry", [[], []])[0] if isinstance(ch.get("geometry"), list) else []
        toes    = ch.get("geometry", [[], []])[1] if isinstance(ch.get("geometry"), list) else []

        diameter = ch.get("diameter")  # mm
        expl     = ch.get("explosive", {})
        density  = expl.get("density")  # g/cc

        holes_name = ch.get("holes")
        burden = None
        drift_name = None
        if holes_name and holes_name in all_hl:
            burden     = all_hl[holes_name].get("burden")
            drift_name = all_hl[holes_name].get("drift")

        drift_geom = None
        stope_geom = None
        stope_name = None
        if drift_name and drift_name in all_dr:
            drift_geom = all_dr[drift_name].get("geometry")
            stope_name = all_dr[drift_name].get("stope")

        if stope_name and stope_name in all_st:
            stope_geom = all_st[stope_name].get("geometry")

        # Constantes HP pueden venir desde DATA si existen a nivel método
        # (si no, las pasa la vista/usuario)
        K_const = ch.get("K_const")
        a_const = ch.get("a_const")

        return dict(
            charges_collar=collars, charges_toe=toes,
            diameter=diameter, density=density,
            K_const=K_const, a_const=a_const,
            drift_geom=drift_geom, stope_geom=stope_geom,
            burden=burden
        )

    # -------------------- Cálculo HP (central, sin UI) --------------------
    @staticmethod
    def _dist_point_to_segment_3d(p: Point3, a: Point3, b: Point3) -> float:
        """Distancia mínima de punto 3D p a segmento AB (3D)."""
        px, py, pz = p
        ax, ay, az = a
        bx, by, bz = b
        ab = np.array([bx-ax, by-ay, bz-az], dtype=float)
        ap = np.array([px-ax, py-ay, pz-az], dtype=float)
        denom = np.dot(ab, ab)
        if denom <= 0.0:
            return float(np.linalg.norm(ap))
        t = np.clip(np.dot(ap, ab)/denom, 0.0, 1.0)
        closest = np.array([ax, ay, az]) + t * ab
        return float(np.linalg.norm(np.array([px, py, pz]) - closest))

    def holmberg_persson(
        self,
        x: np.ndarray | float,
        y: np.ndarray | float,
        z: np.ndarray | float,
        *,
        charges_collar: List[Point3],
        charges_toe: List[Point3],
        diameter: float,   # mm
        density: float,    # g/cc
        K_const: float,    # mm/s
        a_const: float     # adimensional
    ) -> np.ndarray:
        """
        Implementación simple de Holmberg & Persson:
            PPV_i = K * (R_i / Q_i^(1/3))^(-a)
        donde Q_i se aproxima a partir de diámetro (mm) y densidad (g/cc)
        suponiendo 1 m de columna equivalente (placeholder NECESARIO para operar).
        Se suma la contribución de cada carga.

        *Nota*: el profe pidió mover la fórmula al Model; la View/Controller no hacen cálculo.
        """
        # Preparar entrada como arrays para vectorizar
        X = np.asarray(x, dtype=float)
        Y = np.asarray(y, dtype=float)
        Z = np.asarray(z, dtype=float)
        # Broadcast a forma común
        X, Y, Z = np.broadcast_arrays(X, Y, Z)
        out = np.zeros_like(X, dtype=float)

        # Carga por metro ~ área * densidad * 1m
        # diámetro en mm -> m
        d_m = (diameter or 0.0) / 1000.0
        # densidad g/cc -> kg/m3 aprox (1 g/cc = 1000 kg/m3)
        rho = (density or 0.0) * 1000.0
        area = math.pi * (d_m**2) / 4.0
        # Q1m: kg/m * 1m = kg
        Q1m = area * rho  # kg

        # Evitar división por cero:
        if Q1m <= 0.0:
            Q1m = 1.0

        Q13 = Q1m ** (1.0/3.0)
        K   = float(K_const or 1.0)
        a   = float(a_const or 1.0)

        pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)

        for c, t in zip(charges_collar, charges_toe):
            # distancia punto–segmento
            R = np.array([self._dist_point_to_segment_3d(tuple(p), tuple(c), tuple(t)) for p in pts], dtype=float)
            R = R.reshape(X.shape)
            # HP contribución por carga:
            # PPV_i = K * (R / Q^(1/3))^(-a)
            with np.errstate(divide="ignore", invalid="ignore"):
                contrib = K * np.power(R / Q13, -a)
                contrib[~np.isfinite(contrib)] = 0.0
            out += contrib

        return out

