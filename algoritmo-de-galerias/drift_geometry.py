"""
drift_geometry.py - Geometría de galerías subterráneas

Cada función calcula los vértices de una galería centrada en un punto
definido por el usuario (click del mouse). Todas siguen la estructura
del ejemplo del profe: actualizar centro, calcular posiciones relativas,
devolver vértices.
"""

from math import cos, sin, pi, pow


# Utilidad interna

def _update_center(center_x: float, center_y: float,
                   offset_x: float = 0, offset_y: float = 0):
    """
    Actualiza el centro de dibujo con el offset proporcionado.

    Argumentos:
    center_x(float): coordenada x inicial
    center_y(float): coordenada y inicial
    offset_x(float): desplazamiento en x
    offset_y(float): desplazamiento en y

    Retorna:
    center_x_actualizado(float), center_y_actualizado(float)
    """
    return center_x + offset_x, center_y + offset_y


# 1. Rectangular

def rectangular(center_x: float, center_y: float, width: float, height: float):
    """
    Calcula los vértices de una galería rectangular en base a un centro.

    Argumentos:
    center_x, center_y: centro elegido por click
    width, height: dimensiones de la galería

    Retorna:
    lista de 4 vértices [(x1, y1), ..., (x4, y4)]
    """
    dx = width / 2
    dy = height / 2
    return [
        (center_x - dx, center_y - dy),
        (center_x + dx, center_y - dy),
        (center_x + dx, center_y + dy),
        (center_x - dx, center_y + dy)
    ]


# 2. Semicircular


def semicircular(center_x: float, center_y: float, radius: float, n_points: int = 20,
                 offset_x: float = 0, offset_y: float = 0):
    """
    Calcula los vértices de una galería semicircular con base plana.

    La galería se construye centrada en el punto definido por el usuario
    (center_x, center_y), que representa el click del mouse en la pantalla.

    Argumentos:
    center_x (float): coordenada X del centro de referencia
    center_y (float): coordenada Y del centro de referencia
    radius (float): radio de la semicircunferencia superior
    n_points (int, opcional): cantidad de puntos para suavizar el arco superior (por defecto 20)
    offset_x (float, opcional): desplazamiento en X respecto al centro (por defecto 0)
    offset_y (float, opcional): desplazamiento en Y respecto al centro (por defecto 0)

    Retorna:
    list of tuple: lista de vértices [(x1,y1), (x2,y2), ..., (xn,yn)] que forman la galería semicircular cerrada
    """
    # Actualizar centro con offset
    cx, cy = center_x + offset_x, center_y + offset_y
    vertices = []

    # Base izquierda
    vertices.append((cx - radius, cy))

    # Arco superior
    for i in range(n_points + 1):
        theta = pi * i / n_points
        x = cx - radius * cos(theta)
        y = cy + radius * sin(theta)
        vertices.append((x, y))

    # Base derecha
    vertices.append((cx + radius, cy))

    # Cerrar el polígono volviendo al inicio
    vertices.append((cx - radius, cy))

    return vertices



# 3. D-Shaped

def d_shaped(center_x: float, center_y: float, width: float, height: float, n_points: int = 30,
             offset_x: float = 0, offset_y: float = 0):
    """
    Calcula los vértices de una galería D-Shaped: base plana + arco superior semicircular.

    La galería se construye centrada en el punto definido por el usuario
    (center_x, center_y), que representa el click del mouse en la pantalla.
    La altura controla cuánto se alargan las paredes verticales; si se pone igual al radio,
    se obtiene una D perfecta (sin alargamiento).

    Argumentos:
    center_x (float): coordenada X del centro de referencia
    center_y (float): coordenada Y del centro de referencia
    width (float): ancho total de la galería
    height (float): altura total de la galería incluyendo arco y paredes verticales
    n_points (int, opcional): cantidad de puntos para suavizar el arco superior (por defecto 30)
    offset_x (float, opcional): desplazamiento en X respecto al centro (por defecto 0)
    offset_y (float, opcional): desplazamiento en Y respecto al centro (por defecto 0)

    Retorna:
    list of tuple: lista de vértices [(x1,y1), ..., (xn,yn)] que forman la galería D-Shaped cerrada
    """
    # Actualizar centro con offset
    center_x, center_y = _update_center(center_x, center_y, offset_x, offset_y)

    radius = width / 2
    wall_height = max(height - radius, 0)

    vertices = []

    # Base izquierda
    x_left = center_x - radius
    x_right = center_x + radius
    y_base = center_y
    vertices.append((x_left, y_base))

    # Pared izquierda vertical (solo si wall_height > 0)
    y_top = y_base + wall_height
    vertices.append((x_left, y_top))

    # Arco superior de izquierda a derecha
    for i in range(n_points + 1):
        theta = pi * (i / n_points)  # 0 a pi
        x = center_x - radius * cos(theta)  # izquierda a derecha
        y = y_top + radius * sin(theta)
        vertices.append((x, y))

    # Pared derecha vertical
    vertices.append((x_right, y_top))

    # Cerrar en la base derecha y volver al inicio
    vertices.append((x_right, y_base))
    vertices.append((x_left, y_base))

    return vertices



