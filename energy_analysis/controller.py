from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as shp

try:
    import plotly.graph_objects as go

    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False


class EnergyAnalysisController:
    """
    CONTROLLER:
    - Conecta señales (command / trace) de la View
    - Carga listas desde el Model a la View (combos)
    - Implementa lo que en tu clase original eran:
        update_values, update_units, valid_params, plot_energy, plot_energy3D
      (misma lógica, solo que usando view.* y model.*)
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.params: Dict = {}  # espejo del dict de tu clase original

        # Poblar combo de patrones: primera opción "" (PatronDemo vacío)
        patterns = [""] + self.model.get_patterns()
        self.view.combo_charges.configure(values=patterns)

        # Conectar eventos (antes estaban en View)
        self.view.combo_charges.configure(command=self.update_values)
        self.view.combo_section.configure(command=self.update_values)
        self.view.combo_type.configure(command=self.update_units)
        self.view.check_3d.configure(command=self.view.activate_max)
        self.view.button_plot.configure(command=self.plot_energy)

    # ---------------------- Copia de tus métodos (adaptados) ----------------------

    def update_values(self, *_):
        """Actualiza los parámetros y geometrías de evaluación (idéntico en espíritu)."""
        charges_name = self.view.pattern.get()
        if charges_name == "":
            return

        g = self.model.get_geometry(charges_name)
        collars = g["collars"]
        toes = g["toes"]
        charges_diam = g["diameter"]
        drift_geom = g["drift_geom"]
        stope_geom = g["stope_geom"]
        rock_dens = g["rock_dens"]
        expl_dens = g["expl_dens"]
        burden = g.get("burden", 2.0) or 2.0

        # Definir límites del plano (idéntico a tu lógica)
        xmin, ymin, xmax, ymax = shp.Polygon(stope_geom).bounds
        xmid = round(0.5 * (xmin + xmax), 1)
        ymid = round(0.5 * (ymin + ymax), 1)
        zmid = 0.0

        self.view.xmin.set(round(1.1 * xmin - 0.1 * xmax, 1))
        self.view.xmax.set(round(1.1 * xmax - 0.1 * xmin, 1))
        self.view.ymin.set(round(1.1 * ymin - 0.1 * ymax, 1))
        self.view.ymax.set(round(1.1 * ymax - 0.1 * ymin, 1))
        self.view.zmin.set(round(-10 * burden, 1))
        self.view.zmax.set(round(+10 * burden, 1))

        self.view.entry_xmax.configure(state="normal")
        self.view.entry_ymax.configure(state="normal")
        self.view.entry_zmax.configure(state="normal")

        if self.view.section.get() == "Transversal":
            self.view.zmin.set(zmid)
            self.view.zmax.set(zmid)
            if not self.view.tridimensional.get():
                self.view.entry_zmax.configure(state="disabled")

        elif self.view.section.get() == "Longitudinal":
            self.view.xmin.set(xmid)
            self.view.xmax.set(xmid)
            if not self.view.tridimensional.get():
                self.view.entry_xmax.configure(state="disabled")

        else:
            self.view.ymin.set(ymid)
            self.view.ymax.set(ymid)
            if not self.view.tridimensional.get():
                self.view.entry_ymax.configure(state="disabled")

        # Establecer parámetros de evaluación:
        self.view.rock_dens.set(str(rock_dens))
        self.view.expl_dens.set(str(expl_dens))
        self.view.diameter.set(str(charges_diam))

        # Guardar en params (como tu self.params.update)
        self.params.update(
            {
                "charges_collar": collars,
                "charges_toe": toes,
                "drift_geom": drift_geom,
                "stope_geom": stope_geom,
            }
        )

    def update_units(self, *_):
        """Actualiza las unidades del factor de energía"""
        if self.view.type.get() == "Volumen":
            self.view.units_cutoff.configure(text="kg/m³")
        else:
            self.view.units_cutoff.configure(text="kg/t")

    def valid_params(self) -> bool:
        """Valida los parámetros (mismo contenido de tu método)."""
        charge_name = self.view.pattern.get()
        if charge_name == "":
            self.view.info(
                "Análisis de Energía",
                "Seleccione un patrón de carga para calcular su distribución de energía.",
            )
            return False

        try:
            xmin = float(self.view.xmin.get())
            xmax = float(self.view.xmax.get())
            ymin = float(self.view.ymin.get())
            ymax = float(self.view.ymax.get())
            zmin = float(self.view.zmin.get())
            zmax = float(self.view.zmax.get())
            cutoff = float(self.view.cutoff.get())
            resol = int(self.view.resol.get())
            levels = int(self.view.levels.get())
            rock_dens = float(self.view.rock_dens.get())
            expl_dens = float(self.view.expl_dens.get())
            diameter = float(self.view.diameter.get())
        except Exception:
            self.view.error(
                "Análisis de Energía",
                "Complete todos los campos de entrada con valores numéricos.",
            )
            return False

        if xmin > xmax:
            self.view.error(
                "Análisis de Energía",
                "El límite inferior de X no puede ser mayor que el superior.",
            )
            return False
        if ymin > ymax:
            self.view.error(
                "Análisis de Energía",
                "El límite inferior de Y no puede ser mayor que el superior.",
            )
            return False
        if zmin > zmax:
            self.view.error(
                "Análisis de Energía",
                "El límite inferior de Z no puede ser mayor que el superior.",
            )
            return False
        if cutoff <= 0:
            self.view.error(
                "Análisis de Energía",
                "El máximo valor a graficar no puede ser negativo.",
            )
            return False
        if resol < 2:
            resol = 2
            self.view.resol.set("2")
        if levels < 1:
            levels = 1
            self.view.levels.set("1")
        if rock_dens <= 0:
            self.view.error(
                "Análisis de Energía", "La densidad de la roca debe ser mayor a cero."
            )
            return False
        if expl_dens <= 0:
            self.view.error(
                "Análisis de Energía",
                "La densidad del explosivo debe ser mayor a cero.",
            )
            return False
        if diameter <= 0:
            self.view.error(
                "Análisis de Energía", "El diámetro de carga debe ser mayor a cero."
            )
            return False

        # Guardar exactamente como en la clase original
        self.params.update(
            {
                "xmin": xmin,
                "xmax": xmax,
                "ymin": ymin,
                "ymax": ymax,
                "zmin": zmin,
                "zmax": zmax,
                "cutoff": cutoff,
                "resol": resol,
                "levels": levels,
                "diameter": diameter,
                "expl_dens": expl_dens,
                "rock_dens": rock_dens,
            }
        )
        return True

    def plot_energy(self):
        """Genera la distribución de energía (2D o 3D según check), igual que tu clase."""
        if self.view.tridimensional.get():
            self.plot_energy3D()
            return

        if not self.valid_params():
            return

        p = self.params
        xmin, xmax = p["xmin"], p["xmax"]
        ymin, ymax = p["ymin"], p["ymax"]
        zmin, zmax = p["zmin"], p["zmax"]
        cutoff = p["cutoff"]
        resol = p["resol"]
        levels = p["levels"]
        diameter = p["diameter"]
        expl_dens = p["expl_dens"]
        rock_dens = p["rock_dens"]

        collars = p.get("charges_collar", [])
        toes = p.get("charges_toe", [])
        stope_geom = p.get("stope_geom")
        drift_geom = p.get("drift_geom")

        section = self.view.section.get()
        kind = self.view.type.get()

        x = np.linspace(xmin, xmax, resol)
        y = np.linspace(ymin, ymax, resol)
        z = np.linspace(zmin, zmax, resol)

        if section == "Transversal":
            xx, yy = np.meshgrid(x, y)
            E = self.model.kleine(
                xx.ravel(), yy.ravel(), zmin, collars, toes, diameter, expl_dens
            )
            E = np.reshape(E, xx.shape)
            xlabel, ylabel = "Coordenada x [m]", "Coordenada y [m]"
            title = f"Distribución de Energía\nPlano z = {zmin} m"
            Xplot, Yplot = x, y

        elif section == "Longitudinal":
            zz, yy = np.meshgrid(z, y)
            E = self.model.kleine(
                xmin, yy.ravel(), zz.ravel(), collars, toes, diameter, expl_dens
            )
            E = np.reshape(E, zz.shape)
            xlabel, ylabel = "Coordenada z [m]", "Coordenada y [m]"
            title = f"Distribución de Energía\nPlano x = {xmin} m"
            Xplot, Yplot = z, y

        else:  # Planta
            xx, zz = np.meshgrid(x, z)
            E = self.model.kleine(
                xx.ravel(), ymin, zz.ravel(), collars, toes, diameter, expl_dens
            )
            E = np.reshape(E, xx.shape)
            xlabel, ylabel = "Coordenada x [m]", "Coordenada z [m]"
            title = f"Distribución de Energía\nPlano y = {ymin} m"
            Xplot, Yplot = x, z

        E = np.where(E > cutoff, cutoff, E)
        if kind == "Tonelaje" and rock_dens > 0:
            E = E / rock_dens

        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        cont = plt.contourf(Xplot, Yplot, E, levels, cmap="gnuplot2")

        if section == "Transversal" and stope_geom:
            plt.plot(*shp.Polygon(stope_geom).exterior.xy, c="lime", lw=1)
            for c, t in zip(collars, toes):
                line = shp.LineString([(c[0], c[1]), (t[0], t[1])])
                plt.plot(*line.xy, c="red")

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        cbar = plt.colorbar(cont)
        cbar.ax.set_title(self.view.units_cutoff.cget("text"), loc="left")
        plt.show(block=False)

    def plot_energy3D(self):
        """Genera la distribución de energía 3D (igual que tu clase)."""
        if not _HAS_PLOTLY:
            self.view.error(
                "Análisis de Energía", "Plotly no está instalado para la vista 3D."
            )
            return

        if not self.valid_params():
            return

        p = self.params
        xmin, xmax = p["xmin"], p["xmax"]
        ymin, ymax = p["ymin"], p["ymax"]
        zmin, zmax = p["zmin"], p["zmax"]
        cutoff = p["cutoff"]
        resol = p["resol"]

        diameter = p["diameter"]
        expl_dens = p["expl_dens"]
        rock_dens = p["rock_dens"]
        kind = self.view.type.get()

        collars = p.get("charges_collar", [])
        toes = p.get("charges_toe", [])

        x = np.linspace(xmin, xmax, resol)
        y = np.linspace(ymin, ymax, resol)
        z = np.linspace(zmin, zmax, resol)

        xx, yy, zz = np.meshgrid(x, y, z)
        X = xx.flatten()
        Y = yy.flatten()
        Z = zz.flatten()

        energy = self.model.kleine(X, Y, Z, collars, toes, diameter, expl_dens)
        if kind == "Tonelaje" and rock_dens > 0:
            energy = energy / rock_dens

        fig = go.Figure()
        for c, t in zip(collars, toes):
            fig.add_trace(
                go.Scatter3d(
                    x=[c[0], t[0]],
                    y=[c[1], t[1]],
                    z=[c[2], t[2]],
                    mode="lines",
                    line=dict(color="red", width=2),
                    showlegend=False,
                )
            )
        fig.add_trace(
            go.Isosurface(
                x=X,
                y=Y,
                z=Z,
                value=energy,
                colorscale="jet",
                isomin=cutoff,
                isomax=float(np.max(energy)) if energy.size else cutoff,
            )
        )
        fig.update_layout(
            title="Distribución de energía explosiva",
            scene=dict(
                xaxis_title="X", yaxis_title="Y", zaxis_title="Z", aspectmode="data"
            ),
        )
        fig.show()
