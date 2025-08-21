"""
Modelo de EnergyAnalysis (patrón MVC).

Responsabilidad:
- Mantener los parámetros del análisis (mismos nombres que la app original).
- Obtener geometrías/propiedades desde un proveedor de datos (DataProvider).
- Construir la grilla (linspace + meshgrid) y calcular el campo 2D/3D.
  * Hoy: campo placeholder simple para probar el flujo.
  * Futuro: reemplazar solo la línea del placeholder por 'kleine(...)'.

Salidas esperadas:
- compute_energy_grid()       -> dict con x, y, values, xlabel, ylabel, title
- compute_energy_isosurface() -> dict con xx, yy, zz, energy, cutoff
"""

import numpy as np


# --------------------- Estructuras de datos simples ---------------------------

class PatternContext:
    """Contexto mínimo de un patrón (nombres asociados en el proyecto)."""
    def __init__(self, pattern):
        self.pattern = pattern
        self.holes_name = None
        self.drift_name = None
        self.stope_name = None


class GeometryData:
    """Geometrías mínimas necesarias para el análisis."""
    def __init__(self):
        self.stope_polygon = None          # por ejemplo: lista de (x, y)
        self.drift_polygon = None
        self.charges_segments = []         # lista de ((x,y,z), (x,y,z))


class RockProps:
    """Propiedades de roca."""
    def __init__(self, density=None):
        self.density = density  # kg/m3


class ExplosiveProps:
    """Propiedades del explosivo."""
    def __init__(self, density=None, vod=None, rws=None):
        self.density = density
        self.VOD = vod
        self.RWS = rws


# --------------------- Proveedor de datos (stub) ------------------------------

