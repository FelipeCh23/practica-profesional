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

# ======================================
# Generador geométrico de abanicos 2D
# ======================================

class DrillFanGenerator:
    """
    Genera tiros (collar/fondo) de un abanico 2D dentro de un caserón minero.

    Esta clase implementa los cuatro métodos geométricos de diseño:
    - 'angular' → separación angular constante (control por número de tiros)
    - 'directo' → separación constante entre fondos consecutivos
    - 'offset'  → tangencia entre círculos consecutivos (método clásico)
    - 'aeci'    → avance casi constante en el contorno (offsets paralelos)

    Cada método devuelve la geometría (collares y fondos) del abanico.

    Parámetros
    ----------
    stope_geom : list[list[float]]
        Coordenadas (x, y) del polígono del caserón en metros.
    drift_geom : list[list[float]]
        Coordenadas (x, y) del polígono de la galería.
    pivot_geom : list[float]
        Punto (x, y) del pivote de perforación (puede estar dentro o fuera de la galería).
    """

    def __init__(self, stope_geom, drift_geom, pivot_geom) -> None:
        # Geometrías base
        self.stope = _fix_polygon(stope_geom)
        self.drift = _fix_polygon(drift_geom)
        self.pivot = sgeom.Point(pivot_geom)

        self._stope_border = self.stope.exterior
        self._drift_border = self.drift.exterior

        # ----------------------------
        # NORMALIZACIÓN GEOMÉTRICA
        # ----------------------------
        # 1️⃣ Si el pivote está dentro del caserón, muévelo hacia abajo (1 m bajo la base)
        if self.stope.contains(self.pivot):
            miny = self.stope.bounds[1]
            self.pivot = sgeom.Point(self.pivot.x, miny - 1.0)

        # 2️⃣ Calcula la línea base (referencia geométrica) desde el pivote al centroide del caserón
        self._ref_line = sgeom.LineString([self.pivot, self.stope.centroid])

        # 3️⃣ Define el ángulo de referencia (orientación natural del abanico)
        (x1, y1), (x2, y2) = list(self._ref_line.coords)
        dx, dy = x2 - x1, y2 - y1
        self._ref_angle = np.degrees(np.arctan2(dy, dx))

        # 4️⃣ Genera un rayo base (1e4 m de largo) en esa dirección
        self._base_ray = sgeom.LineString([
            self.pivot,
            (
                self.pivot.x + np.cos(np.radians(self._ref_angle)) * 1e4,
                self.pivot.y + np.sin(np.radians(self._ref_angle)) * 1e4
            ),
        ])

    # ---------- auxiliares internos ----------

    def _find_endpoints(self, ray: sgeom.LineString, max_length: float) -> Tuple[Optional[sgeom.Point], Optional[sgeom.Point]]:
        """Encuentra el collar (intersección con galería) y el fondo (intersección con caserón)."""
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

    def _is_valid_hole(self, collar, toe, min_length, stope) -> bool:
        """Valida que el tiro tenga longitud mínima y cruce efectivamente el caserón."""
        if not (collar and toe):
            return False
        hole = sgeom.LineString([collar, toe])
        if hole.length < min_length:
            return False
        return hole.intersects(stope)

    def _safe_parallel_offset(self, line, distance, side):
        """Offset paralelo robusto (maneja geometrías complejas de Shapely)."""
        try:
            g = line.parallel_offset(distance=distance, side=side, join_style=2)
        except Exception:
            return None
        if g.is_empty:
            return None
        geoms = getattr(g, "geoms", [g])
        best = min(geoms, key=lambda seg: seg.distance(self.pivot))
        return best if isinstance(best, sgeom.LineString) else None

    def _nearest_on(self, geometry, ref: sgeom.Point) -> Optional[sgeom.Point]:
        """Devuelve el punto más cercano a 'ref' dentro de la geometría dada."""
        if geometry is None or geometry.is_empty:
            return None
        pts = []
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
        return min(pts, key=lambda p: p.distance(ref)) if pts else None

    # ---------- MÉTODOS DE DISEÑO (fieles a appRing) ----------

    def generate_angular(self, params: Dict) -> Dict:
        """Distribuye los tiros en separación angular constante."""
        n = max(int(params.get("holes_number", 0)), 0)
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        max_len = float(params.get("max_length", 0.0))
        min_len = float(params.get("min_length", 0.1))
        spacing = (amax - amin) / (n - 1) if n > 1 else 0.0

        line = saff.rotate(self._base_ray, angle=amin, origin=self.pivot)
        collars, toes = [], []
        for _ in range(n):
            col, toe = self._find_endpoints(line, max_len)
            if self._is_valid_hole(col, toe, min_len, self.stope):
                collars.append(list(col.coords)[0])
                toes.append(list(toe.coords)[0])
            line = saff.rotate(line, angle=spacing, origin=self.pivot)
        return {"geometry": [collars, toes], "params": dict(params)}

    def generate_direct(self, params: Dict) -> Dict:
        """Método directo: mantiene espaciamiento constante entre fondos consecutivos."""
        spacing = float(params.get("spacing", 0.0))
        amin, amax = params.get("min_angle", 0.0), params.get("max_angle", 0.0)
        max_len, min_len = params.get("max_length", 0.0), params.get("min_length", 0.1)
        collars, toes = [], []

        ref = self._base_ray
        line = saff.rotate(ref, angle=amin, origin=self.pivot)

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

            # elegir el punto que más avanza angularmente dentro del rango permitido
            best, best_delta = None, -1e9
            for p in ints.geoms:
                nxt = sgeom.LineString([self.pivot, p])
                d = _angle_between(line, nxt)
                abs_ang = _angle_between(ref, nxt)
                if amin <= abs_ang <= amax and d > best_delta:
                    best, best_delta = p, d

            if best is None:
                break

            # corte si no avanza angularmente o ya salió del caserón
            if best.distance(toe) < 1e-6 or not sgeom.LineString([self.pivot, best]).intersects(self.stope):
                break

            # corte adicional: si el ángulo excede el máximo definido
            abs_ang = _angle_between(ref, sgeom.LineString([self.pivot, best]))
            if abs_ang > amax or abs_ang < amin:
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
        """Método offset: usa tangencia circular (offset perpendicular)."""
        spacing = float(params.get("spacing", 0.0))
        amin, amax = params.get("min_angle", 0.0), params.get("max_angle", 0.0)
        side_left = amax > amin
        max_len, min_len = params.get("max_length", 0.0), params.get("min_length", 0.1)
        collars, toes = [], []
        ref = self._base_ray
        line = saff.rotate(ref, angle=amin, origin=self.pivot)
        for _ in range(400):
            col, toe = self._find_endpoints(line, max_len)
            if not self._is_valid_hole(col, toe, min_len, self.stope):
                break
            collars.append(list(col.coords)[0])
            toes.append(list(toe.coords)[0])
            _, full_toe = self._find_endpoints(line, 1e6)
            if full_toe is None:
                break
            tang = _get_tangents(full_toe, spacing, self.pivot)
            if tang.is_empty or not hasattr(tang, "geoms"):
                break
            desired_side = "left" if side_left else "right"
            pts = [p for p in tang.geoms if _point_side(line, p) == desired_side]
            if not pts or (toes and pts[0].distance(sgeom.Point(toes[-1])) < 1e-6):
                break
            line = sgeom.LineString([self.pivot, pts[0]])
        return {"geometry": [collars, toes], "params": dict(params)}

    def generate_aeci(self, params: Dict) -> Dict:
        """
        AECI (Avance En Contorno Interno) — versión fiel a appRing.
        Genera tiros paralelos y progresivos siguiendo el contorno del caserón.

        Parámetros esperados (dict)
        ---------------------------
        spacing : float  -> separación entre tiros (m)
        min_angle, max_angle : float  -> rango angular (grados)
        max_length, min_length : float  -> longitudes límites por tiro (m)
        """

        spacing = float(params.get("spacing", 1.0))
        amin = float(params.get("min_angle", 0.0))
        amax = float(params.get("max_angle", 0.0))
        side = "left" if amax > amin else "right"
        max_len = float(params.get("max_length", 12.0))
        min_len = float(params.get("min_length", 0.3))

        collars, toes = [], []

        ref = sgeom.LineString([self.pivot, (self.pivot.x, self.pivot.y + 1e4)])
        line = saff.rotate(ref, angle=amin, origin=self.pivot)

        # Cap de espaciamiento para evitar casos degenerados
        min_dim = min(
            (self.stope.bounds[2] - self.stope.bounds[0]),
            (self.stope.bounds[3] - self.stope.bounds[1]),
        )
        spacing_cap = 0.9 * max(1e-6, min_dim)
        eff_spacing = min(spacing, spacing_cap) if spacing > 0 else 0.0

        for _ in range(400):
            if not line.intersects(self.stope):
                break

            collar, toe = self._find_endpoints(line, max_len)
            if not self._is_valid_hole(collar, toe, min_len, self.stope):
                break

            collars.append(list(collar.coords)[0])
            toes.append(list(toe.coords)[0])

            # --- Generar offsets paralelos ---
            off1 = self._safe_parallel_offset(line, 0.5 * eff_spacing, side)
            off2 = self._safe_parallel_offset(line, eff_spacing, side)
            if off1 is None or off2 is None:
                break

            ints = off1.intersection(self._stope_border)
            if ints.is_empty:
                break

            # elegir el punto más alejado del pivote
            pivot_int = _sort_points(ints, self.pivot)[-1]
            perp = saff.rotate(off1, angle=(-90 if side == "left" else 90), origin=pivot_int)

            nxt_geom = perp.intersection(off2)
            nxt_pt = nxt_geom if isinstance(nxt_geom, sgeom.Point) else self._nearest_on(nxt_geom, pivot_int)
            if nxt_pt is None:
                break

            cand = sgeom.LineString([self.pivot, nxt_pt])
            abs_ang = _angle_between(ref, cand)
            if not (amin <= abs_ang <= amax):
                break

            if toes and nxt_pt.distance(sgeom.Point(toes[-1])) < 1e-6:
                break

            line = cand

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
# Evaluador de carga (energía y volumen)
# =========================

