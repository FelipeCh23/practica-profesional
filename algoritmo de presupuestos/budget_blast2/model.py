# model.py
"""
Modelo (lógica de negocio) para generación de abanicos, diseño de cargas,
evaluación de costo y búsqueda del mejor diseño.

Incluye cuatro métodos de diseño geométrico (fieles a appRing):
- angular  : separación angular constante (control por número de tiros).
- directo  : separación constante entre fondos (control por espaciamiento S).
- offset   : tangencia a círculo en el fondo anterior (control por S).
- aeci     : avance casi constante sobre contorno, con offsets paralelos (control por S).

El optimizador recorre S en un rango (o N° de tiros para 'angular'),
evalúa costo y devuelve el mejor por costo + la lista completa de alternativas válidas.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import shapely.affinity as saff
import shapely.geometry as sgeom
import shapely.ops as sops


# =========================
# Utilidades geométricas
# =========================

def _sort_points(geometry, pivot: sgeom.Point) -> List[sgeom.Point]:
    """
    Ordena puntos por distancia a un pivote.

    Parámetros
    ----------
    geometry : shapely BaseGeometry
        Resultado de una intersección que puede contener uno o más puntos.
    pivot : shapely Point
        Punto de referencia para computar distancia (pivote de perforación).

    Returns
    -------
    list[Point]
        Lista de puntos ordenados por distancia creciente al pivote.
    """
    if geometry is None or geometry.is_empty:
        return []
    pts = [g for g in getattr(geometry, "geoms", [geometry])
           if isinstance(g, sgeom.Point)]
    pts.sort(key=lambda p: p.distance(pivot))
    return pts


def _angle_between(line_a: sgeom.LineString, line_b: sgeom.LineString) -> float:
    """
    Ángulo firmado (en grados) entre dos líneas con el mismo origen.

    Fórmula
    -------
    Sean v_a y v_b los vectores unitarios de las líneas. El ángulo firmado θ se calcula como:
        θ = atan2( det(v_a, v_b), dot(v_a, v_b) )   [radianes]
    y luego se convierte a grados.

    Returns
    -------
    float
        Ángulo en grados (rango -180..+180). Positivo = giro antihorario.
    """
    (ax1, ay1), (ax2, ay2) = list(line_a.coords)[:2]
    (bx1, by1), (bx2, by2) = list(line_b.coords)[:2]
    va = np.array([ax2 - ax1, ay2 - ay1], dtype=float)
    vb = np.array([bx2 - bx1, by2 - by1], dtype=float)
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    va /= na
    vb /= nb
    dot = float(np.clip(np.dot(va, vb), -1.0, 1.0))
    det = float(va[0] * vb[1] - va[1] * vb[0])
    return float(np.degrees(np.arctan2(det, dot)))


def _get_tangents(center: sgeom.Point, radius: float, ext_point: sgeom.Point):
    """
    Puntos de tangencia desde `ext_point` hacia la circunferencia (center, radius).

    Idea geométrica
    ---------------
    Dados un centro y un punto exterior, los puntos de tangencia son la intersección
    entre la circunferencia principal y otra circunferencia cuyo diámetro es el
    segmento 'ext_point - center' (teorema de Tales).

    Returns
    -------
    shapely BaseGeometry
        MultiPoint con 0, 1 o 2 puntos de tangencia.
    """
    circle = center.buffer(radius).exterior
    seg = sgeom.LineString([ext_point, center])
    if seg.length < 1e-6:
        return sgeom.MultiPoint()
    mid = seg.interpolate(0.5, normalized=True)
    mid_radius = 0.5 * seg.length
    if mid_radius < 1e-6:
        return sgeom.MultiPoint()
    mid_circle = mid.buffer(mid_radius).exterior
    return circle.intersection(mid_circle)


def _point_side(line: sgeom.LineString, point: sgeom.Point) -> str:
    """
    Lado relativo de un punto respecto a una línea orientada.

    Returns
    -------
    str
        'left' si queda a la izquierda, 'right' si a la derecha, 'over' si está sobre.
    """
    p1, p2 = line.coords
    d = (point.x - p1[0]) * (p2[1] - p1[1]) - (point.y - p1[1]) * (p2[0] - p1[0])
    if d > 1e-6:
        return "right"
    if d < -1e-6:
        return "left"
    return "over"


def _fix_polygon(coords: List[List[float]]) -> sgeom.Polygon:
    """
    Crea un polígono válido a partir de coords; intenta reparar auto-intersecciones.

    Estrategia
    ----------
    - Crea Polygon.
    - Si es inválido o tiene self-intersection, usa buffer(0) para corregir.
    - Si por alguna razón sigue inválido o vacío, cae a un rectángulo mínimo.

    Returns
    -------
    shapely Polygon
    """
    try:
        poly = sgeom.Polygon(coords)
    except Exception:
        poly = sgeom.Polygon()

    if (poly.is_empty or not poly.is_valid) and len(coords) >= 3:
        try:
            fixed = poly.buffer(0)
            if not fixed.is_empty and fixed.is_valid:
                # si devuelve MultiPolygon, coge el mayor por área
                if hasattr(fixed, "geoms"):
                    fixed = max(fixed.geoms, key=lambda g: g.area)
                poly = fixed
        except Exception:
            pass

    if poly.is_empty or not poly.is_valid:
        # fallback muy básico
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        x0, x1 = (min(xs), max(xs)) if xs else (0.0, 1.0)
        y0, y1 = (min(ys), max(ys)) if ys else (0.0, 1.0)
        poly = sgeom.Polygon([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    return poly


# ======================================
# Generador geométrico de abanicos 2D
# ======================================

class DrillFanGenerator:
    """
    Genera tiros (collar/fondo) de un abanico 2D dentro de un caserón.

    Parámetros del constructor
    -------------------------
    stope_geom : list[list[float]]
        Polígono del caserón (x, y) en metros.
    drift_geom : list[list[float]]
        Polígono de la galería (x, y) en metros.
    pivot_geom : list[float]
        Punto pivote (x, y) desde donde abren los tiros.
    """

    def __init__(self, stope_geom, drift_geom, pivot_geom) -> None:
        self.stope = _fix_polygon(stope_geom)
        self.drift = _fix_polygon(drift_geom)
        self.pivot = sgeom.Point(pivot_geom)

        self._stope_border = self.stope.exterior
        self._drift_border = self.drift.exterior

    # ---------- auxiliares internos ----------

    def _find_endpoints(
        self, ray: sgeom.LineString, max_length: float
    ) -> Tuple[Optional[sgeom.Point], Optional[sgeom.Point]]:
        """
        Encuentra el collar (intersección con galería) y el fondo (con caserón).
        Si la longitud excede `max_length`, recorta el fondo sobre la línea.

        Parámetros
        ----------
        ray : LineString
            Rayo desde el pivote en una dirección dada.
        max_length : float
            Longitud máxima permitida (m) del tiro.

        Returns
        -------
        (Point|None, Point|None)
            (collar, toe). Si no hay intersecciones válidas, retorna (None, None).
        """
        coll_int = ray.intersection(self._drift_border)
        if coll_int.is_empty:
            return None, None
        collar_candidates = _sort_points(coll_int, self.pivot)
        if not collar_candidates:
            return None, None
        collar = collar_candidates[0]

        toes_int = ray.intersection(self._stope_border)
        if toes_int.is_empty:
            return None, None
        toe_candidates = _sort_points(toes_int, self.pivot)
        if not toe_candidates:
            return None, None
        toe = toe_candidates[-1]

        # recorte por longitud máxima (desde collar)
        if collar.distance(toe) > max_length:
            seg = sgeom.LineString([collar, toe])
            toe = seg.interpolate(max_length)

        return collar, toe

    def _is_valid_hole(
        self,
        collar: Optional[sgeom.Point],
        toe: Optional[sgeom.Point],
        min_length: float,
        stope: sgeom.Polygon
    ) -> bool:
        """
        Valida un tiro por longitud mínima y que cruce el caserón.

        Returns
        -------
        bool
            True si hay collar y toe, longitud >= min_length e interseca el stope.
        """
        if not (collar and toe):
            return False
        hole = sgeom.LineString([collar, toe])
        if hole.length < min_length:
            return False
        return hole.intersects(stope)

    # ---- helpers robustos para AECI ----

    def _safe_parallel_offset(
        self, line: sgeom.LineString, distance: float, side: str
    ) -> Optional[sgeom.LineString]:
        """
        Devuelve un LineString usable para el offset paralelo de 'line'.
        - Si Shapely devuelve MultiLineString, toma el segmento más cercano al pivote.
        - Si falla o queda vacío, retorna None.
        """
        try:
            g = line.parallel_offset(distance=distance, side=side, join_style=2)
        except Exception:
            return None
        if g.is_empty:
            return None
        geoms = getattr(g, "geoms", [g])
        best = min(geoms, key=lambda seg: seg.distance(self.pivot))
        if isinstance(best, sgeom.LineString):
            return best
        if hasattr(best, "coords"):
            return sgeom.LineString(best.coords)
        return None

    def _nearest_on(self, geometry, ref: sgeom.Point) -> Optional[sgeom.Point]:
        """
        Devuelve un 'Point' representativo en 'geometry' cercano a 'ref':
        - Si geometry es Point → lo devuelve.
        - Si es MultiPoint → el más cercano a 'ref'.
        - Si es LineString/MultiLineString → toma el punto proyectado sobre el tramo más cercano.
        - Si es Polygon → punto proyectado sobre el borde más cercano.
        """
        if geometry is None or geometry.is_empty:
            return None

        if isinstance(geometry, sgeom.Point):
            return geometry

        pts: List[sgeom.Point] = []
        for g in getattr(geometry, "geoms", [geometry]):
            if isinstance(g, sgeom.Point):
                pts.append(g)
            elif isinstance(g, (sgeom.LineString, sgeom.LinearRing)):
                d = g.project(ref)
                pts.append(g.interpolate(d))
            elif isinstance(g, sgeom.Polygon):
                ring = g.exterior
                d = ring.project(ref)
                pts.append(ring.interpolate(d))

        if not pts:
            return None
        return min(pts, key=lambda p: p.distance(ref))

    # ---------- Métodos de construcción (fieles a appRing) ----------

    def generate_angular(self, params: Dict) -> Dict:
        """
        Espaciamiento angular constante (implementación iterativa fiel a appRing).

        Parámetros esperados (dict)
        ---------------------------
        min_angle, max_angle : float
            Rango angular (grados).
        holes_number : int
            Número de tiros a distribuir en el abanico.
        max_length : float
            Longitud máxima por tiro (m).
        min_length : float, opcional
            Longitud mínima por tiro (m). Default = 0.1.

        Returns
        -------
        dict
            {"geometry": [[collars...], [toes...]], "params": params}
        """
        n = max(int(params.get("holes_number", 0)), 0)
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        max_len = float(params.get("max_length", 0.0))
        min_len = float(params.get("min_length", 0.1))

        spacing = (amax - amin) / (n - 1) if n > 1 else 0.0
        line = sgeom.LineString([self.pivot, (self.pivot.x, self.pivot.y + 1e4)])
        line = saff.rotate(line, angle=amin, origin=self.pivot)

        collars, toes = [], []
        for _ in range(n):
            col, toe = self._find_endpoints(line, max_len)
            if self._is_valid_hole(col, toe, min_len, self.stope):
                collars.append(list(col.coords)[0])
                toes.append(list(toe.coords)[0])
            line = saff.rotate(line, angle=spacing, origin=self.pivot)

        return {"geometry": [collars, toes], "params": dict(params)}

    def generate_direct(self, params: Dict) -> Dict:
        """
        “Directo”: mantiene distancia `spacing` entre los fondos consecutivos.

        Parámetros esperados (dict)
        ---------------------------
        spacing : float
            Espaciamiento buscado entre fondos (m).
        min_angle, max_angle : float
            Rango angular (grados).
        max_length, min_length : float
            Longitud máxima y mínima por tiro (m).

        Returns
        -------
        dict
            {"geometry": [[collars...], [toes...]], "params": params}
        """
        spacing = float(params.get("spacing", 0.0))
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        max_len = float(params.get("max_length", 0.0))
        min_len = float(params.get("min_length", 0.1))

        collars, toes = [], []
        ref = sgeom.LineString([self.pivot, (self.pivot.x, self.pivot.y + 1e4)])
        line = saff.rotate(ref, angle=amin, origin=self.pivot)

        # primer tiro
        col, toe = self._find_endpoints(line, max_len)
        if not self._is_valid_hole(col, toe, min_len, self.stope):
            return {"geometry": [[], []], "params": dict(params)}
        collars.append(list(col.coords)[0])
        toes.append(list(toe.coords)[0])

        for _ in range(400):
            circle = sgeom.Point(toe.x, toe.y).buffer(spacing).exterior
            ints = circle.intersection(self._stope_border)
            if ints.is_empty or not hasattr(ints, "geoms"):
                break

            # elegir el que más avanza angularmente y queda dentro de límites
            best, best_delta = None, -1e9
            for p in ints.geoms:
                nxt = sgeom.LineString([self.pivot, p])
                d = _angle_between(line, nxt)
                abs_ang = _angle_between(ref, nxt)
                if amin <= abs_ang <= amax and d > best_delta:
                    best, best_delta = p, d

            if best is None:
                break
            if best.distance(toe) < 1e-6:  # corte de seguridad: sin avance
                break

            toe = best
            line = sgeom.LineString([self.pivot, toe])
            col, _ = self._find_endpoints(line, max_len)
            if self._is_valid_hole(col, toe, min_len, self.stope):
                collars.append(list(col.coords)[0])
                toes.append(list(toe.coords)[0])
            else:
                break

        return {"geometry": [collars, toes], "params": dict(params)}

    def generate_offset(self, params: Dict) -> Dict:
        """
        “Offset” (tangencia/offset perpendicular) – implementación fiel a appRing.

        Parámetros esperados (dict)
        ---------------------------
        spacing : float
            Radio de tangencia utilizado para posicionar el siguiente fondo (m).
        min_angle, max_angle : float
            Rango angular (grados).
        max_length, min_length : float
            Longitud máxima y mínima por tiro (m).

        Returns
        -------
        dict
            {"geometry": [[collars...], [toes...]], "params": params}
        """
        spacing = float(params.get("spacing", 0.0))
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        side_left = amax > amin
        max_len = float(params.get("max_length", 0.0))
        min_len = float(params.get("min_length", 0.1))

        collars, toes = [], []
        ref = sgeom.LineString([self.pivot, (self.pivot.x, self.pivot.y + 1e4)])
        line = saff.rotate(ref, angle=amin, origin=self.pivot)

        for _ in range(400):
            col, toe = self._find_endpoints(line, max_len)
            if not self._is_valid_hole(col, toe, min_len, self.stope):
                break

            collars.append(list(col.coords)[0])
            toes.append(list(toe.coords)[0])

            # usar fondo “largo” para tangencia (sin max_length)
            _, full_toe = self._find_endpoints(line, 1e6)
            if full_toe is None:
                break

            tang = _get_tangents(full_toe, spacing, self.pivot)
            if tang.is_empty or not hasattr(tang, "geoms"):
                break

            # elegir el punto del lado correcto
            desired_side = "left" if side_left else "right"
            pts = [p for p in tang.geoms if _point_side(line, p) == desired_side]
            if not pts:
                break

            # corte de seguridad: si no avanza respecto del último toe
            if toes and pts[0].distance(sgeom.Point(toes[-1])) < 1e-6:
                break

            line = sgeom.LineString([self.pivot, pts[0]])

        return {"geometry": [collars, toes], "params": dict(params)}

    def generate_aeci(self, params: Dict) -> Dict:
        """
        “AECI”: avance casi-constante en contorno con offsets paralelos (fiel a appRing),
        reforzado para espaciamientos grandes y retornos complejos de Shapely.

        Parámetros esperados (dict)
        ---------------------------
        spacing : float
            Espaciamiento buscado entre fondos (m).
        min_angle, max_angle : float
            Rango angular (grados).
        max_length, min_length : float
            Longitud máxima y mínima por tiro (m).

        Returns
        -------
        dict
            {"geometry": [[collars...], [toes...]], "params": params}
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

        # Cap de spacing por dimensión del caserón (evita objetivos imposibles)
        min_dim = min(
            (self.stope.bounds[2] - self.stope.bounds[0]),
            (self.stope.bounds[3] - self.stope.bounds[1]),
        )
        spacing_cap = 0.9 * max(1e-6, min_dim)
        eff_spacing = min(spacing, spacing_cap) if spacing > 0 else 0.0

        for _ in range(400):
            if not line.intersects(self.stope):
                break

            col, toe = self._find_endpoints(line, max_len)
            if not self._is_valid_hole(col, toe, min_len, self.stope):
                break

            collars.append(list(col.coords)[0])
            toes.append(list(toe.coords)[0])

            # Intentos con backoff si offsets fallan
            attempts = 0
            next_line = None
            local_spacing = eff_spacing

            while attempts < 3 and next_line is None:
                off1 = self._safe_parallel_offset(line, 0.5 * local_spacing, side)
                off2 = self._safe_parallel_offset(line, 1.0 * local_spacing, side)
                if off1 is None or off2 is None:
                    attempts += 1
                    local_spacing *= 0.8
                    continue

                ints = off1.intersection(self._stope_border)
                if ints.is_empty:
                    attempts += 1
                    local_spacing *= 0.8
                    continue

                pivot_int = _sort_points(ints, self.pivot)[-1] if hasattr(ints, "geoms") else self._nearest_on(ints, self.pivot)
                if pivot_int is None:
                    attempts += 1
                    local_spacing *= 0.8
                    continue

                perp = saff.rotate(off1, angle=(-90 if side == "left" else 90), origin=pivot_int)
                nxt_geom = perp.intersection(off2)
                nxt_pt = nxt_geom if isinstance(nxt_geom, sgeom.Point) else self._nearest_on(nxt_geom, pivot_int)
                if nxt_pt is None:
                    attempts += 1
                    local_spacing *= 0.8
                    continue

                cand = sgeom.LineString([self.pivot, nxt_pt])
                abs_ang = _angle_between(ref, cand)
                if not (amin <= abs_ang <= amax):
                    attempts += 1
                    local_spacing *= 0.8
                    continue

                if toes and nxt_pt.distance(sgeom.Point(toes[-1])) < 1e-6:
                    attempts += 1
                    local_spacing *= 0.8
                    continue

                next_line = cand  # éxito

            if next_line is None:
                break

            line = next_line
            eff_spacing = local_spacing  # mantener spacing efectivo

        return {"geometry": [collars, toes], "params": dict(params)}


