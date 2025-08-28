# Geometría de galerias 
# drift.py

import math

def rectangle(width, height):
    """
    Determina la geometría de una galería rectangular.
    Devuelve los vértices del polígono en sentido horario empezando desde la esquina inferior izquierda.
    """
    vertices = [
        (0, 0),            # esquina inferior izquierda
        (width, 0),        # esquina inferior derecha
        (width, height),   # esquina superior derecha
        (0, height)        # esquina superior izquierda
    ]
    return vertices

def rounded(width, height, radius):
    """
    Determina la geometría de una galería rectangular con esquinas redondeadas (arco de radio 'radius').
    Devuelve los vértices de la forma aproximada como polígono (puntos de las esquinas + arcos simplificados).
    """
    # Para simplificar, representamos cada esquina con 4 puntos del arco
    points_per_corner = 4
    vertices = []

    # Esquinas en orden: inferior izquierda, inferior derecha, superior derecha, superior izquierda
    corners = [
        (radius, radius, math.pi, 1.5*math.pi),        # inf izq
        (width - radius, radius, 1.5*math.pi, 2*math.pi), # inf der
        (width - radius, height - radius, 0, 0.5*math.pi), # sup der
        (radius, height - radius, 0.5*math.pi, math.pi)    # sup izq
    ]

    for cx, cy, start_angle, end_angle in corners:
        for i in range(points_per_corner + 1):
            angle = start_angle + (end_angle - start_angle) * i / points_per_corner
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y))

    return vertices

def horseshoe(width, height, radius):
    """
    Determina la geometría de una galería en forma de herradura (Horseshoe).
    Techo semicircular y paredes verticales.
    Devuelve los vértices del polígono empezando desde la esquina inferior izquierda.
    """
    # Paredes verticales
    bottom_left = (0, 0)
    bottom_right = (width, 0)
    top_left = (0, height - radius)
    top_right = (width, height - radius)

    # Arco superior
    points_arc = []
    segments = 10  # número de puntos del arco
    for i in range(segments + 1):
        angle = math.pi - (math.pi * i / segments)
        x = width/2 + (width/2) * math.cos(angle)
        y = height - radius + radius * math.sin(angle)
        points_arc.append((x, y))

    vertices = [bottom_left, bottom_right, top_right] + points_arc + [top_left]
    return vertices

def trapezoidal(bottom_width, top_width, height):
    """
    Determina la geometría de una galería trapezoidal (base más ancha que el techo).
    Devuelve los vértices del polígono empezando desde la esquina inferior izquierda.
    """
    vertices = [
        (0, 0),                   # esquina inferior izquierda
        (bottom_width, 0),        # esquina inferior derecha
        (top_width, height),       # esquina superior derecha
        (0, height)               # esquina superior izquierda
    ]
    return vertices

def d_shaped(width, height, radius):
    """
    Determina la geometría de una galería D-shaped (techo semicircular, base plana).
    Devuelve los vértices del polígono.
    """
    # Base
    vertices = [(0, 0), (width, 0)]
    # Arco superior semicircular
    segments = 10
    for i in range(segments + 1):
        angle = math.pi - (math.pi * i / segments)
        x = width/2 + (width/2) * math.cos(angle)
        y = height - radius + radius * math.sin(angle)
        vertices.append((x, y))
    return vertices