class ChargeEvaluator:
    """
    Calcula la energía liberada y el volumen volado, siguiendo la lógica de RingCharge.

    Este módulo amplía la información de las cargas generadas:
    - masa total y por tiro (kg)
    - energía total (MJ)
    - energía específica (MJ/m³)
    - longitud promedio de carga
    - volumen estimado del bloque volado

    Parámetros esperados
    --------------------
    charges : dict
        {"geometry": [[collars...], [toes...]]}
    unit_costs : dict
        Debe incluir densidad_explosivo_gcc, diametro_carga_mm
    spacing : float
        Espaciamiento (m) actual evaluado.
    burden : float, opcional
        Carga o burden estimado (m). Si no se indica, se usa spacing.
    energia_unidad : float, opcional
        Energía del explosivo (MJ/kg). ANFO ≈ 4.2 MJ/kg.
    """

    def __init__(self) -> None:
        self.ENERGIA_ANFO_MJkg = 4.2  # constante típica de ANFO

    def evaluate_energy(
        self, charges: Dict, unit_costs: Dict,
        spacing: float, burden: Optional[float] = None,
        energia_unidad: Optional[float] = None
    ) -> Dict:
        """Evalúa propiedades energéticas y volumétricas del diseño."""

        rho = float(unit_costs.get("densidad_explosivo_gcc", 1.1))
        dmm = float(unit_costs.get("diametro_carga_mm", 64.0))
        ql = 7.854e-4 * rho * (dmm ** 2)  # kg/m

        energia_u = energia_unidad or self.ENERGIA_ANFO_MJkg
        geo = charges.get("geometry", [[], []])

        if not geo or not geo[0] or len(geo[0]) != len(geo[1]):
            return {
                "M_total": 0.0,
                "E_total": 0.0,
                "E_especifica": 0.0,
                "L_prom": 0.0,
                "V_volado": 0.0,
            }

        a = np.array(geo[0], dtype=float)
        b = np.array(geo[1], dtype=float)
        longitudes = np.linalg.norm(b - a, axis=1)
        L_prom = float(np.mean(longitudes))
        L_total = float(np.sum(longitudes))

        # masa total de explosivo (kg)
        M_total = L_total * ql

        # energía total liberada (MJ)
        E_total = M_total * energia_u

        # burden estimado (si no se da, se usa spacing)
        B = float(burden or spacing)
        V_volado = float(B * spacing * L_prom * len(longitudes))

        E_esp = (E_total / V_volado) if V_volado > 0 else 0.0

        return {
            "M_total": M_total,
            "E_total": E_total,
            "E_especifica": E_esp,
            "L_prom": L_prom,
            "V_volado": V_volado,
        }


