# plot_utils.py
"""
Funciones auxiliares para graficar resultados del optimizador de tronaduras.

Incluye:
    - generación de mapas de isocosto (fragmentación P80 vs energía específica),
      donde cada curva representa un nivel de igual costo total.

Uso:
    from plot_utils import generar_curvas_isocosto
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.interpolate import griddata

# === 🎨 Configuración global para modo oscuro ===
mpl.rcParams.update({
    "legend.facecolor": "#222",      # Fondo oscuro para leyendas
    "legend.edgecolor": "gray",      # Borde gris
    "legend.labelcolor": "white",    # Texto blanco
    "legend.fontsize": 8,
    "axes.labelcolor": "white",      # Ejes blancos
    "xtick.color": "white",
    "ytick.color": "white",
    "axes.titlecolor": "white",
})


def generar_curvas_isocosto(ax, energia_vals, fragmentacion_vals, costo_vals):
    """
    Genera un mapa de isocostos: curvas que representan el mismo costo total
    en función de la fragmentación (P80) y la energía específica.

    Parámetros
    ----------
    ax : matplotlib.axes.Axes
        Eje donde se graficará el mapa.
    energia_vals : array-like
        Energía específica efectiva (MJ/m³) de cada simulación.
    fragmentacion_vals : array-like
        Tamaño P80 estimado (mm) correspondiente a cada punto.
    costo_vals : array-like
        Costo total ($) asociado a cada diseño.

    Retorna
    -------
    contour : matplotlib.contour.QuadContourSet
        Objeto de contorno útil para añadir un colorbar o exportar el gráfico.
    """

    # --- Validar datos ---
    energia_vals = np.asarray(energia_vals)
    fragmentacion_vals = np.asarray(fragmentacion_vals)
    costo_vals = np.asarray(costo_vals)

    mask = (energia_vals > 0) & (fragmentacion_vals > 0) & (costo_vals > 0)
    energia_vals, fragmentacion_vals, costo_vals = (
        energia_vals[mask],
        fragmentacion_vals[mask],
        costo_vals[mask],
    )

    if len(energia_vals) < 3:
        ax.text(
            0.5, 0.5, "Datos insuficientes para generar curvas",
            ha="center", va="center", color="white", transform=ax.transAxes
        )
        return None

    # --- Crear malla regular para interpolar ---
    energia_grid, fragm_grid = np.meshgrid(
        np.linspace(energia_vals.min(), energia_vals.max(), 80),
        np.linspace(fragmentacion_vals.min(), fragmentacion_vals.max(), 80)
    )

    costo_interp = griddata(
        (energia_vals, fragmentacion_vals),
        costo_vals,
        (energia_grid, fragm_grid),
        method="cubic"
    )

    # --- Dibujar curvas de igual costo ---
    contour = ax.contourf(
        energia_grid, fragm_grid, costo_interp,
        levels=12, cmap="plasma", alpha=0.85
    )
    ax.contour(
        energia_grid, fragm_grid, costo_interp,
        colors="white", linewidths=0.5, alpha=0.7
    )

    # --- Puntos simulados ---
    ax.scatter(
        energia_vals, fragmentacion_vals,
        c="#00ffff", s=65, edgecolors="black", linewidths=0.8, zorder=10,
        label="Simulaciones reales"
    )
    ax.legend(loc="upper right")

    # --- Estilo general ---
    ax.set_facecolor("#2B2B2B")
    ax.set_xlabel("Energía específica efectiva (MJ/m³)")
    ax.set_ylabel("Fragmentación P80 (mm)")
    ax.set_title(
        "Mapa de costo total — Relación Fragmentación (P80) vs Energía específica\n"
        "(curvas: niveles de igual costo | puntos azules: simulaciones reales)",
        pad=10, fontsize=11
    )

    # --- Colorbar ---
    cbar = plt.colorbar(contour, ax=ax, label="Costo total ($)")
    cbar.ax.yaxis.label.set_color("white")
    cbar.ax.tick_params(colors="white")

    # --- Ajustes finales ---
    ax.set_xlim(energia_vals.min() * 0.9, energia_vals.max() * 1.05)
    ax.set_ylim(fragmentacion_vals.min() * 0.95, fragmentacion_vals.max() * 1.05)
    plt.tight_layout(pad=1.0)

    return contour
