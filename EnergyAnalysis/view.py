"""
Analisis hasta linea 1952 (revisar)
- La UI principal (Tkinter)
- La carga de datos y cálculo de energía (vía EnergyModel)
- Las grillas (CanvasGrid) para visualización
- Los colores (CTkColor) que se usan para la UI o análisis
- El StopeDesigner para mostrar volumen de cámaras si aplica  """

import tkinter as tk
from tkinter import filedialog, messagebox
from model import EnergyModel, CanvasGrid, CTkColor, StopeDesigner


class EnergyView(tk.Tk):
    """
    Vista extendida de la aplicación de análisis de energía.
    Maneja la interacción con el usuario, carga de datos, cálculos y visualización.
    """

    def __init__(self):
        super().__init__()
        self.title("Energy Analysis")
        self.geometry("800x600")

        # Modelo principal
        self.model = EnergyModel()

        # Widgets principales
        self.create_widgets()

        # Grilla de ejemplo
        self.canvas_grid = CanvasGrid(width=600, height=400, spacing=50)

        # Color por defecto
        self.default_color = CTkColor(50, 150, 250)

    def create_widgets(self):
        """Crea y ubica todos los widgets de la vista."""

        # Botón para cargar CSV
        self.load_button = tk.Button(self, text="Cargar CSV", command=self.load_data)
        self.load_button.pack(pady=10)

        # Parámetros para cálculo
        self.param1_label = tk.Label(self, text="Parámetro 1:")
        self.param1_label.pack()
        self.param1_entry = tk.Entry(self)
        self.param1_entry.pack()

        self.param2_label = tk.Label(self, text="Parámetro 2:")
        self.param2_label.pack()
        self.param2_entry = tk.Entry(self)
        self.param2_entry.pack()

        # Botón para calcular energía
        self.calculate_button = tk.Button(self, text="Calcular Energía", command=self.calculate_energy)
        self.calculate_button.pack(pady=10)

        # Botón para calcular volumen de stope
        self.volume_button = tk.Button(self, text="Calcular Volumen Cámara", command=self.calculate_stope_volume)
        self.volume_button.pack(pady=5)

        # Área de resultados
        self.result_text = tk.Text(self, height=15, width=80)
        self.result_text.pack(pady=10)

    def load_data(self):
        """Carga CSV mediante dialog y lo guarda en el modelo."""
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            try:
                data = self.model.load_data(filepath)
                messagebox.showinfo("Éxito", f"Datos cargados correctamente. {len(data)} filas.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def calculate_energy(self):
        """Calcula energía usando los parámetros de entrada y el modelo."""
        try:
            param1 = float(self.param1_entry.get())
            param2 = float(self.param2_entry.get())
            energy = self.model.calculate_energy(param1, param2)
            self.show_results(f"Energía calculada: {energy}")
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))

    def calculate_stope_volume(self):
        """Calcula el volumen de una cámara de explotación."""
        try:
            width = float(self.param1_entry.get())
            height = float(self.param2_entry.get())
            depth = 10  # valor de ejemplo; se podría agregar otra entrada
            stope = StopeDesigner(width, height, depth)
            volume = stope.calculate_volume()
            self.show_results(f"Volumen de la cámara: {volume}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_results(self, text):
        """Muestra los resultados en el área de texto."""
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)

    def draw_grid(self):
        """Dibuja la grilla en un canvas (opcional)."""
        # Aquí se podría agregar un Canvas Tkinter y dibujar las líneas de CanvasGrid
        pass

    def set_color(self, r, g, b):
        """Actualiza el color de visualización."""
        self.default_color = CTkColor(r, g, b)


if __name__ == "__main__":
    app = EnergyView()
    app.mainloop()