# =========================
# Diseñador de cargas
# =========================

class ChargeDesigner:
    """
    Genera la geometría de las cargas (columna de explosivo) dentro de cada tiro.

    Parámetros (de entrada a `get_charges`)
    --------------------------------------
    holes_design : dict
        {"geometry": [collars, toes]} con listas de pares (x, y).
    charge_params : dict
        stemming : float
            Longitud de taco en collar (m) sin explosivo.
    """

    def get_charges(self, holes_design: Dict, charge_params: Dict) -> Dict:
        """
        Devuelve la geometría de las cargas como líneas desde el punto
        a 'stemming' m del collar hasta el toe de cada tiro.

        Returns
        -------
        dict
            {"geometry": [[charge_collars...], [charge_toes...]]}
        """
        collars_out, toes_out = [], []
        geo = holes_design.get("geometry", [[], []])
        if not geo or len(geo) != 2 or not geo[0]:
            return {"geometry": [[], []]}

        hole_collars, hole_toes = geo
        stemming = float(charge_params.get("stemming", 0.0))

        for c_coord, t_coord in zip(hole_collars, hole_toes):
            hole = sgeom.LineString([c_coord, t_coord])
            if hole.length > stemming:
                charge_collar = hole.interpolate(stemming)
                charge_toe = sgeom.Point(t_coord)
                collars_out.append(list(charge_collar.coords)[0])
                toes_out.append(list(charge_toe.coords)[0])

        return {"geometry": [collars_out, toes_out]}


