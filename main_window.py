import tkinter as tk
from tkinter import ttk
from config_manager import ConfigManager
from arduino_connection import ArduinoConnectionDialog, ArduinoManager
from laser_control import LaserControlDialog
from cnc_control import CNCControlDialog
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('MainWindow')

class WorkArea(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, bg='#1e1e1e')
        self.config_manager = ConfigManager()
        
        # Obtener dimensiones de la máquina
        dimensions = self.config_manager.get_machine_dimensions()
        self.width_mm = dimensions['width']
        self.height_mm = dimensions['length']
        
        # Factor de zoom inicial (píxeles por mm)
        self.zoom = 2
        
        # Configurar eventos
        self.bind('<MouseWheel>', self.on_mousewheel)
        self.bind('<Configure>', self.on_resize)
        
        # Dibujar elementos
        self.draw_all()
    
    def draw_all(self):
        self.delete('all')  # Limpiar canvas
        self.draw_grid()
        self.draw_rulers()
    
    def draw_grid(self):
        # Dibujar cuadrícula
        for x in range(0, int(self.width_mm) + 1, 10):
            x_pos = x * self.zoom
            # Línea vertical
            self.create_line(x_pos, 0, x_pos, self.height_mm * self.zoom, 
                           fill='#333333', tags='grid')
        
        for y in range(0, int(self.height_mm) + 1, 10):
            y_pos = y * self.zoom
            # Línea horizontal
            self.create_line(0, y_pos, self.width_mm * self.zoom, y_pos, 
                           fill='#333333', tags='grid')
    
    def draw_rulers(self):
        # Dibujar reglas
        ruler_width = 20
        
        # Regla horizontal (X)
        for x in range(0, int(self.width_mm) + 1, 10):
            x_pos = x * self.zoom
            self.create_line(x_pos, 0, x_pos, ruler_width, 
                           fill='white', tags='ruler')
            self.create_text(x_pos, ruler_width/2, 
                           text=str(x), fill='white', 
                           tags='ruler')
        
        # Regla vertical (Y)
        for y in range(0, int(self.height_mm) + 1, 10):
            y_pos = y * self.zoom
            self.create_line(0, y_pos, ruler_width, y_pos, 
                           fill='white', tags='ruler')
            self.create_text(ruler_width/2, y_pos, 
                           text=str(y), fill='white', 
                           tags='ruler')
    
    def on_mousewheel(self, event):
        # Zoom con la rueda del ratón
        old_zoom = self.zoom
        if event.delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom /= 1.1
        
        # Limitar zoom
        self.zoom = max(0.5, min(10, self.zoom))
        
        if old_zoom != self.zoom:
            self.draw_all()
    
    def on_resize(self, event):
        self.draw_all()

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ARLA PWM")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # Crear panel principal
        self.main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_panel.pack(fill=tk.BOTH, expand=True)
        
        # Área de trabajo (izquierda)
        self.work_area = WorkArea(self.main_panel)
        self.main_panel.add(self.work_area, weight=2)
        
        # Panel de control (derecha)
        self.control_panel = ttk.Frame(self.main_panel)
        self.main_panel.add(self.control_panel, weight=1)
        
        # Inicializar Arduino Manager
        self.arduino_manager = ArduinoManager()
        
        # Modificar el botón de conexión
        self.connect_button = ttk.Button(self.control_panel, 
                                       text="Conectar Arduino",
                                       command=self.show_connection_dialog)
        self.connect_button.pack(pady=10)
        
        # Botón de control láser (inicialmente deshabilitado)
        self.laser_control_button = ttk.Button(self.control_panel, 
                                             text="Control Láser",
                                             command=self.show_laser_control,
                                             state='disabled')
        self.laser_control_button.pack(pady=10)
        
        # Botón de control CNC (inicialmente deshabilitado)
        self.cnc_control_button = ttk.Button(self.control_panel, 
                                           text="Control CNC",
                                           command=self.show_cnc_control,
                                           state='disabled')
        self.cnc_control_button.pack(pady=10)
    
    def show_connection_dialog(self):
        if not self.arduino_manager.is_connected():
            dialog = ArduinoConnectionDialog(self.root)
            self.root.wait_window(dialog.dialog)
            
            if self.arduino_manager.board:
                self.connect_button.configure(text="Conectado", state='disabled')
                # Habilitar botones de control
                self.laser_control_button.configure(state='normal')
                self.cnc_control_button.configure(state='normal')
    
    def show_laser_control(self):
        logger.debug("Mostrando control láser")
        # Pasar la instancia existente del ArduinoManager
        dialog = LaserControlDialog(self.root, self.arduino_manager)
        dialog.dialog.protocol("WM_DELETE_WINDOW", dialog.on_closing)
    
    def show_cnc_control(self):
        logger.debug("Mostrando control CNC")
        dialog = CNCControlDialog(self.root, self.arduino_manager)
    
    def run(self):
        self.root.mainloop() 