class DataProvider:
    """
    Capa de acceso a datos.

    - Si existe 'parent_app', lee desde parent_app.designs (charges/stopes/drifts).
    - Si no existe, retorna valores de prueba (dummies) para permitir ejecutar.
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

        ge.stope_polygon    = s.get("geometry")
        ge.drift_polygon    = d.get("geometry")
        ge.charges_segments = ch.get("lines") or []

        # Rellenos de seguridad para pruebas
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
        density = rock.get("density", 2700.0)  # valor por defecto
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


# --------------------- Parámetros y Modelo ------------------------------------

class EnergyParams:
    """
    Contenedor de parámetros de EnergyAnalysis.
    (Se preservan los nombres originales.)
    """
    def __init__(self):
        self.pattern = ""
        self.section = "Transversal"   # Transversal | Longitudinal | Planta
        self.type    = "Volumen"       # Volumen | Tonelaje
        self.xmin = 0.0; self.xmax = 10.0
        self.ymin = 0.0; self.ymax = 10.0
        self.zmin = 0.0; self.zmax = 10.0
        self.cutoff = 1.0
        self.resol  = 50
        self.levels = 10
        self.diameter = 0.0
        self.density  = 0.0
        self.K_const  = 200.0
        self.a_const  = 0.9


class Model:
    """
    Modelo numérico de EnergyAnalysis.

    Funciones principales:
    - set_from_view_strings(data): convierte strings de la vista a números.
    - validate(): valida reglas mínimas.
    - compute_energy_grid(): calcula un campo 2D en la sección seleccionada.
    - compute_energy_isosurface(): calcula un campo 3D en el volumen.

    Nota: el cálculo actual usa un placeholder (plano) para probar el flujo.
          Para igualar la app original, reemplazar el placeholder por 'kleine'.
    """
    def __init__(self, parent_app=None):
        self.params   = EnergyParams()
        self.provider = DataProvider(parent_app)

    def bind_parent(self, parent_app):
        """Permite reconectar el modelo a un 'parent_app' real (appRing)."""
        self.provider = DataProvider(parent_app)

    # Conversión segura desde strings (vista) a tipos numéricos
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
        Actualiza 'self.params' con datos en formato string recibidos de la vista.
        Claves esperadas: pattern, section, type, xmin..zmax, cutoff, resol,
                          levels, diameter, density, K_const, a_const.
        """
        p = self.params
        p.pattern = data.get("pattern", p.pattern)
        p.section = data.get("section", p.section)
        p.type    = data.get("type",    p.type)

        p.xmin = self._f(data.get("xmin", p.xmin), p.xmin)
        p.xmax = self._f(data.get("xmax", p.xmax), p.xmax)
        p.ymin = self._f(data.get("ymin", p.ymin), p.ymin)
        p.ymax = self._f(data.get("ymax", p.ymax), p.ymax)
        p.zmin = self._f(data.get("zmin", p.zmin), p.zmin)
        p.zmax = self._f(data.get("zmax", p.zmax), p.zmax)

        p.cutoff  = self._f(data.get("cutoff",  p.cutoff),  p.cutoff)
        p.resol   = self._i(data.get("resol",   p.resol),   p.resol)
        p.levels  = self._i(data.get("levels",  p.levels),  p.levels)

        p.diameter= self._f(data.get("diameter",p.diameter),p.diameter)
        p.density = self._f(data.get("density", p.density), p.density)
        p.K_const = self._f(data.get("K_const", p.K_const), p.K_const)
        p.a_const = self._f(data.get("a_const", p.a_const), p.a_const)

    def validate(self):
        """
        Reglas mínimas de validación.
        - 'resol' y 'levels' deben ser positivos.
        - 'section' ∈ {Transversal, Longitudinal, Planta}.
        Devuelve (ok: bool, msg: str).
        """
        p = self.params
        if p.resol <= 0 or p.levels <= 0:
            return False, "Resolución y niveles deben ser positivos."
        if p.section not in ("Transversal", "Longitudinal", "Planta"):
            return False, "Sección no válida."
        return True, ""

    # --------------------- Cálculos (placeholder) -----------------------------

    def compute_energy_grid(self):
        """
        Cálculo 2D en la sección seleccionada.

        Procedimiento:
        - Construye la malla (X, Y) según 'section' (tercer eje fijo).
        - Calcula un campo placeholder simple (Z = X + Y).
        - Si 'type' == 'Tonelaje', escala por densidad de roca.

        Futuro:
        - Reemplazar 'Z = X + Y' por 'kleine(...)' aplanando y rearmando la malla.

        Retorna: dict con x, y, values, xlabel, ylabel, title.
        """
        p = self.params

        # Puntos de conexión a datos reales (listos para appRing)
        ctx   = self.provider.get_pattern_context(p.pattern)
        geoms = self.provider.get_geometries(ctx)
        rock  = self.provider.get_rock_props(ctx)
        _exp  = self.provider.get_explosive_props(ctx)

        nx = ny = int(p.resol)

        if p.section == "Transversal":
            x = np.linspace(p.xmin, p.xmax, nx)
            y = np.linspace(p.ymin, p.ymax, ny)
            X, Y = np.meshgrid(x, y)
            Z = X + Y  # <-- placeholder (reemplazar por 'kleine' cuando corresponda)
            xlabel, ylabel = "x [m]", "y [m]"
            title = f"Energía — z={p.zmin} m"

        elif p.section == "Longitudinal":
            z = np.linspace(p.zmin, p.zmax, nx)
            y = np.linspace(p.ymin, p.ymax, ny)
            X, Y = np.meshgrid(z, y)  # aquí X representa z
            Z = X + Y
            xlabel, ylabel = "z [m]", "y [m]"
            title = f"Energía — x={p.xmin} m"

        else:  # Planta
            x = np.linspace(p.xmin, p.xmax, nx)
            z = np.linspace(p.zmin, p.zmax, ny)
            X, Y = np.meshgrid(x, z)  # aquí Y representa z
            Z = X + Y
            xlabel, ylabel = "x [m]", "z [m]"
            title = f"Energía — y={p.ymin} m"

        if p.type == "Tonelaje":
            Z = Z * (rock.density / 1000.0)

        return dict(x=X, y=Y, values=Z, xlabel=xlabel, ylabel=ylabel, title=title)

    def compute_energy_isosurface(self):
        """
        Cálculo 3D en el volumen definido.

        Procedimiento:
        - Construye la malla (X, Y, Z) completa.
        - Calcula un campo placeholder simple (E = X + Y + Z).
        - Si 'type' == 'Tonelaje', escala por densidad de roca.

        Futuro:
        - Reemplazar 'E = X + Y + Z' por 'kleine(...)' con X/Y/Z aplanados.

        Retorna: dict con xx, yy, zz (ravel), energy (ravel), cutoff.
        """
        p = self.params

        n  = max(10, int(p.resol)//3)
        xx = np.linspace(p.xmin, p.xmax, n)
        yy = np.linspace(p.ymin, p.ymax, n)
        zz = np.linspace(p.zmin, p.zmax, n)
        X, Y, Z = np.meshgrid(xx, yy, zz, indexing="ij")

        E = X + Y + Z  # <-- placeholder

        rock = self.provider.get_rock_props(self.provider.get_pattern_context(p.pattern))
        if p.type == "Tonelaje":
            E = E * (rock.density / 1000.0)

        return dict(xx=X.ravel(), yy=Y.ravel(), zz=Z.ravel(),
                    energy=E.ravel(), cutoff=p.cutoff)
