# practica-profesional/vibraciones/view.py

import customtkinter as ctk
from tkinter import filedialog, messagebox


class VibrationView(ctk.CTk):
    """
    Vista principal para el análisis de vibraciones.
    Encargada de mostrar la interfaz gráfica (UI) y capturar entradas del usuario.
    """

    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.title("Módulo de Análisis de Vibraciones")
        self.geometry("800x600")

        # Marco principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Etiquetas y campos de entrada
        self.param1_label = ctk.CTkLabel(self.main_frame, text="Parámetro 1 (frecuencia):")
        self.param1_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.param1_entry = ctk.CTkEntry(self.main_frame)
        self.param1_entry.grid(row=0, column=1, padx=10, pady=10)

        self.param2_label = ctk.CTkLabel(self.main_frame, text="Parámetro 2 (amplitud):")
        self.param2_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.param2_entry = ctk.CTkEntry(self.main_frame)
        self.param2_entry.grid(row=1, column=1, padx=10, pady=10)

        # Botones de acción
        self.load_button = ctk.CTkButton(self.main_frame, text="Cargar Datos")
        self.load_button.grid(row=2, column=0, padx=10, pady=10)

        self.calculate_button = ctk.CTkButton(self.main_frame, text="Calcular Vibraciones")
        self.calculate_button.grid(row=2, column=1, padx=10, pady=10)

        self.plot_button = ctk.CTkButton(self.main_frame, text="Graficar Señal")
        self.plot_button.grid(row=2, column=2, padx=10, pady=10)

        # Área de resultados
        self.results_box = ctk.CTkTextbox(self.main_frame, width=600, height=250)
        self.results_box.grid(row=3, column=0, columnspan=3, padx=10, pady=20)

    # ---------------- Métodos auxiliares ---------------- #

    def show_results(self, text: str):
        """Muestra resultados en el cuadro de texto."""
        self.results_box.insert("end", text + "\n")
        self.results_box.see("end")

    def ask_file_path(self):
        """Abre un diálogo para seleccionar archivo CSV de vibraciones."""
        return filedialog.askopenfilename(
            title="Seleccione archivo de vibraciones",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )

    def show_error(self, message: str):
        """Muestra un cuadro de error."""
        messagebox.showerror("Error", message)
