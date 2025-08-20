"""
Model energy_analysis
- Mantiene parámetros.
- Recupera geometrías/propiedades (stubs).
- Calcula campos 2D/3D (placeholders, listos para reemplazar por Kleine).
"""

import numpy as np
import time


# -------------------- Estructuras simples --------------------

class PatternContext:
    """Contexto de un patrón: nombres relacionados en el proyecto."""
    def __init__(self, pattern):
        self.pattern = pattern
        self.holes_name = None
        self.drift_name = None
        self.stope_name = None


class GeometryData:
    """Geometrías mínimas para el análisis."""
    def __init__(self):
        self.stope_polygon = None         # p.ej. lista de (x,y)
        self.drift_polygon = None
        self.charges_segments = []        # [((x,y,z),(x,y,z)), ...]


class RockProps:
    """Propiedades de roca."""
    def __init__(self, density=None):
        self.density = density  # kg/m3


class ExplosiveProps:
    """Propiedades del explosivo."""
    def __init__(self, density=None, vod=None, rws=None):
        self.density = density  # (unidades según tu app)
        self.VOD = vod
        self.RWS = rws


# -------------------- Proveedor de datos (stubs) --------------------

class DataProvider:
    """
    Interfaz con el programa principal (appRing).
    Si no hay datos reales, entrega valores de prueba.
    """
    def __init__(self, parent_app=None):
        self.parent = parent_app

    def get_pattern_context(self, pattern):
        ctx = PatternContext(pattern)
        designs = getattr(self.parent, "designs", {}) if self.parent else {}
        c = designs.get("charges", {}).get(pattern)
        if c:
            ctx.holes_name = c.get("holes")
            ctx.drift_name = c.get("drift")
            ctx.stope_name = c.get("stope")
        return ctx

    def get_geometries(self, ctx):
        ge = GeometryData()
        designs = getattr(self.parent, "designs", {}) if self.parent else {}

        s = designs.get("stopes", {}).get(ctx.stope_name, {}) if ctx.stope_name else {}
        d = designs.get("drifts", {}).get(ctx.drift_name, {}) if ctx.drift_name else {}
        ch = designs.get("charges", {}).get(ctx.pattern, {}) if ctx.pattern else {}

        ge.stope_polygon = s.get("geometry")
        ge.drift_polygon = d.get("geometry")
        ge.charges_segments = ch.get("lines") or []

        # Dummies seguros
        if ge.stope_polygon is None:
            ge.stope_polygon = [(0, 0), (10, 0), (10, 4), (0, 4)]
        if not ge.charges_segments:
            ge.charges_segments = [((2, 0, 2), (2, 4, 2)),
                                   ((5, 0, 2), (5, 4, 2)),
                                   ((8, 0, 2), (8, 4, 2))]
        return ge

    def get_rock_props(self, ctx):
        designs = getattr(self.parent, "designs", {}) if self.parent else {}
        s = designs.get("stopes", {}).get(ctx.stope_name, {}) if ctx.stope_name else {}
        rock = s.get("rock", {})
        density = rock.get("density", 2700.0)  # default seguro
        return RockProps(density=density)

    def get_explosive_props(self, ctx):
        designs = getattr(self.parent, "designs", {}) if self.parent else {}
        ch = designs.get("charges", {}).get(ctx.pattern, {}) if ctx.pattern else {}
        exp = ch.get("explosive", {})
        return ExplosiveProps(
            density=exp.get("density", 0.85),
            vod=exp.get("VOD", 4500.0),
            rws=exp.get("RWS", 100.0)
        )


# -------------------- Parámetros y Modelo --------------------

class EnergyParams:
    """
    Parámetros de EnergyAnalysis (mismos nombres que la vista/app original).
    """
    def __init__(self):
        self.pattern = ""
        self.section = "Transversal"   # Transversal | Longitudinal | Planta
        self.type = "Volumen"          # Volumen | Tonelaje
        self.xmin = 0.0; self.xmax = 10.0
        self.ymin = 0.0; self.ymax = 10.0
        self.zmin = 0.0; self.zmax = 10.0
        self.cutoff = 1.0
        self.resol = 50
        self.levels = 10
        self.diameter = 0.0
        self.density = 0.0
        self.K_const = 200.0
        self.a_const = 0.9