# 4. Horseshoe




def horseshoe(center_x: float, center_y: float, width: float, height: float,
              n_curve: int = 10, offset_x: float = 0, offset_y: float = 0):
    """
    Calcula los vértices de una galería Horseshoe (herradura) centrada en un punto de referencia.

    La galería tiene paredes rectas verticales y un arco superior suavizado mediante n_curve puntos.
    El centro (center_x, center_y) corresponde al click del usuario en la pantalla.
    La altura controla la extensión vertical de las paredes y el arco se escala en función del ancho.

    Argumentos:
    center_x (float): coordenada X del centro de referencia
    center_y (float): coordenada Y del centro de referencia
    width (float): ancho total de la herradura
    height (float): altura de las paredes rectas
    n_curve (int, opcional): cantidad de puntos para suavizar la curva superior (por defecto 10)
    offset_x (float, opcional): desplazamiento en X respecto al centro (por defecto 0)
    offset_y (float, opcional): desplazamiento en Y respecto al centro (por defecto 0)

    Retorna:
    list of tuple: lista de vértices [(x1,y1), ..., (xn,yn)] que forman la herradura cerrada
    """
    # Actualizar centro con offset
    center_x, center_y = _update_center(center_x, center_y, offset_x, offset_y)

    dx = width / 2  # mitad del ancho
    dy = height     # altura de las paredes rectas

    # Puntos de la base y paredes
    left_base = (center_x - dx, center_y)
    right_base = (center_x + dx, center_y)
    left_top = (center_x - dx, center_y + dy)
    right_top = (center_x + dx, center_y + dy)

    # Puntos de la curva superior (semi-arco)
    curve_points = []
    for i in range(n_curve + 1):
        theta = pi * i / n_curve  # de 0 a pi
        x = center_x - dx + (width) * 0.5 * (1 - cos(theta))  # escala horizontal
        y = center_y + dy + (width / 2) * sin(theta)          # arco hacia arriba
        curve_points.append((x, y))

    # Unir vértices en orden para formar la herradura cerrada
    verts = [left_base, left_top] + curve_points + [right_top, right_base]

    return verts



# 5. Bézier Tunnel (techo curvo, paredes rectas)

def bezier_tunnel(center_x: float, center_y: float, width: float, wall_height: float,
                  curve_height: float, n_points: int = 30):
    """
    Calcula los vértices de una galería tipo Bezier con paredes verticales y techo curvo.

    La galería tiene paredes rectas y un techo suavizado mediante una curva Bezier cúbica.
    El centro (center_x, center_y) corresponde al click del usuario en la pantalla.
    La altura de las paredes y la altura de la curva se controlan con wall_height y curve_height.

    Argumentos:
    center_x (float): coordenada X del centro de referencia
    center_y (float): coordenada Y del centro de referencia
    width (float): ancho total de la galería
    wall_height (float): altura de las paredes verticales
    curve_height (float): altura de la curva tipo Bezier
    n_points (int, opcional): cantidad de puntos para suavizar la curva (por defecto 30)

    Retorna:
    list of tuple: lista de vértices [(x1,y1), ..., (xn,yn)] que forman la galería cerrada
    """
    # Actualizamos centro
    center_x, center_y = _update_center(center_x, center_y)

    # Puntos de control de la curva tipo Bezier
    x0, y0 = center_x - width/2, center_y + wall_height
    x3, y3 = center_x + width/2, center_y + wall_height
    x1, y1 = x0 + width/3, y0 + curve_height
    x2, y2 = x0 + 2*width/3, y0 + curve_height

    verts = []

    # Curva superior (Bezier cúbica)
    for i in range(n_points + 1):
        t = i / n_points
        Bx = pow(1-t,3)*x0 + 3*pow(1-t,2)*t*x1 + 3*(1-t)*pow(t,2)*x2 + pow(t,3)*x3
        By = pow(1-t,3)*y0 + 3*pow(1-t,2)*t*y1 + 3*(1-t)*pow(t,2)*y2 + pow(t,3)*y3
        verts.append((Bx, By))

    # Pared derecha
    verts.append((x3, center_y))
    # Base
    verts.append((x0, center_y))
    # Pared izquierda
    verts.append((x0, y0))

    return verts
