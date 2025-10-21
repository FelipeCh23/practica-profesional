
"""
Script de optimización para diseños de tronadura en abanico.

Este programa implementa la lógica de un diagrama de flujo para encontrar
el diseño de perforación más económico que cumpla con un presupuesto dado.
Itera a través de un rango de posibles diseños, los genera geométricamente,
calcula su costo y selecciona el mejor candidato.
"""
import numpy as np
import shapely as shp
import json

# ===========================================================================
# SECCIÓN 1: FUNCIONES GEOMÉTRICAS AUXILIARES (Adaptadas de appRing.py)
# ===========================================================================

def sort_points(geometry, pivot: shp.Point):
    """
    Ordena los puntos de una geometría desde el más cercano al más lejano al pivote.

    Args:
        geometry: Una geometría de Shapely (ej. MultiPoint).
        pivot (shp.Point): El punto de referencia para medir la distancia.

    Returns:
        list: Una lista de puntos de Shapely ordenados.
    """
    points = list(shp.extract_unique_points(geometry).geoms)
    points.sort(key=lambda point: point.distance(pivot))
    return points

# ===========================================================================
# SECCIÓN 2: LÓGICA DE GENERACIÓN DE DISEÑOS (Adaptada de HolesDesigner)
# ===========================================================================

def find_endpoints(stope: shp.Polygon, drift: shp.Polygon, pivot: shp.Point, line: shp.LineString, max_length: float):
    """
    Halla el collar (inicio en la galería) y el fondo (fin en el caserón o largo máx.) de una perforación.

    Args:
        stope (shp.Polygon): Polígono del caserón.
        drift (shp.Polygon): Polígono de la galería.
        pivot (shp.Point): Punto de origen de la perforación.
        line (shp.LineString): Línea directriz que define el ángulo del tiro.
        max_length (float): Longitud máxima permitida para la perforación.

    Returns:
        tuple: Una tupla con el punto de collar y el punto de fondo (o None si es inválido).
    """
    collar = line.intersection(drift.exterior)
    if collar.is_empty:
        return None, None # La línea no cruza la galería, tiro inválido.

    # El punto de collar puede ser una geometría compleja si cruza en una esquina
    if not isinstance(collar, shp.Point):
        collar = collar.geoms[0]

    # Intersección con el caserón
    intersections = line.intersection(stope.exterior)
    
    if intersections.is_empty:
        # Si no hay intersección, el tiro no llega al caserón. Podríamos descartarlo o usar largo máx.
        # Por ahora, lo descartamos para asegurar que todos los tiros lleguen al objetivo.
        return None, None

    # Ordenamos las intersecciones para quedarnos con la más lejana al pivote
    toe = sort_points(intersections, pivot)[-1]

    # Verificamos que el tiro no exceda la longitud máxima
    if pivot.distance(toe) > max_length:
        toe = line.interpolate(max_length + pivot.distance(collar))

    return collar, toe

def angular_method(stope_geom, drift_geom, pivot_geom, params):
    """
    Genera un abanico de perforación usando espaciamiento angular constante.

    Args:
        stope_geom (list): Coordenadas del polígono del caserón.
        drift_geom (list): Coordenadas del polígono de la galería.
        pivot_geom (list): Coordenadas del punto pivote.
        params (dict): Diccionario con parámetros de diseño ('min_angle', 'max_angle', 'holes_number', 'max_length').

    Returns:
        dict: Un diccionario con la geometría de los tiros generados.
    """
    collars, toes = [], []
    stope = shp.Polygon(stope_geom)
    drift = shp.Polygon(drift_geom)
    pivot = shp.Point(pivot_geom)

    angle_range = abs(params['max_angle'] - params['min_angle'])
    
    if params['holes_number'] > 1:
        angle_step = angle_range / (params['holes_number'] - 1)
    else:
        angle_step = 0

    current_angle = params['min_angle']

    for _ in range(params['holes_number']):
        # Se crea una línea de referencia muy larga y se rota al ángulo deseado
        ref_line = shp.LineString([pivot, (pivot.x, pivot.y + 10000)])
        rotated_line = shp.affinity.rotate(ref_line, angle=current_angle, origin=pivot)

        collar, toe = find_endpoints(stope, drift, pivot, rotated_line, params['max_length'])

        if collar and toe:
            collars.append(list(collar.coords)[0])
            toes.append(list(toe.coords)[0])

        current_angle += angle_step

    return {"geometry": [collars, toes]}

# ===========================================================================
# SECCIÓN 3: LÓGICA DE CÁLCULO DE COSTOS
# ===========================================================================

def calculate_total_cost(design: dict, unit_costs: dict) -> float:
    """
    Calcula el costo total de un diseño (perforación, explosivos, detonadores).

    Args:
        design (dict): Objeto de diseño completo.
        unit_costs (dict): Diccionario con los precios unitarios.

    Returns:
        float: El costo total calculado.
    """
    # 1. Costo de Perforación
    total_drill_length = 0
    if 'holes' in design and design['holes']['geometry'][0]:
        collars = np.array(design['holes']['geometry'][0])
        toes = np.array(design['holes']['geometry'][1])
        total_drill_length = np.sum(np.linalg.norm(toes - collars, axis=1))
    
    cost_drilling = total_drill_length * unit_costs['perforacion_por_metro']

    # 2. Costo de Explosivos (AÚN NO IMPLEMENTADO - SIMPLIFICADO)
    cost_explosives = 0.0
    
    # 3. Costo de Detonadores (simplificado, un detonador por tiro)
    num_detonators = len(design.get('holes', {}).get('geometry', [[]])[0])
    cost_detonators = num_detonators * unit_costs['detonador_por_unidad']

    return cost_drilling + cost_explosives + cost_detonators

