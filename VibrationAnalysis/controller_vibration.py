# controller_vibration.py
<<<<<<< HEAD
import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as shp

=======
import numpy as np
import shapely.geometry as shp
import matplotlib.pyplot as plt
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

class VibrationAnalysisController:
    """Conecta Vista y Modelo. Hace update_values y plot, como en la clase original."""

    def __init__(self, model, view):
        self.model = model
<<<<<<< HEAD
        self.view = view
=======
        self.view  = view
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

        # Poblar combos y conectar eventos desde el controlador
        patterns = [""] + self.model.get_patterns()
        self.view.combo_charges.configure(values=patterns)
<<<<<<< HEAD
        self.view.combo_section.configure(
            values=["Transversal", "Longitudinal", "Planta"]
        )
=======
        self.view.combo_section.configure(values=['Transversal', 'Longitudinal', 'Planta'])
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

        # Conectar cambios:
        self.view.combo_charges.configure(command=self.update_values)
        self.view.combo_section.configure(command=self.update_values)
        self.view.button_plot.configure(command=self.plot_distribution)

    def update_values(self, event=None):
        """Replica la lógica de update_values del original, pero usando Model para datos."""
        pattern_name = self.view.pattern.get()
<<<<<<< HEAD
        if pattern_name == "":
=======
        if pattern_name == '':
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
            return

        data = self.model.geometry_for_pattern(pattern_name)
        xmin, ymin, xmax, ymax = self.model.stope_bounds(data["stope_geom"])

<<<<<<< HEAD
        xmid = round(0.5 * (xmin + xmax), 1)
        ymid = round(0.5 * (ymin + ymax), 1)
        zmid = 0.0

        self.view.xmin.set(round(1.1 * xmin - 0.1 * xmax, 1))
        self.view.xmax.set(round(1.1 * xmax - 0.1 * xmin, 1))
        self.view.ymin.set(round(1.1 * ymin - 0.1 * ymax, 1))
        self.view.ymax.set(round(1.1 * ymax - 0.1 * ymin, 1))
        self.view.zmin.set(round(-10 * data["holes_burden"], 1))
        self.view.zmax.set(round(+10 * data["holes_burden"], 1))

        self.view.entry_xmax.configure(state="normal")
        self.view.entry_ymax.configure(state="normal")
        self.view.entry_zmax.configure(state="normal")

        sec = self.view.section.get()
        if sec == "Transversal":
            self.view.zmin.set(zmid)
            self.view.zmax.set(zmid)
            self.view.entry_zmax.configure(state="disabled")
        elif sec == "Longitudinal":
            self.view.xmin.set(xmid)
            self.view.xmax.set(xmid)
            self.view.entry_xmax.configure(state="disabled")
        elif sec == "Planta":
            self.view.ymin.set(ymid)
            self.view.ymax.set(ymid)
            self.view.entry_ymax.configure(state="disabled")
=======
        xmid = round(0.5*(xmin + xmax), 1)
        ymid = round(0.5*(ymin + ymax), 1)
        zmid = 0.0

        self.view.xmin.set(round(1.1*xmin - 0.1*xmax, 1))
        self.view.xmax.set(round(1.1*xmax - 0.1*xmin, 1))
        self.view.ymin.set(round(1.1*ymin - 0.1*ymax, 1))
        self.view.ymax.set(round(1.1*ymax - 0.1*ymin, 1))
        self.view.zmin.set(round(-10*data["holes_burden"], 1))
        self.view.zmax.set(round(+10*data["holes_burden"], 1))

        self.view.entry_xmax.configure(state='normal')
        self.view.entry_ymax.configure(state='normal')
        self.view.entry_zmax.configure(state='normal')

        sec = self.view.section.get()
        if sec == 'Transversal':
            self.view.zmin.set(zmid); self.view.zmax.set(zmid)
            self.view.entry_zmax.configure(state='disabled')
        elif sec == 'Longitudinal':
            self.view.xmin.set(xmid); self.view.xmax.set(xmid)
            self.view.entry_xmax.configure(state='disabled')
        elif sec == 'Planta':
            self.view.ymin.set(ymid); self.view.ymax.set(ymid)
            self.view.entry_ymax.configure(state='disabled')
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

        # Parámetros de evaluación (se copian desde los datos)
        self.view.diameter.set(str(data["diameter"]))
        self.view.density.set(str(data["expl_density"]))

        # Guardar geometrías como hace la clase original
<<<<<<< HEAD
        self.view.params.update(
            {
                "charges_collar": data["charges_collar"],
                "charges_toe": data["charges_toe"],
                "drift_geom": data["drift_geom"],
                "stope_geom": data["stope_geom"],
            }
        )
=======
        self.view.params.update({
            'charges_collar': data["charges_collar"],
            'charges_toe':    data["charges_toe"],
            'drift_geom':     data["drift_geom"],
            'stope_geom':     data["stope_geom"],
        })
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

    def plot_distribution(self):
        """Replica plot_distribution del original, ejecutando la fórmula del Model y graficando."""
        if not self.view.valid_params():
            return

        p = self.view.params