# =========================
# Evaluación de costos
# =========================
# =========================
# Diseñador de secuencia de disparo (Timing)
# =========================

class TimingDesigner:
    """
    Asigna orden y retardos a los tiros, siguiendo la lógica simplificada de RingTiming.

    Objetivo
    --------
    - Numerar los tiros en orden de encendido.
    - Calcular el retardo de cada uno (ms) según su posición.
    - Calcular la carga máxima por retardo (Q_max) para evaluar PPV.

    Parámetros esperados
    --------------------
    charges : dict
        {"geometry": [[collars...], [toes...]]}
    charge_eval : dict
        Resultados energéticos del ChargeEvaluator (contiene M_total, L_prom, etc.)
    delay_step_ms : float, opcional
        Intervalo de retardo entre tiros consecutivos (ms). Por defecto 25 ms.
    delay_row_ms : float, opcional
        Retardo adicional entre filas (ms). Por defecto 50 ms.
    """

    def __init__(self) -> None:
        self.delay_step_ms = 25.0
        self.delay_row_ms = 50.0

    def assign_timing(
        self,
        charges: Dict,
        charge_eval: Dict,
        delay_step_ms: Optional[float] = None,
        delay_row_ms: Optional[float] = None
    ) -> Dict:
        """Asigna tiempos de encendido a cada tiro y calcula Qmax."""

        delays = []
        coords = []
        geo = charges.get("geometry", [[], []])
        if not geo or not geo[0]:
            return {"timing": [], "Q_max": 0.0}

        collars, toes = np.array(geo[0]), np.array(geo[1])
        n_tiros = len(collars)
        delay_step = delay_step_ms or self.delay_step_ms
        delay_row = delay_row_ms or self.delay_row_ms

        # Calcular masas individuales (asumir carga uniforme por tiro)
        M_total = float(charge_eval.get("M_total", 0.0))
        M_por_tiro = (M_total / n_tiros) if n_tiros > 0 else 0.0

        # Ordenar tiros por coordenadas (de izquierda a derecha, luego abajo hacia arriba)
        indices = np.lexsort((collars[:, 1], collars[:, 0]))

        delay_dicts = []
        fila_actual = 0
        fila_y = None
        for i, idx in enumerate(indices, start=1):
            x, y = collars[idx]
            # Determinar fila (si Y cambia > 1 m se asume nueva fila)
            if fila_y is None:
                fila_y = y
            elif abs(y - fila_y) > 1.0:
                fila_actual += 1
                fila_y = y
            delay_ms = fila_actual * delay_row + (i - 1) * delay_step

            delay_dicts.append({
                "id": i,
                "coords": (float(x), float(y)),
                "delay_ms": delay_ms,
                "charge_kg": M_por_tiro,
            })
            delays.append(delay_ms)
            coords.append((x, y))

        # Calcular carga máxima por retardo (Q_max)
        delay_groups = {}
        for d in delay_dicts:
            t = round(d["delay_ms"], 1)
            delay_groups.setdefault(t, 0.0)
            delay_groups[t] += d["charge_kg"]

        Q_max = max(delay_groups.values()) if delay_groups else 0.0

        return {"timing": delay_dicts, "Q_max": Q_max}