# =========================
# Evaluación de costos
# =========================

class DesignEvaluator:
    """
    Calcula métricas y costos de un diseño.

    Costos considerados
    -------------------
    Perforación:  C_perf = L_total_perforado * Cp
    Detonadores:  C_det  = N_tiros * Cd
    Explosivo:    C_exp  = M_total_explosivo * Ce

    Donde:
    - L_total_perforado = suma de longitudes de todos los tiros.
    - M_total_explosivo = q_l * L_total_carga, con
        q_l [kg/m] = (π/4) * (D_mm/1000)^2 * (ρ_g/cc * 1000)
                   = 7.854e-4 * ρ_gcc * D_mm^2
    """

    def total_drilled_length(self, holes: Dict) -> float:
        """
        Longitud total perforada [m].

        Returns
        -------
        float
            Suma de las longitudes de todos los tiros.
        """
        geo = holes.get("geometry", [[], []])
        if not geo or len(geo) != 2 or len(geo[0]) == 0 or len(geo[0]) != len(geo[1]):
            return 0.0
        a = np.array(geo[0], dtype=float)
        b = np.array(geo[1], dtype=float)
        return float(np.sum(np.linalg.norm(b - a, axis=1)))

    def total_charge_length(self, charges: Dict) -> float:
        """
        Longitud total de columna de carga [m].

        Returns
        -------
        float
            Suma de longitudes de todas las columnas de explosivo.
        """
        geo = charges.get("geometry", [[], []])
        if not geo or len(geo) != 2 or len(geo[0]) == 0 or len(geo[0]) != len(geo[1]):
            return 0.0
        a = np.array(geo[0], dtype=float)
        b = np.array(geo[1], dtype=float)
        return float(np.sum(np.linalg.norm(b - a, axis=1)))

    def calculate_total_cost(self, design: Dict, unit_costs: Dict) -> float:
        """
        Costo total (perforación + detonadores + explosivo).

        Parámetros
        ----------
        design : dict
            {"holes": {...}, "charges": {...}} (charges opcional).
        unit_costs : dict
            perforacion_por_metro : float ($/m)
            detonador_por_unidad  : float ($/u)
            explosivo_por_kg      : float ($/kg)
            densidad_explosivo_gcc: float (g/cc)
            diametro_carga_mm     : float (mm)

        Returns
        -------
        float
            Costo total en unidades monetarias del usuario.
        """
        Cp = float(unit_costs.get("perforacion_por_metro", 0.0))
        Cd = float(unit_costs.get("detonador_por_unidad", 0.0))
        Ce = float(unit_costs.get("explosivo_por_kg", 0.0))
        rho = float(unit_costs.get("densidad_explosivo_gcc", 0.0))
        dmm = float(unit_costs.get("diametro_carga_mm", 0.0))

        holes = design.get("holes", {})
        charges = design.get("charges", {})

        # perforación
        L = self.total_drilled_length(holes)
        C_perf = L * Cp

        # detonadores
        n_tiros = len(holes.get("geometry", [[], []])[0]) if holes.get("geometry") else 0
        C_det = n_tiros * Cd

        # explosivo
        Lc = self.total_charge_length(charges)
        ql = 7.854e-4 * rho * (dmm ** 2)  # kg/m (ver docstring)
        M_total = Lc * ql
        C_exp = M_total * Ce

        return float(C_perf + C_det + C_exp)


