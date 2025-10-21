"""
Modelo (lógica de negocio): generación de abanicos, cargas, costos y optimización.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import shapely.geometry as sgeom
import shapely.affinity as saff


# -------------------------------------------------
# Utilidades geométricas (robustas y documentadas)
# -------------------------------------------------

def _sort_points(geometry: sgeom.base.BaseGeometry,
                 pivot: sgeom.Point) -> List[sgeom.Point]:
    """Devuelve los puntos de `geometry` ordenados por distancia creciente a `pivot`."""
    if geometry.is_empty:
        return []
    pts: List[sgeom.Point] = []
    if isinstance(geometry, sgeom.Point):
        pts = [geometry]
    elif hasattr(geometry, "geoms"):
        pts = [g for g in geometry.geoms if isinstance(g, sgeom.Point)]
    pts.sort(key=lambda p: p.distance(pivot))
    return pts


def _angle_between(line_a: sgeom.LineString, line_b: sgeom.LineString) -> float:
    """Ángulo firmado (grados) entre dos líneas con mismo origen (rango [-180, 180])."""
    (ax1, ay1), (ax2, ay2) = list(line_a.coords)[:2]
    (bx1, by1), (bx2, by2) = list(line_b.coords)[:2]
    va = np.array([ax2 - ax1, ay2 - ay1], dtype=float)
    vb = np.array([bx2 - bx1, by2 - by1], dtype=float)
    if np.linalg.norm(va) == 0 or np.linalg.norm(vb) == 0:
        return 0.0
    va /= np.linalg.norm(va)
    vb /= np.linalg.norm(vb)
    dot = np.clip(np.dot(va, vb), -1, 1)
    det = va[0] * vb[1] - va[1] * vb[0]
    return float(np.degrees(np.arctan2(det, dot)))


# --------------------------------
# Generador geométrico de abanicos
# --------------------------------

class DrillFanGenerator:
    """
    Genera tiros (collar/fondo) de un abanico 2D dentro de un caserón.

    Contexto
    --------
    stope_geom : list[list[float]]  Polígono del caserón (x, y).
    drift_geom : list[list[float]]  Polígono de la galería (x, y).
    pivot_geom : list[float]        Punto pivote (x, y) desde donde abren los tiros.
    """

    def __init__(self, stope_geom, drift_geom, pivot_geom) -> None:
        self.stope = sgeom.Polygon(stope_geom)
        self.drift = sgeom.Polygon(drift_geom)
        self.pivot = sgeom.Point(pivot_geom)

        self._stope_border = self.stope.exterior
        self._drift_border = self.drift.exterior

    def _find_endpoints(self, ray: sgeom.LineString, max_length: float
                        ) -> Tuple[Optional[sgeom.Point], Optional[sgeom.Point]]:
        """
        Encuentra collar (intersección con galería) y fondo (intersección con caserón).
        Respeta `max_length` acortando sobre la recta del tiro si es necesario.
        """
        coll_int = ray.intersection(self._drift_border)
        if coll_int.is_empty:
            return None, None
        collar_candidates = _sort_points(coll_int, self.pivot)
        if not collar_candidates:
            return None, None
        collar = collar_candidates[0]

        toes_int = ray.intersection(self._stope_border)
        toe_candidates = _sort_points(toes_int, self.pivot)
        if not toe_candidates:
            return None, None
        toe = toe_candidates[-1]

        if self.pivot.distance(toe) > max_length:
            dist_pc = self.pivot.distance(collar)
            toe = ray.interpolate(dist_pc + max_length)

        return collar, toe

    @staticmethod
    def _valid_hole(collar: Optional[sgeom.Point],
                    toe: Optional[sgeom.Point],
                    min_length: float,
                    stope: sgeom.Polygon) -> bool:
        """Filtra tiros no válidos por longitud mínima o por no intersectar el stope."""
        if not (collar and toe):
            return False
        hole = sgeom.LineString([collar, toe])
        if hole.length < min_length:
            return False
        return hole.intersects(stope)

    # ---------- Métodos de construcción ----------

    def generate_angular(self, params: Dict) -> Dict:
        """
        Espaciamiento angular constante.

        params:
          - min_angle, max_angle : float (grados)
          - holes_number : int
          - max_length : float (m)
          - min_length : float (m)

        return: {"geometry": [[(x,y)..],[(x,y)..]], "params": params}
        """
        n = max(int(params.get("holes_number", 0)), 0)
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        max_len = float(params.get("max_length", 0.0))
        min_len = float(params.get("min_length", 0.1))
        a_step = (amax - amin) / (n - 1) if n > 1 else 0.0

        ref = sgeom.LineString([self.pivot, (self.pivot.x, self.pivot.y + 1e4)])
        collars, toes = [], []
        for i in range(n):
            ang = amin + i * a_step
            ray = saff.rotate(ref, angle=ang, origin=self.pivot)
            col, toe = self._find_endpoints(ray, max_len)
            if self._valid_hole(col, toe, min_len, self.stope):
                collars.append(list(col.coords)[0])
                toes.append(list(toe.coords)[0])

        return {"geometry": [collars, toes], "params": dict(params)}

    def generate_direct(self, params: Dict) -> Dict:
        """
        “Directo”: intenta mantener distancia `spacing` entre fondos consecutivos.

        params:
          - spacing : float (m)
          - min_angle, max_angle : float (deg)
          - max_length : float (m)
          - min_length : float (m)
        """
        spacing = float(params.get("spacing", 0.0))
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        max_len = float(params.get("max_length", 0.0))
        min_len = float(params.get("min_length", 0.1))

        collars, toes = [], []
        ref = sgeom.LineString([self.pivot, (self.pivot.x, self.pivot.y + 1e4)])
        line = saff.rotate(ref, angle=amin, origin=self.pivot)

        col, toe = self._find_endpoints(line, max_len)
        if not self._valid_hole(col, toe, min_len, self.stope):
            return {"geometry": [[], []], "params": dict(params)}
        collars.append(list(col.coords)[0]); toes.append(list(toe.coords)[0])

        # Itera buscando puntos del borde del stope a distancia `spacing`
        for _ in range(200):
            circle = sgeom.Point(toe.x, toe.y).buffer(spacing).exterior
            ints = circle.intersection(self._stope_border)
            candidates = _sort_points(ints, self.pivot)
            if not candidates:
                break

            # Elegimos el que más aumenta el ángulo respecto a la línea anterior,
            # sin salir del rango [amin, amax].
            best, best_delta = None, -1e9
            for p in candidates:
                nxt = sgeom.LineString([self.pivot, p])
                d = _angle_between(line, nxt)
                abs_ang = _angle_between(ref, nxt)
                if amin <= abs_ang <= amax and d > best_delta:
                    best, best_delta = p, d

            if best is None:
                break

            toe = best
            line = sgeom.LineString([self.pivot, toe])
            col, _ = self._find_endpoints(line, max_len)
            if self._valid_hole(col, toe, min_len, self.stope):
                collars.append(list(col.coords)[0]); toes.append(list(toe.coords)[0])
            else:
                break

        return {"geometry": [collars, toes], "params": dict(params)}

    def generate_offset(self, params: Dict) -> Dict:
        """
        “Offset” (tangencia/offset perpendicular) – versión heurística estable.

        Idea:
          - Dispara el 1º a `min_angle`.
          - A partir del fondo completo, construye una circunferencia de radio `spacing`
            y busca un punto de avance angular consistente (lado del giro).
        """
        spacing = float(params.get("spacing", 0.0))
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        side_left = amax > amin  # True si vamos CCW
        max_len = float(params.get("max_length", 0.0))
        min_len = float(params.get("min_length", 0.1))

        collars, toes = [], []
        ref = sgeom.LineString([self.pivot, (self.pivot.x, self.pivot.y + 1e4)])
        line = saff.rotate(ref, angle=amin, origin=self.pivot)

        for _ in range(200):
            col, toe = self._find_endpoints(line, max_len)
            if not self._valid_hole(col, toe, min_len, self.stope):
                break
            collars.append(list(col.coords)[0]); toes.append(list(toe.coords)[0])

            # Fondo “completo” (sin max_length) para estimar dirección de avance
            _, full_toe = self._find_endpoints(line, 1e6)
            if full_toe is None:
                break

            # Puntos del borde del stope a distancia 'spacing'
            circle = sgeom.Point(full_toe.x, full_toe.y).buffer(spacing).exterior
            ints = circle.intersection(self._stope_border)
            candidates = _sort_points(ints, self.pivot)
            if not candidates:
                break

            # Elegimos candidato en el “lado” correcto y con avance angular
            best, best_delta = None, -1e9
            for p in candidates:
                nxt = sgeom.LineString([self.pivot, p])
                delta = _angle_between(line, nxt)
                abs_ang = _angle_between(ref, nxt)
                if side_left and delta > 0 and amin <= abs_ang <= amax and delta > best_delta:
                    best, best_delta = p, delta
                if (not side_left) and delta < 0 and amin <= abs_ang <= amax and abs(delta) > abs(best_delta):
                    best, best_delta = p, delta

            if best is None:
                break
            line = sgeom.LineString([self.pivot, best])

        return {"geometry": [collars, toes], "params": dict(params)}

    def generate_aeci(self, params: Dict) -> Dict:
        """
        “AECI”: avance casi-constante en contorno – versión heurística.

        Emulación:
          - Offset paralelo pequeño para “pegarse” al contorno.
          - Avance con offsets paralelos y corte perpendicular para saltar
            aproximadamente `spacing` en contorno (prototipo).
        """
        spacing = float(params.get("spacing", 0.0))
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        side = "left" if amax > amin else "right"
        max_len = float(params.get("max_length", 0.0))
        min_len = float(params.get("min_length", 0.1))

        collars, toes = [], []
        ref = sgeom.LineString([self.pivot, (self.pivot.x, self.pivot.y + 1e4)])
        line = saff.rotate(ref, angle=amin, origin=self.pivot)

        for _ in range(200):
            if not line.intersects(self.stope):
                break

            col, toe = self._find_endpoints(line, max_len)
            if not self._valid_hole(col, toe, min_len, self.stope):
                break
            collars.append(list(col.coords)[0]); toes.append(list(toe.coords)[0])

            # offset1 ~ “pegado” al contorno, offset2 ~ salto spacing
            off1 = line.parallel_offset(distance=0.5 * spacing, side=side)
            off2 = line.parallel_offset(distance=1.0 * spacing, side=side)
            ints = off1.intersection(self._stope_border)
            if ints.is_empty:
                break
            pivot_int = _sort_points(ints, self.pivot)[-1]
            perp = saff.rotate(off1, angle=(-90 if side == "left" else 90), origin=pivot_int)
            nxt_pt = perp.intersection(off2)
            if nxt_pt.is_empty or not isinstance(nxt_pt, sgeom.Point):
                break
            line = sgeom.LineString([self.pivot, nxt_pt])

        return {"geometry": [collars, toes], "params": dict(params)}


# ------------------------
# Diseño de cargas (stemming)
# ------------------------

class ChargeDesigner:
    """Geometría de cargas dentro de los tiros: recorta 'stemming' en el collar."""
    def get_charges(self, holes_design: Dict, charge_params: Dict) -> Dict:
        collars_out, toes_out = [], []
        hole_collars, hole_toes = holes_design['geometry']
        stemming = float(charge_params.get('stemming', 0.0))

        for collar_coord, toe_coord in zip(hole_collars, hole_toes):
            hole = sgeom.LineString([collar_coord, toe_coord])
            if hole.length > stemming:
                charge_collar = hole.interpolate(stemming)
                charge_toe = sgeom.Point(toe_coord)
                collars_out.append(list(charge_collar.coords)[0])
                toes_out.append(list(charge_toe.coords)[0])

        return {"geometry": [collars_out, toes_out]}


# ------------------------
# Evaluación de costos
# ------------------------

def _linear_mass_kg_per_m(diam_mm: float, dens_gcc: float) -> float:
    """
    Masa lineal (kg/m) de explosivo en carga cilíndrica.
    d_mm → m, dens(g/cc) → kg/m3.  π/4 * d^2 * dens.
    """
    d_m = max(float(diam_mm), 0.0) / 1000.0
    rho = max(float(dens_gcc), 0.0) * 1000.0
    return (np.pi / 4.0) * d_m * d_m * rho


class DesignEvaluator:
    """Costo total = Perforación + Detonadores + Explosivo."""
    @staticmethod
    def total_drilled_length(holes: Dict) -> float:
        geo = holes.get("geometry", [[], []])
        if not geo or len(geo) != 2 or len(geo[0]) == 0 or len(geo[0]) != len(geo[1]):
            return 0.0
        a = np.array(geo[0], dtype=float)
        b = np.array(geo[1], dtype=float)
        return float(np.sum(np.linalg.norm(b - a, axis=1)))

    @staticmethod
    def total_charge_length(charges: Dict) -> float:
        geo = charges.get("geometry", [[], []])
        if not geo or len(geo) != 2 or len(geo[0]) == 0 or len(geo[0]) != len(geo[1]):
            return 0.0
        a = np.array(geo[0], dtype=float)
        b = np.array(geo[1], dtype=float)
        return float(np.sum(np.linalg.norm(b - a, axis=1)))

    def calculate_total_cost(self, design: Dict, unit_costs_or_params: Dict) -> float:
        """
        unit_costs_or_params puede ser:
        - dict con clave "unit_costs" que contiene los costos/propiedades, o
        - el dict de unit_costs directamente.
        """
        unit_costs = unit_costs_or_params.get("unit_costs", unit_costs_or_params)

        Cp = float(unit_costs.get("perforacion_por_metro", 0.0))
        Cd = float(unit_costs.get("detonador_por_unidad", 0.0))
        Ce = float(unit_costs.get("explosivo_por_kg", 0.0))
        dens_gcc = float(unit_costs.get("densidad_explosivo_gcc", 0.0))
        d_mm = float(unit_costs.get("diametro_carga_mm", 0.0))

        holes = design.get("holes", {})
        charges = design.get("charges", {})

        L_perfo = self.total_drilled_length(holes)
        n_tiros = len(holes.get("geometry", [[], []])[0]) if holes.get("geometry") else 0

        L_carga = self.total_charge_length(charges)
        ql = _linear_mass_kg_per_m(d_mm, dens_gcc)  # kg/m
        masa = L_carga * ql  # kg

        return L_perfo * Cp + n_tiros * Cd + masa * Ce


# -------------
# Optimizador
# -------------

class Optimizer:
    """
    Recorre S = Smin:Smax y devuelve el diseño válido (<= presupuesto) de menor costo.
    - Método 'angular' → S = número de tiros.
    - 'directo'/'offset'/'aeci' → S = spacing (m).
    Incluye meta: método, S usado y etiqueta de S.
    """

    def __init__(self, generator: DrillFanGenerator,
                 charge_designer: ChargeDesigner,
                 evaluator: DesignEvaluator) -> None:
        self.generator = generator
        self.charge_designer = charge_designer
        self.evaluator = evaluator

    def run(self, all_params: Dict, log: Callable[[str], None]) -> Optional[Dict]:
        method = (all_params.get("design_method") or "angular").lower()
        s_min = int(all_params.get("s_min", 5))
        s_max = int(all_params.get("s_max", 15))
        budget = float(all_params.get("presupuesto_maximo", 0.0))

        # parámetros geométricos flexibles
        min_angle = float(all_params.get("min_angle", -45.0))
        max_angle = float(all_params.get("max_angle", 45.0))
        min_length = float(all_params.get("min_length", 0.3))
        max_length = float(all_params.get("max_length", 30.0))
        stemming = float(all_params.get("stemming", 0.0))

        s_label = "N° tiros" if method == "angular" else "Spacing [m]"
        log(f"▶ Método: {method} | S={s_min}:{s_max} ({s_label}) | Presupuesto={budget:,.2f}")

        solutions: List[Dict] = []
        for S in range(s_min, s_max + 1):
            log(f"\n— Probando S={S} …")

            # Parámetros al generador
            base = {
                "min_angle": min_angle,
                "max_angle": max_angle,
                "min_length": min_length,
                "max_length": max_length,
            }
            if method == "angular":
                if S < 2:
                    log("   · Omitido: Método angular requiere al menos 2 tiros.")
                    continue
                gen_params = {**base, "holes_number": S}
            else:
                gen_params = {**base, "spacing": float(S)}

            # Generación de tiros
            gen_func = getattr(self.generator, f"generate_{method}", self.generator.generate_angular)
            holes = gen_func(gen_params)
            if not holes["geometry"][0]:
                log("   · Geometría de perforación vacía/no válida.")
                continue

            # Geometría de cargas
            charges = self.charge_designer.get_charges(holes, {"stemming": stemming})

            # Diseño completo y costo
            design = {"holes": holes, "charges": charges}
            cost = self.evaluator.calculate_total_cost(design, all_params)
            log(f"   · {s_label}={S} | Tiros={len(holes['geometry'][0])} | Costo={cost:,.2f}")

            if cost <= budget:
                log("   · ✅ Dentro del presupuesto")
                solutions.append({"design": design, "cost": cost,
                                  "meta": {"method": method, "S_used": S, "S_label": s_label}})
            else:
                log("   · ❌ Excede presupuesto")

        if not solutions:
            log("\n✖ No se encontró diseño válido.")
            return None

        best = min(solutions, key=lambda d: d["cost"])
        log(f"\n🏁 Mejor costo = {best['cost']:,.2f} | {best['meta']['S_label']} usado = {best['meta']['S_used']}")
        return best


# -----
# Model
# -----

class Model:
    """Fachada: instancia generador, diseñador de cargas, evaluador y optimizador."""
    def __init__(self) -> None:
        self.generator: Optional[DrillFanGenerator] = None
        self.charge_designer = ChargeDesigner()
        self.evaluator = DesignEvaluator()
        self.optimizer: Optional[Optimizer] = None

    def update_geometry(self, stope_geom, drift_geom, pivot_geom):
        """Configura/actualiza el contexto geométrico y crea el optimizador."""
        self.generator = DrillFanGenerator(stope_geom, drift_geom, pivot_geom)
        self.optimizer = Optimizer(self.generator, self.charge_designer, self.evaluator)