# =========================
# Evaluador global del ring
# =========================

class RingEvaluator:
    """
    Evalúa globalmente un diseño de tronadura (ring) integrando
    métricas geométricas, energéticas y económicas, siguiendo
    la filosofía de AppRing.

    Propósito
    ----------
    - Obtener energía total (MJ) y específica (MJ/m³).
    - Calcular volumen volado aproximado según espaciamiento (S),
      burden (B) y longitud efectiva de perforación (L).
    - Evaluar costo total y unitario ($, $/m³).
    - Estimar eficiencia energética (energía efectiva 85 %).
    - Dejar listos los parámetros para cálculo de fragmentación (P80).

    Parámetros de entrada
    ---------------------
    design : dict
        {"holes": {...}, "charges": {...}} generado por el modelo.
    unit_costs : dict
        {
          "densidad_explosivo_gcc": float,
          "diametro_carga_mm": float,
          "energia_explosivo_MJkg": float,
          "explosivo_por_kg": float,
          "perforacion_por_metro": float,
          "detonador_por_unidad": float
        }

    Retorna
    --------
    dict con métricas globales:
        {
          "volumen": m³,
          "masa_explosivo": kg,
          "energia_total": MJ,
          "energia_efectiva": MJ,
          "energia_especifica": MJ/m³,
          "energia_especifica_efectiva": MJ/m³,
          "costo_total": $,
          "costo_por_m3": $/m³,
          "energia_por_dolar": MJ/$,
          "eficiencia_energetica": %
        }
    """

    def evaluate_ring(self, design: dict, unit_costs: dict) -> dict:
        # --- Extraer geometrías ---
        holes = design.get("holes", {})
        charges = design.get("charges", {})

        # --- Longitudes perforadas y cargadas ---
        evaluator = DesignEvaluator()
        L_perf = evaluator.total_drilled_length(holes)  # m
        L_carga = evaluator.total_charge_length(charges)  # m

        # --- Parámetros del explosivo ---
        rho = float(unit_costs.get("densidad_explosivo_gcc", 1.1))  # g/cc
        D = float(unit_costs.get("diametro_carga_mm", 64.0))  # mm
        E_u = float(unit_costs.get("energia_explosivo_MJkg", 4.2))  # MJ/kg
        Ce = float(unit_costs.get("explosivo_por_kg", 2.2))  # $/kg

        # --- Cálculos de carga ---
        q_l = 7.854e-4 * rho * (D ** 2)       # kg/m (carga lineal)
        M_total = q_l * L_carga               # masa total de explosivo (kg)
        E_total = M_total * E_u               # energía total (MJ)

        # --- Geometría global del bloque ---
        params = holes.get("params", {})
        S = float(params.get("spacing", 2.0))
        B = float(params.get("burden", S))    # si no se define burden, se asume igual a S
        n_tiros = len(holes.get("geometry", [[], []])[0])
        L_prom = L_perf / max(n_tiros, 1)     # longitud promedio de tiro

        # Volumen aproximado de roca volada
        V = S * B * L_prom * max(n_tiros, 1) * 0.8  # factor 0.8 ≈ eficiencia de llenado

        # --- Costos ---
        C_total = evaluator.calculate_total_cost(design, unit_costs)
        C_m3 = C_total / V if V > 0 else 0.0

        # --- Energía específica y eficiencia ---
        Eesp = E_total / V if V > 0 else 0.0
        eficiencia = 0.85
        E_efectiva = E_total * eficiencia
        Eesp_ef = E_efectiva / V if V > 0 else 0.0

        # --- Relaciones energéticas ---
        EporUSD = E_total / C_total if C_total > 0 else 0.0

        return {
            "volumen": V,
            "masa_explosivo": M_total,
            "energia_total": E_total,
            "energia_efectiva": E_efectiva,
            "energia_especifica": Eesp,
            "energia_especifica_efectiva": Eesp_ef,
            "costo_total": C_total,
            "costo_por_m3": C_m3,
            "energia_por_dolar": EporUSD,
            "eficiencia_energetica": eficiencia * 100.0,
        }

