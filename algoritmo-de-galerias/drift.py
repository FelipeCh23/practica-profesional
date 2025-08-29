"""
Módulo: drift.py
Autor: Felipe Chávez
Descripción:
    Contiene funciones para generar la geometría de diferentes tipos de galerías subterráneas.
    Cada función recibe parámetros como ancho, alto o radio, y devuelve una lista de vértices (x, y)
    que definen la sección transversal de la galería.

Uso:
    from drift import rectangular, circular, horseshoe, trapezoidal, d_shaped, bezier

    vertices = rectangular(5, 3)
"""

import math
import math

# ------------------------------
# Funciones de utilidad
# ------------------------------
def polygon_centroid(vertices):
    """Calcula el centroide (Cx, Cy) de un polígono"""
    x_list, y_list = zip(*vertices)
    n = len(vertices)
    A = 0
    Cx = 0
    Cy = 0
    for i in range(n):
        xi, yi = vertices[i]
        xi1, yi1 = vertices[(i + 1) % n]
        cross = xi * yi1 - xi1 * yi
        A += cross
        Cx += (xi + xi1) * cross
        Cy += (yi + yi1) * cross
    A *= 0.5
    if A == 0:
        return (0, 0)
    Cx /= (6 * A)
    Cy /= (6 * A)
    return (Cx, Cy)

def center_polygon(vertices):
    """Traslada los vértices para que el centroide quede en 0,0"""
    Cx, Cy = polygon_centroid(vertices)
    return [(x - Cx, y - Cy) for x, y in vertices]


# -------------------------------------------------
# 1. Rectangular
# -------------------------------------------------
def rectangular(width, height):
    vertices = [
        (0, 0),
        (width, 0),
        (width, height),
        (0, height)
    ]
    return center_polygon(vertices)


# -------------------------------------------------
# 2. Circular
# -------------------------------------------------
def circular(radius, n_points=60):
    vertices = []
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertices.append((x, y))
    return center_polygon(vertices)


# -------------------------------------------------
# 3. Trapezoidal
# -------------------------------------------------
def trapezoidal(top_width, bottom_width, height):
    offset = (bottom_width - top_width) / 2
    vertices = [
        (0, 0),
        (bottom_width, 0),
        (bottom_width - offset, height),
        (offset, height)
    ]
    return center_polygon(vertices)


# -------------------------------------------------
# 4. Horseshoe (Herradura)
# -------------------------------------------------
def horseshoe(width, height, radius=None, n_points=50):
    if radius is None:
        radius = width / 2

    vertices = []
    # Semicírculo superior (de izquierda a derecha)
    for i in range(n_points + 1):
        theta = math.pi * (1 - i / n_points)  # de π a 0
        x = radius * math.cos(theta)
        y = height + radius * math.sin(theta)
        vertices.append((x, y))

    # Pared derecha (bajar de altura a 0)
    vertices.append((radius, 0))

    # Base (de derecha a izquierda)
    vertices.append((-radius, 0))

    return center_polygon(vertices)


# -------------------------------------------------
# 5. D-Shaped (Semicircular sobre base plana)
# -------------------------------------------------
def d_shaped(width, height, n_points=30):
    radius = width / 2
    wall_height = height - radius

    vertices = []
    for i in range(n_points + 1):
        angle = math.pi * i / n_points  # 0 a pi
        x = radius * (1 - math.cos(angle))
        y = wall_height + radius * math.sin(angle)
        vertices.append((x, y))

    vertices += [
        (width, 0),
        (0, 0)
    ]

    return center_polygon(vertices)


# -------------------------------------------------
# 6. Bézier (para secciones personalizadas)
# -------------------------------------------------
def bezier(p0, p1, p2, n_points=20):
    vertices = []
    for t in [i/n_points for i in range(n_points+1)]:
        x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
        y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
        vertices.append((x, y))
    return center_polygon(vertices)

import math

def rounded_rectangle(width, height, radius=0.5, n_corner_points=10):
    """
    Devuelve los vértices de un rectángulo con esquinas redondeadas.
    
    Parámetros:
        width (float): ancho total del rectángulo
        height (float): alto total del rectángulo
        radius (float): radio de las esquinas
        n_corner_points (int): cantidad de puntos para aproximar cada curva
        
    Retorna:
        list[(x, y)]: lista de vértices en sentido antihorario, centrada en el centroide
    """
    if radius > min(width, height)/2:
        radius = min(width, height)/2  # limitar radio para que no se solape

    vertices = []

    # Definir centros de cada esquina
    corners = [
        (width/2 - radius, height/2 - radius),    # esquina superior derecha
        (-width/2 + radius, height/2 - radius),   # esquina superior izquierda
        (-width/2 + radius, -height/2 + radius),  # esquina inferior izquierda
        (width/2 - radius, -height/2 + radius)    # esquina inferior derecha
    ]

    # Ángulos para cada esquina (de 0 a pi/2)
    corner_angles = [
        [0, math.pi/2],           # sup der
        [math.pi/2, math.pi],     # sup izq
        [math.pi, 3*math.pi/2],   # inf izq
        [3*math.pi/2, 2*math.pi]  # inf der
    ]

    # Construir las esquinas con arcos
    for i, ((cx, cy), (angle_start, angle_end)) in enumerate(zip(corners, corner_angles)):
        for j in range(n_corner_points):
            t = j / (n_corner_points - 1)
            angle = angle_start + t * (angle_end - angle_start)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y))

    return vertices
