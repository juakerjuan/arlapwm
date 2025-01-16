import tkinter as tk
from tkinter import ttk
import logging
from config_manager import ConfigManager
from arduino_manager import ArduinoManager
from PIL import Image, ImageTk
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('CNCControl')

class CNCControlDialog:
    def __init__(self, parent, arduino_manager=None):
        logger.debug("Iniciando CNCControlDialog")
        
        self.arduino_manager = arduino_manager if arduino_manager else ArduinoManager()
        logger.debug(f"Usando ArduinoManager existente: {self.arduino_manager.is_connected()}")
        
        # Cargar configuración
        self.config_manager = ConfigManager()
        self.load_config()
        
        # Crear la ventana
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Control CNC")
        self.dialog.geometry("400x500")
        self.dialog.configure(bg='#1e1e1e')
        self.dialog.resizable(False, False)
        
        # Hacer la ventana modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar la ventana
        self.center_window(parent)
        
        # Crear interfaz
        self.create_widgets()
        
        # Configurar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_config(self):
        """Cargar configuración desde config_manager"""
        machine_config = self.config_manager.get_machine_config()
        
        # Obtener pasos por mm
        self.steps_per_mm_x = float(machine_config.get('steps_x', 100))
        self.steps_per_mm_y = float(machine_config.get('steps_y', 100))
        
        # Obtener pines usando las claves correctas
        self.pin_step_x = machine_config.get('x_step')
        self.pin_dir_x = machine_config.get('x_dir')
        self.pin_step_y = machine_config.get('y_step')
        self.pin_dir_y = machine_config.get('y_dir')
        self.pin_home_x = machine_config.get('x_home')
        self.pin_home_y = machine_config.get('y_home')
        
        logger.debug(f"Configuración cargada: steps_x={self.steps_per_mm_x}, steps_y={self.steps_per_mm_y}")
    
    def create_widgets(self):
        """Crear widgets de la interfaz"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title = ttk.Label(main_frame,
                         text="Control de Movimiento CNC",
                         font=('Arial', 12, 'bold'),
                         foreground='white',
                         background='#1e1e1e')
        title.pack(pady=(0,20))
        
        # Frame para entrada de distancia
        distance_frame = ttk.Frame(main_frame)
        distance_frame.pack(fill='x', pady=10)
        
        ttk.Label(distance_frame,
                 text="Distancia (mm):",
                 foreground='white',
                 background='#1e1e1e').pack(side='left', padx=5)
        
        self.distance_entry = ttk.Entry(distance_frame, width=10)
        self.distance_entry.insert(0, "10")
        self.distance_entry.pack(side='left', padx=5)
        
        # Frame para botones de control
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=20)
        
        # Cargar y crear botones con iconos
        self.create_control_buttons(control_frame)
        
        # Botón de Home
        home_button = ttk.Button(main_frame,
                               text="Home",
                               command=self.home)
        home_button.pack(pady=10)
    
    def create_control_buttons(self, parent):
        """Crear botones de control con iconos"""
        # Aquí irían los botones con iconos para X+, X-, Y+, Y-
        # Por ahora usaremos botones de texto
        button_frame = ttk.Frame(parent)
        button_frame.pack()
        
        # Botón Y+
        ttk.Button(button_frame,
                  text="Y+",
                  command=lambda: self.move('y', 1)).pack(pady=5)
        
        # Botones X- X+
        x_frame = ttk.Frame(button_frame)
        x_frame.pack()
        ttk.Button(x_frame,
                  text="X-",
                  command=lambda: self.move('x', -1)).pack(side='left', padx=5)
        ttk.Button(x_frame,
                  text="X+",
                  command=lambda: self.move('x', 1)).pack(side='left', padx=5)
        
        # Botón Y-
        ttk.Button(button_frame,
                  text="Y-",
                  command=lambda: self.move('y', -1)).pack(pady=5)
    
    def move(self, axis, direction):
        """Mover eje en la dirección especificada"""
        try:
            distance = float(self.distance_entry.get())
            logger.debug(f"Moviendo {axis} {direction * distance}mm")
            
            if self.arduino_manager.move_mm(axis, direction * distance):
                logger.debug("Movimiento completado")
            else:
                logger.error("Error en movimiento")
                
        except ValueError:
            logger.error("Distancia inválida")
    
    def home(self):
        """Ir a posición home"""
        logger.debug("Iniciando secuencia de home")
        
        # Home en Y primero
        self.arduino_manager.home_axis('y')
        # Home en X después
        self.arduino_manager.home_axis('x')
    
    def center_window(self, parent):
        """Centrar ventana respecto al padre"""
        self.dialog.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        logger.debug("Cerrando ventana de control CNC")
        self.dialog.grab_release()
        self.dialog.destroy() 