# =========================
# Optimizador
# =========================

class Optimizer:
    """
    Recorre S en el rango dado (o N para 'angular'), evalúa costo y conserva
    todas las alternativas válidas. Devuelve el mejor por costo y la lista completa.
    """

    def __init__(self, generator: DrillFanGenerator, charge_designer: ChargeDesigner,
                 evaluator: DesignEvaluator) -> None:
        self.generator = generator
        self.charge_designer = charge_designer
        self.evaluator = evaluator

    def run(self, cfg: Dict, log: Callable[[str], None]) -> Optional[Dict]:
        """
        Ejecuta la optimización.

        Parámetros
        ----------
        cfg : dict
            Debe incluir:
              - design_method: {'angular'|'directo'|'offset'|'aeci'}
              - s_min, s_max: int (para 'angular' es N_tiros; para otros es S en m)
              - presupuesto_maximo: float
              - min_angle, max_angle, min_length, max_length
              - stemming (para cargas)
              - unit_costs: dict (ver DesignEvaluator)
        log : callable
            Función para imprimir mensajes en la UI.

        Returns
        -------
        dict | None
            Si hay válidos:
              {
                "best":   {"S", "method", "design", "cost", "num_holes"},
                "trials": [ ... mismas claves por cada alternativa válida ... ]
              }
            Si no hay válidos: None
        """
        method = (cfg.get("design_method") or "angular").lower()
        smin = int(cfg.get("s_min", 5))
        smax = int(cfg.get("s_max", 15))
        budget = float(cfg.get("presupuesto_maximo", 0.0))
        unit_costs = dict(cfg.get("unit_costs", {}))

        unit = "tiros" if method == "angular" else "m (S)"
        log(f"▶ Método: {method} | S={smin}:{smax} {unit} | Presupuesto={budget:,.2f}")

        trials: List[Dict] = []
        for S in range(smin, smax + 1):
            log(f"\n— Probando S={S} …")
            base = {
                "min_angle": float(cfg.get("min_angle", -45.0)),
                "max_angle": float(cfg.get("max_angle", 45.0)),
                "max_length": float(cfg.get("max_length", 30.0)),
                "min_length": float(cfg.get("min_length", 0.3)),
            }

            # generar tiros según método
            if method == "angular":
                holes = self.generator.generate_angular({**base, "holes_number": S})
            elif method == "directo":
                holes = self.generator.generate_direct({**base, "spacing": float(S)})
            elif method == "offset":
                holes = self.generator.generate_offset({**base, "spacing": float(S)})
            elif method == "aeci":
                holes = self.generator.generate_aeci({**base, "spacing": float(S)})
            else:
                holes = self.generator.generate_angular({**base, "holes_number": S})

            if not holes["geometry"][0]:
                log("   · Geometría vacía/no válida.")
                continue

            # diseñar cargas
            charges = self.charge_designer.get_charges(
                holes,
                {"stemming": float(cfg.get("stemming", 0.0))}
            )
            design = {"holes": holes, "charges": charges}

            cost = self.evaluator.calculate_total_cost(design, unit_costs)
            n_tiros = len(holes["geometry"][0])
            log(f"   · Tiros={n_tiros} | Costo={cost:,.2f}")

            if cost <= budget:
                log("   · ✅ Dentro del presupuesto")
                trials.append({
                    "S": S,
                    "method": method,
                    "design": design,
                    "cost": float(cost),
                    "num_holes": int(n_tiros),
                })
            else:
                log("   · ❌ Excede presupuesto")

        if not trials:
            log("\n✖ No se encontró diseño válido.")
            return None

        best = min(trials, key=lambda d: d["cost"])
        log(f"\n🏁 Mejor costo = {best['cost']:,.2f} | método={method} | S={best['S']}")

        return {"best": best, "trials": trials}