class Model:
    """
    Modelo de energía:
    - Guarda parámetros (EnergyParams).
    - Recupera contexto/geom/propiedades vía DataProvider.
    - Calcula mallas 2D y 3D (placeholders).
    """
    def __init__(self, parent_app=None):
        self.params = EnergyParams()
        self.provider = DataProvider(parent_app)

    def bind_parent(self, parent_app):
        """Conecta el modelo al app real (appRing)."""
        self.provider = DataProvider(parent_app)

    # ---- utilidades de parseo (sin abusar de try) ----
    def _f(self, s, default=0.0):
        try:
            return float(s)
        except Exception:
            return default

    def _i(self, s, default=0):
        try:
            return int(float(s))
        except Exception:
            return default

    def set_from_view_strings(self, data):
        """
        Recibe strings de la vista y actualiza parámetros.
        Claves esperadas: pattern, section, type, xmin..zmax, cutoff, resol, levels, diameter, density, K_const, a_const.
        """
        p = self.params
        p.pattern = data.get("pattern", p.pattern)
        p.section = data.get("section", p.section)
        p.type    = data.get("type", p.type)

        p.xmin = self._f(data.get("xmin", p.xmin), p.xmin)
        p.xmax = self._f(data.get("xmax", p.xmax), p.xmax)
        p.ymin = self._f(data.get("ymin", p.ymin), p.ymin)
        p.ymax = self._f(data.get("ymax", p.ymax), p.ymax)
        p.zmin = self._f(data.get("zmin", p.zmin), p.zmin)
        p.zmax = self._f(data.get("zmax", p.zmax), p.zmax)

        p.cutoff  = self._f(data.get("cutoff", p.cutoff), p.cutoff)
        p.resol   = self._i(data.get("resol", p.resol), p.resol)
        p.levels  = self._i(data.get("levels", p.levels), p.levels)

        p.diameter= self._f(data.get("diameter", p.diameter), p.diameter)
        p.density = self._f(data.get("density", p.density), p.density)
        p.K_const = self._f(data.get("K_const", p.K_const), p.K_const)
        p.a_const = self._f(data.get("a_const", p.a_const), p.a_const)

    def validate(self):
        """Devuelve (ok, msg)."""
        p = self.params
        if p.resol <= 0 or p.levels <= 0:
            return False, "Resolución y niveles deben ser positivos."
        if p.section not in ("Transversal", "Longitudinal", "Planta"):
            return False, "Sección no válida."
        return True, ""

    # -------------------- Cálculos (placeholders vectorizados) --------------------

    def compute_energy_grid(self):
        """
        Devuelve dict con:
            x, y, values, xlabel, ylabel, title, elapsed
        Para reemplazar por el modelo real (Kleine). Aquí todo es vectorizado, sin bucles.
        """
        p = self.params
        t0 = time.time()

        # Hooks de datos (dejan claro dónde conectar appRing)
        ctx = self.provider.get_pattern_context(p.pattern)
        geoms = self.provider.get_geometries(ctx)
        rock  = self.provider.get_rock_props(ctx)
        _exp  = self.provider.get_explosive_props(ctx)

        nx = ny = int(p.resol)

        if p.section == "Transversal":
            x = np.linspace(p.xmin, p.xmax, nx)
            y = np.linspace(p.ymin, p.ymax, ny)
            X, Y = np.meshgrid(x, y)
            Z = np.exp(-((X - (p.xmin+p.xmax)/2)**2 + (Y - (p.ymin+p.ymax)/2)**2) / 10.0)
            xlabel, ylabel = "x [m]", "y [m]"
            title = f"Energía — z={p.zmin} m"

        elif p.section == "Longitudinal":
            x = np.linspace(p.zmin, p.zmax, nx)
            y = np.linspace(p.ymin, p.ymax, ny)
            X, Y = np.meshgrid(x, y)
            Z = np.sin(0.5*X) * np.cos(0.5*Y)
            xlabel, ylabel = "z [m]", "y [m]"
            title = f"Energía — x={p.xmin} m"

        else:  # Planta
            x = np.linspace(p.xmin, p.xmax, nx)
            y = np.linspace(p.zmin, p.zmax, ny)
            X, Y = np.meshgrid(x, y)
            Z = np.sin(0.5*X) * np.sin(0.5*Y)
            xlabel, ylabel = "x [m]", "z [m]"
            title = f"Energía — y={p.ymin} m"

        if p.type == "Tonelaje":
            Z = Z * (rock.density / 1000.0)  # ejemplo simple

        return {
            "x": X, "y": Y, "values": Z,
            "xlabel": xlabel, "ylabel": ylabel, "title": title,
            "elapsed": time.time() - t0
        }

    def compute_energy_isosurface(self):
        """
        Devuelve dict con:
            xx, yy, zz, energy, cutoff, elapsed
        Placeholder 3D (vectorizado). Reemplazar por cálculo real.
        """
        p = self.params
        t0 = time.time()

        n = max(10, int(p.resol)//3)
        xx = np.linspace(p.xmin, p.xmax, n)
        yy = np.linspace(p.ymin, p.ymax, n)
        zz = np.linspace(p.zmin, p.zmax, n)
        X, Y, Z = np.meshgrid(xx, yy, zz, indexing="ij")
        E = np.exp(-((X-(p.xmin+p.xmax)/2)**2 + (Y-(p.ymin+p.ymax)/2)**2 + (Z-(p.zmin+p.zmax)/2)**2) / 10.0)

        return {
            "xx": X.ravel(), "yy": Y.ravel(), "zz": Z.ravel(),
            "energy": E.ravel(), "cutoff": p.cutoff,
            "elapsed": time.time() - t0
        }