# ===========================================================================
# SECCIÓN 4: EL OPTIMIZADOR (Implementación del Diagrama de Flujo)
# ===========================================================================

def optimize_fan_design(stope_geom, drift_geom, pivot_geom, budget_params):
    """
    Bucle principal que itera para encontrar el mejor diseño de abanico.

    Args:
        stope_geom (list): Coordenadas del polígono del caserón.
        drift_geom (list): Coordenadas del polígono de la galería.
        pivot_geom (list): Coordenadas del punto pivote.
        budget_params (dict): Parámetros de presupuesto y optimización.

    Returns:
        dict: El mejor diseño encontrado que cumple con el presupuesto, o None si no se encuentra ninguno.
    """
    valid_designs = []
    
    # Interpretamos Smin y Smax como el número mínimo y máximo de tiros a probar
    s_min_tiros = budget_params['s_min_tiros']
    s_max_tiros = budget_params['s_max_tiros']
    
    print(f"🚀 Iniciando optimización. Probando de {s_min_tiros} a {s_max_tiros} tiros...")

    for num_tiros in range(s_min_tiros, s_max_tiros + 1):
        
        print(f"\n--- Probando diseño con {num_tiros} tiros ---")
        
        # 1. CONSTRUIR EL DISEÑO usando el método angular
        design_params = {
            'min_angle': -45.0,
            'max_angle': 45.0,
            'max_length': 30.0, # Longitud máxima de perforación en metros
            'holes_number': num_tiros
        }
        
        holes_design = angular_method(stope_geom, drift_geom, pivot_geom, design_params)
        
        # Ensamblamos un objeto de diseño completo (simplificado)
        current_design = {
            "holes": holes_design,
            # Aquí se generarían 'charges' y 'blasts' en una versión más completa
        }

        # 2. CALCULAR EL COSTO
        total_cost = calculate_total_cost(current_design, budget_params['unit_costs'])
        print(f"Costo del diseño generado: ${total_cost:,.2f}")

        # 3. VERIFICAR PRESUPUESTO
        if total_cost <= budget_params['presupuesto_maximo']:
            print(f"✅ Diseño VÁLIDO (dentro del presupuesto de ${budget_params['presupuesto_maximo']:,.2f})")
            valid_designs.append({'design': current_design, 'cost': total_cost})
        else:
            print(f"❌ Diseño INVÁLIDO (excede el presupuesto)")

    # 4. SELECCIONAR EL MEJOR DISEÑO
    if not valid_designs:
        print("\nNo se encontró ningún diseño que cumpliera con el presupuesto.")
        return None
    
    # Criterio de optimización: el más barato de los válidos
    best_design = min(valid_designs, key=lambda x: x['cost'])
    
    print("\n=========================================")
    print("🏆 Optimización Finalizada 🏆")
    print(f"Se encontraron {len(valid_designs)} diseños válidos.")
    
    best_design_info = best_design['design']['holes']
    num_tiros_optimo = len(best_design_info['geometry'][0])
    costo_optimo = best_design['cost']
    
    print(f"El mejor diseño tiene {num_tiros_optimo} tiros y un costo de ${costo_optimo:,.2f}")
    print("=========================================")
    
    return best_design

# ===========================================================================
# SECCIÓN 5: EJECUCIÓN DEL SCRIPT
# ===========================================================================

if __name__ == '__main__':
    # --- PARÁMETROS DE ENTRADA (¡Puedes modificar estos valores!) ---
    
    # 1. Geometrías
    stope_polygon = [[0,0], [25,0], [25,35], [0,35]]
    drift_polygon = [[10,12], [15,12], [15,16], [10,16]]
    pivot_point = [12.5, 14]

    # 2. Parámetros de Presupuesto y Optimización
    budget_parameters = {
        "presupuesto_maximo": 15000.0,
        "s_min_tiros": 5,  # Número MÍNIMO de tiros a probar
        "s_max_tiros": 15, # Número MÁXIMO de tiros a probar
        "unit_costs": {
            "perforacion_por_metro": 30.0,
            "explosivo_por_kg": 2.2, # Aún no se usa en el cálculo
            "detonador_por_unidad": 18.0
        }
    }
    
    # --- EJECUTAR EL OPTIMIZADOR ---
    resultado_optimo = optimize_fan_design(stope_polygon, drift_polygon, pivot_point, budget_parameters)

    # --- GUARDAR EL RESULTADO ---
    if resultado_optimo:
        try:
            with open('mejor_diseno.json', 'w') as f:
                # Guardamos solo el diccionario del diseño, no el costo.
                json.dump(resultado_optimo['design'], f, indent=4)
            print("\nEl mejor diseño se ha guardado en el archivo 'mejor_diseno.json'")
        except Exception as e:
            print(f"\nNo se pudo guardar el archivo de resultado. Error: {e}")