<<<<<<< HEAD
        xmin, xmax = p["xmin"], p["xmax"]
        ymin, ymax = p["ymin"], p["ymax"]
        zmin, zmax = p["zmin"], p["zmax"]
        cutoff = p["cutoff"]
        resol = p["resol"]
        levels = p["levels"]

        diameter = p["diameter"]
        density = p["density"]
        const_K = p["const_K"]
        const_a = p["const_a"]

        charges_collar = self.view.params["charges_collar"]
        charges_toe = self.view.params["charges_toe"]
        stope_geom = self.view.params["stope_geom"]
        drift_geom = self.view.params["drift_geom"]
=======
        xmin, xmax = p['xmin'], p['xmax']
        ymin, ymax = p['ymin'], p['ymax']
        zmin, zmax = p['zmin'], p['zmax']
        cutoff     = p['cutoff']
        resol      = p['resol']
        levels     = p['levels']

        diameter   = p['diameter']
        density    = p['density']
        const_K    = p['const_K']
        const_a    = p['const_a']

        charges_collar = self.view.params['charges_collar']
        charges_toe    = self.view.params['charges_toe']
        stope_geom     = self.view.params['stope_geom']
        drift_geom     = self.view.params['drift_geom']
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

        x = np.linspace(xmin, xmax, resol)
        y = np.linspace(ymin, ymax, resol)
        z = np.linspace(zmin, zmax, resol)

        sec = self.view.section.get()
<<<<<<< HEAD
        if sec == "Transversal":
            xx, yy = np.meshgrid(x, y)
            total_vibration = self.model.holmberg_persson(
                xx.ravel(),
                yy.ravel(),
                zmin,
                charges_collar,
                charges_toe,
                diameter,
                density,
                const_K,
                const_a,
            ).reshape(xx.shape)
            xlabel, ylabel = "Coordenada x [m]", "Coordenada y [m]"
            title = f"Distribución de Vibraciones\nPlano z = {zmin} m"
            X, Y = x, y
        elif sec == "Longitudinal":
            zz, yy = np.meshgrid(z, y)
            total_vibration = self.model.holmberg_persson(
                xmin,
                yy.ravel(),
                zz.ravel(),
                charges_collar,
                charges_toe,
                diameter,
                density,
                const_K,
                const_a,
            ).reshape(zz.shape)
            xlabel, ylabel = "Coordenada z [m]", "Coordenada y [m]"
            title = f"Distribución de Vibraciones\nPlano x = {xmin} m"
=======
        if sec == 'Transversal':
            xx, yy = np.meshgrid(x, y)
            total_vibration = self.model.holmberg_persson(
                xx.ravel(), yy.ravel(), zmin,
                charges_collar, charges_toe, diameter, density, const_K, const_a
            ).reshape(xx.shape)
            xlabel, ylabel = 'Coordenada x [m]', 'Coordenada y [m]'
            title = f'Distribución de Vibraciones\nPlano z = {zmin} m'
            X, Y = x, y
        elif sec == 'Longitudinal':
            zz, yy = np.meshgrid(z, y)
            total_vibration = self.model.holmberg_persson(
                xmin, yy.ravel(), zz.ravel(),
                charges_collar, charges_toe, diameter, density, const_K, const_a
            ).reshape(zz.shape)
            xlabel, ylabel = 'Coordenada z [m]', 'Coordenada y [m]'
            title = f'Distribución de Vibraciones\nPlano x = {xmin} m'
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
            X, Y = z, y
        else:  # Planta
            xx, zz = np.meshgrid(x, z)
            total_vibration = self.model.holmberg_persson(
<<<<<<< HEAD
                xx.ravel(),
                ymin,
                zz.ravel(),
                charges_collar,
                charges_toe,
                diameter,
                density,
                const_K,
                const_a,
            ).reshape(xx.shape)
            xlabel, ylabel = "Coordenada x [m]", "Coordenada z [m]"
            title = f"Distribución de Vibraciones\nPlano y = {ymin} m"
=======
                xx.ravel(), ymin, zz.ravel(),
                charges_collar, charges_toe, diameter, density, const_K, const_a
            ).reshape(xx.shape)
            xlabel, ylabel = 'Coordenada x [m]', 'Coordenada z [m]'
            title = f'Distribución de Vibraciones\nPlano y = {ymin} m'
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
            X, Y = x, z

        total_vibration = np.where(total_vibration > cutoff, cutoff, total_vibration)

        fig, ax = plt.subplots()
<<<<<<< HEAD
        ax.set_aspect("equal")

        cont = plt.contourf(X, Y, total_vibration, levels, cmap="viridis")
=======
        ax.set_aspect('equal')

        cont = plt.contourf(X, Y, total_vibration, levels, cmap='viridis')
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        # Contorno del caserón y cargas (igual que el original)
<<<<<<< HEAD
        plt.plot(*shp.Polygon(stope_geom).exterior.xy, c="lime", lw=1)
        for collar, toe in zip(charges_collar, charges_toe):
            line = shp.LineString([collar, toe])
            plt.plot(*line.xy, c="red")

        cbar = plt.colorbar(cont)
        cbar.ax.set_title("mm/s", loc="left")
=======
        plt.plot(*shp.Polygon(stope_geom).exterior.xy, c='lime', lw=1)
        for collar, toe in zip(charges_collar, charges_toe):
            line = shp.LineString([collar, toe])
            plt.plot(*line.xy, c='red')

        cbar = plt.colorbar(cont)
        cbar.ax.set_title('mm/s', loc='left')
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        plt.show(block=False)
