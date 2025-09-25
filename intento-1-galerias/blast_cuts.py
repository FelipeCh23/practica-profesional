# blast_cuts.py
# Generadores geométricos de CUELEs para frentes de galería (2D).
# Salida: lista de "holes" con posición (x,y) relativa al centro del frente,
# familia="cuele" y número de retardo (delay) según el esquema del plano.

from math import cos, radians, sin


def _pt(x, y, delay, note=""):
    return {"x": x, "y": y, "family": "cuele", "delay": delay, "note": note}


# CUELE SARRIOS (3x3)


def cuele_sarrois(center=(0.0, 0.0), d_core=0.15, vacio_central=True):
    """
    Sarrois clásico: 9 posiciones en retícula 3x3 con paso d_core,
    paralelos al frente. El central suele ir SIN carga (alivio).
    Retardos en 3 series (2 -> 1 -> 0) del exterior al interior.
    d_core típico (pág. 42): 0.20 flojo, 0.15 medio, 0.10 duro (m).
    """
    cx, cy = center
    # Malla 3x3 centrada en (cx, cy)
    offs = [-d_core, 0.0, d_core]
    holes = []
    for j, oy in enumerate(offs):
        for i, ox in enumerate(offs):
            # Centro (0,0) reservado para vacío si corresponde
            if (ox == 0.0 and oy == 0.0) and vacio_central:
                holes.append(_pt(cx + ox, cy + oy, delay=99, note="alivio (vacío)"))
            else:
                # Serie de retardos: anillo exterior=2, cruz intermedia=1, centro=0
                ring = 0
                if abs(ox) == d_core and abs(oy) == d_core:
                    ring = 2  # esquinas (exterior)
                elif (abs(ox) == d_core and oy == 0.0) or (
                    abs(oy) == d_core and ox == 0.0
                ):
                    ring = 1  # lados (intermedio)
                else:
                    ring = 0  # interior inmediato
                holes.append(_pt(cx + ox, cy + oy, delay=ring, note="sarrios"))
    return holes


# CUELE SUECO


def cuele_sueco(center=(0.0, 0.0), d_core=0.15, roca_dura=False):
    """
    Variante sueca: para roca media/blanda (menos taladros) o dura (más compacta).
    Implementación simple: rombo 2x2 alrededor del centro + opcional puntos extra.
    Retardos en 3 series: 2 (exterior), 1 (intermedio), 0 (interior).
    """
    cx, cy = center
    holes = []
    a = d_core
    # Rombo básico alrededor del centro
    base = [(0, a), (a, 0), (0, -a), (-a, 0)]
    for ox, oy in base:
        holes.append(_pt(cx + ox, cy + oy, delay=1, note="sueco"))
    # Centro (puede ir vacío o cargado suave)
    holes.append(_pt(cx, cy, delay=0, note="sueco centro (posible alivio)"))
    if roca_dura:
        # Añade esquinas para compactar (anillo exterior)
        for ox, oy in [(-a, a), (a, a), (a, -a), (-a, -a)]:
            holes.append(_pt(cx + ox, cy + oy, delay=2, note="sueco refuerzo"))
    return holes


# CUELE COROMANT (alivio en '8')


def cuele_coromant(center=(0.0, 0.0), d_core=0.18):
    """
    Coromant: par central 'en ocho' (sin carga) como gran alivio + 6 tiros alrededor.
    Retardos: 2 (anillo exterior), 1 (cercanos al alivio), 99 para los alivios vacíos.
    """
    cx, cy = center
    holes = []
    # Dos tiros centrales comunicados (forma de 8) -> sin carga (alivio)
    holes.append(_pt(cx - 0.5 * d_core, cy, delay=99, note="alivio '8' (vacío)"))
    holes.append(_pt(cx + 0.5 * d_core, cy, delay=99, note="alivio '8' (vacío)"))
    # Corona de 6: cruz + 2 esquinas
    ring1 = [(0, d_core), (d_core, 0), (0, -d_core), (-d_core, 0)]
    for ox, oy in ring1:
        holes.append(_pt(cx + ox, cy + oy, delay=1, note="coromant corte"))
    ring2 = [(d_core, d_core), (-d_core, -d_core)]
    for ox, oy in ring2:
        holes.append(_pt(cx + ox, cy + oy, delay=2, note="coromant corte"))
    return holes


# CUELE CUÑA (V-cut)


def cuele_cuna(center=(0.0, 0.0), d_core=0.20, n_pairs=3, ang_deg=70):
    """
    Cuña: dos filas convergentes que forman una 'V' con vértice en el centro.
    - n_pairs: pares por lado (3 típico).
    - ang_deg: ángulo respecto del piso (≈ 68–70° en los croquis).
    Retardos del vértice hacia afuera: 0,1,2,...
    """
    cx, cy = center
    holes = []
    ang = radians(ang_deg)
    # Dirección de cada ala (unidad): a la izquierda y derecha del centro
    # En la cara sólo dibujamos collares, así que ubicamos pares a distancias crecientes
    for k in range(n_pairs):
        r = (k + 1) * d_core
        # Izquierda
        holes.append(_pt(cx - r * cos(ang), cy - r * sin(ang), delay=k, note="cuna L"))
        # Derecha
        holes.append(_pt(cx + r * cos(ang), cy - r * sin(ang), delay=k, note="cuna R"))
    # Vértice (opcional uno o dos tiros cortos)
    holes.append(_pt(cx, cy, delay=0, note="cuna vértice"))
    return holes


# CUELE ABANICO (Fan)


def cuele_abanico(center=(0.0, 0.0), radio=0.5, n=10, ang_start=25, ang_end=10):
    """
    Abanico: n collares distribuidos en arco; cada uno apunta con
    una inclinación entre ang_start y ang_end (grados).
    Para la cara (2D) ubicamos puntos en un pequeño arco alrededor del centro.
    Retardos radiales del centro hacia afuera: 0..N
    """
    cx, cy = center
    holes = []
    if n < 3:
        n = 3
    for i in range(n):
        # Arco semicircular pequeño delante del centro
        theta = -3.14159 / 4 + i * (3.14159 / 2) / (n - 1)  # de -45° a +45° aprox
        x = cx + radio * cos(theta)
        y = cy + radio * sin(theta)
        holes.append(_pt(x, y, delay=i // 3, note="abanico"))
    return holes


# CUELE BETHUNE


def cuele_bethune(center=(0.0, 0.0), d_core=0.20, n_rows=3):
    """
    Bethune: grupos en abanico con distintas longitudes (en croquis 0.8–2.2 m y ángulos 24–34°).
    En la cara (2D) lo representamos como 3 arcos concéntricos de collares.
    Retardos por arco: 0 (interno), 1 (medio), 2 (externo).
    """
    cx, cy = center
    holes = []
    for r_i, delay in zip([0.4 * d_core, 0.8 * d_core, 1.2 * d_core], [0, 1, 2]):
        for j in range(5):  # 5 puntos por arco
            theta = -3.14159 / 3 + j * (2 * 3.14159 / 3) / 4  # ~ -60°..+60°
            x = cx + r_i * cos(theta)
            y = cy + r_i * sin(theta)
            holes.append(_pt(x, y, delay=delay, note="bethune"))
    return holes


# Helper: desplazar/rotar un cuele (opcional)


def transform(holes, dx=0.0, dy=0.0):
    """Aplica un desplazamiento plano a todos los collares."""
    out = []
    for h in holes:
        h2 = dict(h)
        h2["x"] += dx
        h2["y"] += dy
        out.append(h2)
    return out