# =========================
# Fragmentación (modelo Kuz-Ram)
# =========================

class RingFragmentation:
    """
    Estima la fragmentación (P80, P50, P20) en función de la energía específica
    y las propiedades de la roca, siguiendo el modelo empírico de Kuz-Ram
    usado en AppRing y calibrado para MJ/m³.
    """

    def __init__(self) -> None:
        # Valores típicos base (pueden ajustarse según litología)
        self.defaults = {
            "A": 5.0,     # factor de fragmentación base (roca media)
            "b": 0.8,     # exponente empírico de energía
            "E_ref": 0.4, # MJ/m³, energía de referencia para roca media
            "k": 1.0,     # factor de escala (ajuste dimensional)
        }

    def evaluate_fragmentation(
        self,
        ring_metrics: Dict,
        rock_params: Optional[Dict] = None
    ) -> Dict:
        """Evalúa P80, P50, P20 según el modelo Kuz-Ram estabilizado."""

        if not ring_metrics:
            return {"P80": 0.0, "P50": 0.0, "P20": 0.0, "relacion_energia": 0.0}

        # Parámetros de roca
        params = self.defaults.copy()
        if rock_params:
            params.update(rock_params)

        E_esp = max(float(ring_metrics.get("energia_especifica_efectiva", 0.0)), 1e-3)
        E_ref = max(float(params.get("E_ref", 0.4)), 1e-3)
        A = float(params.get("A", 5.0))
        b = float(params.get("b", 0.8))
        k = float(params.get("k", 1.0))

        # Relación energía / referencia
        ratio = E_esp / E_ref

        # Modelo empírico (Kuz-Ram)
        # Nota: usamos 1000 para pasar de metros a milímetros si A está calibrado en metros.
        P80 = A * k * (E_ref / E_esp) ** b * 1000.0  # mm
        P80 = float(np.clip(P80, 10.0, 400.0))        # limitar a 10–400 mm

        P50 = P80 * 0.67
        P20 = P80 * 0.33

        return {
            "P80": P80,
            "P50": P50,
            "P20": P20,
            "relacion_energia": ratio,
        }

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
    Recorre el rango de espaciamiento S (o número de tiros N en el caso 'angular'),
    evalúa el costo y conserva todas las alternativas válidas.

    Devuelve el mejor diseño por costo y la lista completa de opciones dentro del presupuesto.
    """

    def __init__(self, 
                 generator: DrillFanGenerator, 
                 charge_designer: ChargeDesigner,
                 evaluator: DesignEvaluator,  
                 ring_evaluator: RingEvaluator
                 ) -> None:
                self.generator = generator
                self.charge_designer = charge_designer
                self.evaluator = evaluator
                self.ring_evaluator = ring_evaluator

    def run(self, cfg: Dict, log: Callable[[str], None]) -> Optional[Dict]:
        """
        Ejecuta la optimización iterando sobre S o N según el método.

        Parámetros
        ----------
        cfg : dict
            Debe incluir:
              - design_method: {'angular'|'directo'|'offset'|'aeci'}
              - s_min, s_max: float (o int para 'angular')
              - presupuesto_maximo: float
              - min_angle, max_angle, min_length, max_length
              - stemming (para cargas)
              - unit_costs: dict (ver DesignEvaluator)
        log : callable
            Función callback para registrar mensajes en la interfaz.

        Returns
        -------
        dict | None
            Si hay válidos:
              {
                "best":   {"S", "method", "design", "cost", "num_holes"},
                "trials": [ ... mismas claves por cada alternativa válida ... ]
              }
            Si no hay válidos, retorna None.
        """
        method = (cfg.get("design_method") or "angular").lower()
        smin = float(cfg.get("s_min", 1.0))
        smax = float(cfg.get("s_max", 5.0))
        budget = float(cfg.get("presupuesto_maximo", 0.0))
        unit_costs = dict(cfg.get("unit_costs", {}))

        # Determinar tipo de variable: discreta (N) o continua (S)
        if method == "angular":
            S_values = range(int(smin), int(smax) + 1)
            unit_label = "tiros"
        else:
            # Paso de 0.5 m para espaciamientos continuos
            S_values = np.arange(smin, smax + 0.001, 0.5)
            unit_label = "m (S)"

        log(f"▶ Método: {method} | S={smin}–{smax} {unit_label} | Presupuesto=${budget:,.2f}")

        trials: List[Dict] = []
        for S in S_values:
            try:
                log(f"\n— Probando S={S:.2f} …")
                base = {
                    "min_angle": float(cfg.get("min_angle", -45.0)),
                    "max_angle": float(cfg.get("max_angle", 45.0)),
                    "max_length": float(cfg.get("max_length", 30.0)),
                    "min_length": float(cfg.get("min_length", 0.3)),
                }

                # Generar tiros
                if method == "angular":
                    holes = self.generator.generate_angular({**base, "holes_number": int(S)})
                elif method == "directo":
                    holes = self.generator.generate_direct({**base, "spacing": float(S)})
                elif method == "offset":
                    holes = self.generator.generate_offset({**base, "spacing": float(S)})
                elif method == "aeci":
                    holes = self.generator.generate_aeci({**base, "spacing": float(S)})
                else:
                    holes = self.generator.generate_angular({**base, "holes_number": int(S)})

                if not holes["geometry"][0]:
                    log("   · Geometría vacía o sin intersección con caserón.")
                    continue

                # Cargas
                charges = self.charge_designer.get_charges(
                    holes, {"stemming": float(cfg.get("stemming", 0.0))}
                )
                design = {"holes": holes, "charges": charges}

                # Evaluaciones (todas dentro de try)
                try:
                    charge_eval = ChargeEvaluator()
                    energy_data = charge_eval.evaluate_energy(charges, unit_costs, spacing=float(S))
                    design["energy_data"] = energy_data
                    timing_designer = TimingDesigner()
                    timing_data = timing_designer.assign_timing(charges, energy_data)
                    design["timing_data"] = timing_data

                    ring_metrics = self.ring_evaluator.evaluate_ring(design, unit_costs)

                    # 👇 Agregamos aquí el cálculo de fragmentación, dentro del mismo try
                    frag_model = RingFragmentation()
                    rock_params = cfg.get("rock_params", {})
                    frag_data = frag_model.evaluate_fragmentation(ring_metrics, rock_params)
                    design["frag_data"] = frag_data
                    ring_metrics.update(frag_data)

                except Exception as e_inner:
                    log(f"   ⚠️ Error interno al evaluar cargas/timing/fragmentación: {e_inner}")
                    continue

                cost = ring_metrics.get("costo_total", 0.0)
                n_tiros = len(holes["geometry"][0])

                log(f"   · Tiros generados: {n_tiros} | Costo total: ${cost:,.2f}")

                if cost <= budget and n_tiros > 0:
                    trials.append({
                        "S": float(S),
                        "method": method,
                        "design": design,
                        "metrics": ring_metrics,
                        "cost": cost,
                        "num_holes": int(n_tiros),
                        "P80": frag_data.get("P80", 0.0),
                    })
                    log("   · ✅ Dentro del presupuesto.")
                else:
                    log("   · ❌ Excede presupuesto o diseño vacío.")

            except Exception as e:
                log(f"❌ Error general en iteración S={S:.2f}: {e}")
                continue


        if not trials:
            log("\n✖ No se encontró diseño válido.")
            return None

        best = min(trials, key=lambda d: d["cost"])
        log(f"\n🏁 Mejor costo = ${best['cost']:,.2f} | Método = {method} | S = {best['S']:.2f}")

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

        # Componentes del modelo
        self.generator = DrillFanGenerator(stope_geom, drift_geom, pivot_geom)
        self.charge_designer = ChargeDesigner()
        self.evaluator = DesignEvaluator()
        self.ring_evaluator = RingEvaluator()  
        self.optimizer = Optimizer(
            self.generator,
            self.charge_designer,
            self.evaluator,
            self.ring_evaluator,
        )
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
        self.optimizer = Optimizer(
            self.generator, 
            self.charge_designer, 
            self.evaluator,
            self.ring_evaluator,
        )
