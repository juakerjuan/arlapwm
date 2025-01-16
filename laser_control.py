import tkinter as tk
from tkinter import ttk
import logging
from config_manager import ConfigManager
from arduino_manager import ArduinoManager

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('LaserControl')

class LaserControlDialog:
    def __init__(self, parent, arduino_manager=None):
        logger.debug("Iniciando LaserControlDialog")
        
        # Inicializar variables de estado
        self.laser_on = False
        # Usar el arduino_manager pasado o crear uno nuevo
        self.arduino_manager = arduino_manager if arduino_manager else ArduinoManager()
        logger.debug(f"Usando ArduinoManager existente: {self.arduino_manager.is_connected()}")
        
        # Verificar configuración
        config_manager = ConfigManager()
        logger.debug(f"Configuración cargada: {config_manager.config}")
        
        # Asegurar que el láser esté apagado al inicio
        if self.arduino_manager.is_connected():
            logger.debug("Apagando láser al inicio")
            success = self.arduino_manager.set_laser_power(0)
            if not success:
                logger.error("No se pudo apagar el láser al inicio")
        else:
            logger.error("No hay conexión con Arduino al iniciar LaserControl")
        
        # Crear la ventana
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Control Láser")
        self.dialog.geometry("300x400")
        self.dialog.configure(bg='#1e1e1e')
        self.dialog.resizable(False, False)
        
        # Hacer la ventana modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar la ventana respecto al padre
        self.dialog.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = 300
        height = 400
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title = ttk.Label(main_frame, 
                         text="Control de Potencia Láser",
                         font=('Arial', 12, 'bold'),
                         foreground='white',
                         background='#1e1e1e')
        title.pack(pady=(0,20))
        
        # Etiqueta de potencia
        self.power_label = ttk.Label(main_frame,
                                   text="Potencia: 0",
                                   font=('Arial', 10),
                                   foreground='white',
                                   background='#1e1e1e')
        self.power_label.pack(pady=5)
        
        # Barra de potencia (ahora del 1 al 10)
        self.power_scale = ttk.Scale(main_frame,
                                   from_=0,
                                   to=10,
                                   orient='horizontal',
                                   command=self.on_power_change)
        self.power_scale.set(0)
        self.power_scale.pack(fill='x', pady=10)
        
        # Botón de encendido/apagado
        self.laser_button = ttk.Button(main_frame,
                                     text="Probar Láser",
                                     command=self.toggle_laser)
        self.laser_button.pack(pady=20)
        
        # Advertencia
        warning = ttk.Label(main_frame,
                          text="¡PRECAUCIÓN!\nUsar protección ocular adecuada",
                          font=('Arial', 10, 'bold'),
                          foreground='red',
                          background='#1e1e1e')
        warning.pack(pady=10)
        
        # Configurar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_power_change(self, value):
        power_level = int(float(value))
        logger.debug(f"Cambio en slider: nivel {power_level}")
        self.power_label.configure(text=f"Potencia: {power_level}")
        
        # Convertir nivel 0-10 a valor PWM 0-255
        pwm_value = int((power_level / 10) * 255)
        logger.debug(f"Valor PWM calculado: {pwm_value}")
        
        # Solo actualizar potencia si el láser está encendido
        if self.laser_on:
            logger.debug(f"Actualizando potencia del láser a nivel {power_level} (PWM: {pwm_value})")
            self.arduino_manager.set_laser_power(pwm_value)
    
    def toggle_laser(self):
        self.laser_on = not self.laser_on
        logger.debug(f"Toggle láser: {'encendido' if self.laser_on else 'apagado'}")
        
        if self.laser_on:
            # Encender láser
            power_level = int(self.power_scale.get())
            pwm_value = int((power_level / 10) * 255)
            logger.debug(f"Encendiendo láser nivel {power_level} (PWM: {pwm_value})")
            self.arduino_manager.set_laser_power(pwm_value)
            self.laser_button.configure(text="Apagar Láser")
            self.power_scale.configure(state='disabled')
        else:
            # Apagar láser
            logger.debug("Apagando láser")
            self.arduino_manager.set_laser_power(0)
            self.laser_button.configure(text="Probar Láser")
            self.power_scale.configure(state='normal')
    
    def on_closing(self):
        logger.debug("Cerrando ventana de control láser")
        if self.laser_on:
            logger.debug("Apagando láser antes de cerrar")
            self.toggle_laser()
        self.dialog.grab_release()
        self.dialog.destroy() 