# =========================
# Fachada del modelo
# =========================

class Model:
    """
    Fachada: instancia generador, diseñador de cargas, evaluador y optimizador.

    Geometría de ejemplo (editable luego con `update_geometry`):
    - Caserón: rectángulo 11 x 8.5 m aprox.
    - Galería: rectángulo centrado de 5 x 4 m.
    - Pivote : en el origen (0, 0).
    """

    def __init__(self) -> None:
        # Geometría por defecto (ajústala desde la UI)
        stope_geom = [[-5.0, -4.0], [6.0, -4.0], [6.0, 4.5], [-5.0, 4.5]]
        drift_geom = [[-2.5, -2.0], [2.5, -2.0], [2.5, 2.0], [-2.5, 2.0]]
        pivot_geom = [0.0, 0.0]

        self.generator = DrillFanGenerator(stope_geom, drift_geom, pivot_geom)
        self.charge_designer = ChargeDesigner()
        self.evaluator = DesignEvaluator()
        self.optimizer = Optimizer(self.generator, self.charge_designer, self.evaluator)

    def update_geometry(self, stope_geom, drift_geom, pivot_geom) -> None:
        """
        Actualiza las geometrías base del modelo. Repara polígonos inválidos.

        Parámetros
        ----------
        stope_geom : list[list[float]]
            Polígono del caserón.
        drift_geom : list[list[float]]
            Polígono de la galería.
        pivot_geom : list[float]
            Punto pivote (x, y).
        """
        self.generator = DrillFanGenerator(stope_geom, drift_geom, pivot_geom)
        self.optimizer = Optimizer(self.generator, self.charge_designer, self.evaluator)
