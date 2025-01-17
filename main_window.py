import tkinter as tk
from tkinter import ttk
from config_manager import ConfigManager
from arduino_connection import ArduinoConnectionDialog, ArduinoManager
from laser_control import LaserControlDialog
from cnc_control import CNCControlDialog
from calibration_control import CalibrationDialog
from svg_import_window import SVGImportWindow
import logging
import tkinter.messagebox as messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
from pcb_processor import PCBProcessor

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('MainWindow')

class WorkArea(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, bg='#1e1e1e')
        self.config_manager = ConfigManager()
        
        # Variables para PCB
        self.pcb_image = None
        self.pcb_dims = None
        self.pcb_position = {'x': 0, 'y': 0}  # Posición en mm
        self.pcb_rotation = 0  # Rotación en grados
        self.pcb_selected = False
        
        # Obtener dimensiones de la máquina
        dimensions = self.config_manager.get_machine_dimensions()
        self.width_mm = dimensions['width']
        self.height_mm = dimensions['length']
        
        # Factor de zoom inicial (píxeles por mm)
        self.zoom = 2
        
        # Configurar eventos
        self.bind('<MouseWheel>', self.on_mousewheel)
        self.bind('<Configure>', self.on_resize)
        self.bind('<Button-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Button-3>', self.on_right_click)  # Para rotar
        
        # Dibujar elementos
        self.draw_all()
    
    def draw_all(self):
        """Redibujar todo el área de trabajo"""
        self.delete('all')
        self.draw_grid()
        
        # Dibujar PCB si existe
        if self.pcb_image and self.pcb_dims:
            self.draw_pcb()
            
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
    
    def show_pcb(self, image, dimensions):
        """Mostrar PCB en el área de trabajo"""
        self.pcb_image = image
        self.pcb_dims = dimensions
        
        # Centrar PCB inicialmente
        self.pcb_position = {
            'x': (self.width_mm - dimensions['width']) / 2,
            'y': (self.height_mm - dimensions['height']) / 2
        }
        
        self.draw_all()
    
    def draw_pcb(self):
        """Dibujar PCB con transformaciones"""
        if not self.pcb_image:
            return
            
        try:
            # Crear copia de la imagen para transformar
            img = self.pcb_image.copy()
            
            # Rotar imagen si es necesario
            if self.pcb_rotation != 0:
                img = img.rotate(self.pcb_rotation, expand=True)
            
            # Escalar imagen según zoom
            new_width = int(self.pcb_dims['width'] * self.zoom)
            new_height = int(self.pcb_dims['height'] * self.zoom)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convertir a PhotoImage
            self.pcb_photo = ImageTk.PhotoImage(img)
            
            # Calcular posición en pixels
            x = self.pcb_position['x'] * self.zoom
            y = self.pcb_position['y'] * self.zoom
            
            # Dibujar imagen
            self.create_image(x, y, 
                            image=self.pcb_photo, 
                            anchor='nw',
                            tags='pcb')
            
            # Dibujar borde si está seleccionado
            if self.pcb_selected:
                self.create_rectangle(x, y,
                                   x + new_width,
                                   y + new_height,
                                   outline='#00ff00',
                                   width=2,
                                   tags='pcb_border')
                
        except Exception as e:
            logger.error(f"Error dibujando PCB: {e}")
    
    def on_click(self, event):
        """Manejar click del mouse"""
        # Convertir coordenadas a mm
        x_mm = event.x / self.zoom
        y_mm = event.y / self.zoom
        
        # Verificar si el click fue sobre el PCB
        if self.pcb_image:
            pcb_x = self.pcb_position['x']
            pcb_y = self.pcb_position['y']
            
            if (pcb_x <= x_mm <= pcb_x + self.pcb_dims['width'] and
                pcb_y <= y_mm <= pcb_y + self.pcb_dims['height']):
                self.pcb_selected = True
                self.last_x = event.x
                self.last_y = event.y
            else:
                self.pcb_selected = False
            
            self.draw_all()
    
    def on_drag(self, event):
        """Manejar arrastre del PCB"""
        if self.pcb_selected:
            # Calcular diferencia en mm
            dx = (event.x - self.last_x) / self.zoom
            dy = (event.y - self.last_y) / self.zoom
            
            # Actualizar posición
            self.pcb_position['x'] += dx
            self.pcb_position['y'] += dy
            
            # Actualizar última posición
            self.last_x = event.x
            self.last_y = event.y
            
            self.draw_all()
    
    def on_release(self, event):
        """Manejar liberación del mouse"""
        self.pcb_selected = False
        self.draw_all()
    
    def on_right_click(self, event):
        """Rotar PCB 90 grados"""
        if self.pcb_selected:
            self.pcb_rotation = (self.pcb_rotation + 90) % 360
            
            # Intercambiar dimensiones si es necesario
            if self.pcb_rotation in [90, 270]:
                self.pcb_dims['width'], self.pcb_dims['height'] = \
                    self.pcb_dims['height'], self.pcb_dims['width']
            
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
        self.pcb_processor = PCBProcessor()
        
        # Botones en el panel de control
        self.connect_button = ttk.Button(self.control_panel, 
                                       text="Conectar Arduino",
                                       command=self.show_connection_dialog)
        self.connect_button.pack(pady=10)
        
        self.laser_control_button = ttk.Button(self.control_panel, 
                                             text="Control Láser",
                                             command=self.show_laser_control,
                                             state='disabled')
        self.laser_control_button.pack(pady=10)
        
        self.cnc_control_button = ttk.Button(self.control_panel, 
                                           text="Control CNC",
                                           command=self.show_cnc_control,
                                           state='disabled')
        self.cnc_control_button.pack(pady=10)
        
        self.calibration_button = ttk.Button(self.control_panel,
                                           text="Calibración",
                                           command=self.show_calibration,
                                           state='disabled')
        self.calibration_button.pack(pady=10)
        
        # Botón para cargar PCB
        self.pcb_button = ttk.Button(self.control_panel,
                                   text="Cargar PCB",
                                   command=self.load_pcb,
                                   style='Dark.TButton')
        self.pcb_button.pack(pady=5)
    
    def show_connection_dialog(self):
        if not self.arduino_manager.is_connected():
            dialog = ArduinoConnectionDialog(self.root)
            self.root.wait_window(dialog.dialog)
            
            if self.arduino_manager.board:
                self.connect_button.configure(text="Conectado", state='disabled')
                # Habilitar botones de control
                self.laser_control_button.configure(state='normal')
                self.cnc_control_button.configure(state='normal')
                self.calibration_button.configure(state='normal')
    
    def show_laser_control(self):
        logger.debug("Mostrando control láser")
        # Pasar la instancia existente del ArduinoManager
        dialog = LaserControlDialog(self.root, self.arduino_manager)
        dialog.dialog.protocol("WM_DELETE_WINDOW", dialog.on_closing)
    
    def show_cnc_control(self):
        logger.debug("Mostrando control CNC")
        dialog = CNCControlDialog(self.root, self.arduino_manager)
    
    def show_calibration(self):
        logger.debug("Mostrando ventana de calibración")
        dialog = CalibrationDialog(self.root, self.arduino_manager)
    
    def load_pcb(self):
        """Cargar archivo de PCB"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Archivos de imagen", "*.bmp *.png"),
                ("Archivos BMP", "*.bmp"),
                ("Archivos PNG", "*.png")
            ]
        )
        
        if file_path:
            if self.pcb_processor.load_image(file_path):
                # Obtener dimensiones
                dims = self.pcb_processor.get_dimensions()
                logger.info(f"PCB cargado: {dims['width']:.2f}mm x {dims['height']:.2f}mm")
                
                # Obtener preview
                preview = self.pcb_processor.get_preview_image()
                if preview:
                    # Mostrar en el área de trabajo
                    self.work_area.show_pcb(preview, dims)
            else:
                messagebox.showerror("Error", 
                                   "Error cargando archivo de imagen")
    
    def run(self):
        self.root.mainloop() 