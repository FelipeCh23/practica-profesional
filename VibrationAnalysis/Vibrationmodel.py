
import numpy as np
import pandas as pd

class VibrationModel:
    """
    Modelo principal para análisis de vibraciones.
    Encargado de realizar cálculos de amplitud, frecuencia, desplazamiento,
    aceleración y almacenar resultados.
    """

    def __init__(self):
        self.results = {}

    def calculate_amplitude(self, signal):
        """
        Calcula la amplitud máxima de una señal de vibración.
        
        Parámetros:
            signal (array-like): señal de vibración
            
        Retorna:
            float: amplitud máxima
        """
        try:
            amplitude = float(np.max(np.abs(signal)))
            self.results["amplitude"] = amplitude
            return amplitude
        except Exception as e:
            raise ValueError(f"Error en cálculo de amplitud: {e}")

    def calculate_rms(self, signal):
        """
        Calcula el valor RMS (Root Mean Square) de una señal.
        
        Parámetros:
            signal (array-like): señal de vibración
            
        Retorna:
            float: RMS de la señal
        """
        try:
            rms = float(np.sqrt(np.mean(np.square(signal))))
            self.results["rms"] = rms
            return rms
        except Exception as e:
            raise ValueError(f"Error en cálculo RMS: {e}")

    def calculate_frequency_spectrum(self, signal, sampling_rate):
        """
        Calcula el espectro de frecuencias de la señal mediante FFT.
        
        Parámetros:
            signal (array-like): señal de vibración
            sampling_rate (float): frecuencia de muestreo en Hz
            
        Retorna:
            tuple: (frecuencias, amplitudes)
        """
        try:
            n = len(signal)
            fft_vals = np.fft.fft(signal)
            fft_freq = np.fft.fftfreq(n, 1/sampling_rate)
            amplitudes = 2.0 / n * np.abs(fft_vals[:n // 2])
            frequencies = fft_freq[:n // 2]
            self.results["frequency_spectrum"] = (frequencies, amplitudes)
            return frequencies, amplitudes
        except Exception as e:
            raise ValueError(f"Error en cálculo de espectro de frecuencia: {e}")

    def load_data(self, filepath):
        """
        Carga datos de vibración desde un archivo CSV utilizando pandas.

        Parámetros:
            filepath (str): ruta al archivo CSV

        Retorna:
            DataFrame: datos cargados
        """
        try:
            data = pd.read_csv(filepath)
            self.results["data"] = data
            return data
        except Exception as e:
            raise Exception(f"Error al cargar datos: {e}")

    def get_results(self):
        """
        Devuelve los resultados calculados y/o cargados.

        Retorna:
            dict: resultados almacenados
        """
        return self.results



# Clases auxiliares (utilidades de vibración)


class VibrationSignal:
    """
    Clase que encapsula una señal de vibración y permite operaciones básicas.
    """

    def __init__(self, signal, sampling_rate):
        self.signal = np.array(signal)
        self.sampling_rate = sampling_rate

    def normalize(self):
        """Normaliza la señal entre -1 y 1."""
        max_val = np.max(np.abs(self.signal))
        if max_val == 0:
            return self.signal
        return self.signal / max_val

    def offset(self, value):
        """Desplaza la señal por un valor constante."""
        return self.signal + value
