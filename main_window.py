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
import threading
import time
from material_manager import MaterialManager

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

class WorkDialog:
    def __init__(self, parent, pcb_image, pcb_position):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Trabajo en Progreso")
        
        # Hacer la ventana modal y asegurar que esté por encima
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()
        
        # Quitar marcos de la ventana
        self.dialog.overrideredirect(True)
        
        # Centrar la ventana
        window_width = 500
        window_height = 500
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.dialog.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Borde visible
        self.dialog.configure(bg='#2d2d2d',
                            highlightbackground='#3d3d3d',
                            highlightthickness=2)
        
        # Guardar referencia a la imagen y posición del PCB
        self.pcb_image = pcb_image
        self.pcb_position = pcb_position
        self.config_manager = ConfigManager()
        
        # Añadir MaterialManager
        self.material_manager = MaterialManager()
        
        # Frame para selección de material
        material_frame = tk.Frame(self.dialog, bg='#2d2d2d')
        material_frame.pack(pady=20)
        
        # Label para material
        material_label = tk.Label(material_frame,
                                text="Material:",
                                font=('Arial', 12),
                                bg='#2d2d2d',
                                fg='white')
        material_label.pack(side='left', padx=10)
        
        # Combobox para materiales
        self.material_var = tk.StringVar()
        self.material_combo = ttk.Combobox(material_frame,
                                         textvariable=self.material_var,
                                         values=self.material_manager.get_material_names(),
                                         width=20,
                                         state='readonly')
        self.material_combo.pack(side='left', padx=10)
        
        # Frame para botones de material
        material_buttons_frame = tk.Frame(material_frame, bg='#2d2d2d')
        material_buttons_frame.pack(side='left', padx=5)
        
        # Botones para editar y añadir material
        self.edit_button = ttk.Button(material_buttons_frame,
                                    text="✎",
                                    width=3,
                                    command=self.edit_material)
        self.edit_button.pack(side='left', padx=2)
        
        self.add_button = ttk.Button(material_buttons_frame,
                                   text="+",
                                   width=3,
                                   command=self.add_material)
        self.add_button.pack(side='left', padx=2)
        
        # Frame para la vista previa
        preview_frame = tk.Frame(self.dialog, bg='#2d2d2d')
        preview_frame.pack(pady=20)
        
        # Canvas para la vista previa
        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=300,
            height=300,
            bg='#1e1e1e',
            highlightthickness=1,
            highlightbackground='#3d3d3d'
        )
        self.preview_canvas.pack()
        
        # Frame para botones
        button_frame = tk.Frame(self.dialog, bg='#2d2d2d')
        button_frame.pack(side='bottom', pady=20)
        
        # Botón de generar G-code
        self.gcode_button = ttk.Button(button_frame,
                                     text="Generar G-code ARLA",
                                     command=self.generate_gcode,
                                     width=20)
        self.gcode_button.pack(side='left', padx=10)
        
        # Botón de cancelar
        self.cancel_button = ttk.Button(button_frame,
                                      text="Cancelar",
                                      command=self.cancel_work,
                                      width=20)
        self.cancel_button.pack(side='left', padx=10)
        
        # Si hay materiales, seleccionar el primero
        if self.material_manager.get_materials():
            self.material_combo.set(self.material_manager.get_material_names()[0])
            
        # Bind para cambio de material
        self.material_combo.bind('<<ComboboxSelected>>', self.update_preview)
        
        # Mostrar vista previa inicial
        self.update_preview()
        
        # Evitar que se cierre con Alt+F4
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def update_preview(self, event=None):
        """Actualizar vista previa según el tipo de grabado"""
        if not self.pcb_image:
            return
            
        # Limpiar canvas
        self.preview_canvas.delete('all')
        
        # Obtener material seleccionado
        material = self.material_manager.get_material_by_name(
            self.material_var.get()
        )
        if not material:
            return
        
        # Crear copia de la imagen para procesar
        from PIL import Image, ImageTk
        preview_image = self.pcb_image.copy()
        
        # Asegurar que la imagen está en modo 'L' (escala de grises)
        if preview_image.mode != 'L':
            preview_image = preview_image.convert('L')
        
        # Escalar imagen para el canvas manteniendo proporción
        canvas_width = 300  # Tamaño fijo para el preview
        canvas_height = 300
        
        img_width, img_height = preview_image.size
        scale = min(
            canvas_width / img_width,
            canvas_height / img_height
        )
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Redimensionar imagen
        preview_image = preview_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Centrar en canvas
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        
        # Convertir a PhotoImage
        self.preview_photo = ImageTk.PhotoImage(preview_image)
        
        # Mostrar imagen base
        self.preview_canvas.create_image(
            x, y,
            image=self.preview_photo,
            anchor='nw'
        )
        
        # Superponer visualización según tipo de grabado
        if material['engrave_type'] == 'outline':
            self.show_outline_overlay(x, y, new_width, new_height)
        elif material['engrave_type'] == 'fill':
            self.show_fill_overlay(x, y, new_width, new_height)
        else:  # mixed
            self.show_mixed_overlay(x, y, new_width, new_height)
    
    def show_outline_overlay(self, x, y, width, height):
        """Mostrar overlay de contorno"""
        # Dibujar línea de contorno
        self.preview_canvas.create_rectangle(
            x, y, x + width, y + height,
            outline='#00ff00',
            width=2
        )
        
        self.preview_canvas.create_text(
            x + width//2,
            y + height + 20,
            text="Vista previa: Contorno",
            fill='white',
            font=('Arial', 10)
        )
    
    def show_fill_overlay(self, x, y, width, height):
        """Mostrar overlay de relleno"""
        # Dibujar patrón de líneas
        spacing = 5
        for i in range(0, width, spacing):
            self.preview_canvas.create_line(
                x + i, y,
                x + i, y + height,
                fill='#00ff00',
                width=1
            )
        
        self.preview_canvas.create_text(
            x + width//2,
            y + height + 20,
            text="Vista previa: Relleno",
            fill='white',
            font=('Arial', 10)
        )
    
    def show_mixed_overlay(self, x, y, width, height):
        """Mostrar overlay mixto"""
        self.show_fill_overlay(x, y, width, height)
        self.show_outline_overlay(x, y, width, height)
        
        self.preview_canvas.create_text(
            x + width//2,
            y + height + 20,
            text="Vista previa: Mixto",
            fill='white',
            font=('Arial', 10)
        )
    
    def edit_material(self):
        """Editar material seleccionado"""
        material_name = self.material_var.get()
        material = self.material_manager.get_material_by_name(material_name)
        if material:
            dialog = MaterialDialog(self.dialog, material)
            if dialog.result:
                # Actualizar material
                self.material_manager.update_material(material_name, dialog.result)
                self.update_material_list()
    
    def add_material(self):
        """Añadir nuevo material"""
        dialog = MaterialDialog(self.dialog)
        if dialog.result:
            # Añadir nuevo material
            self.material_manager.add_material(dialog.result)
            self.update_material_list()
    
    def update_material_list(self):
        """Actualizar lista de materiales en el combobox"""
        current = self.material_var.get()
        materials = self.material_manager.get_material_names()
        self.material_combo['values'] = materials
        
        # Mantener selección actual si existe, sino seleccionar el primero
        if current in materials:
            self.material_combo.set(current)
        elif materials:
            self.material_combo.set(materials[0])
        
        self.update_preview()
    
    def cancel_work(self):
        """Cancelar el trabajo"""
        if messagebox.askyesno("Cancelar", 
                             "¿Estás seguro de que quieres cancelar el trabajo?"):
            self.dialog.destroy()
    
    def generate_gcode(self):
        """Generar archivo G-code"""
        try:
            # Obtener material seleccionado
            material = self.material_manager.get_material_by_name(
                self.material_var.get()
            )
            
            if not material:
                messagebox.showerror("Error", "No hay material seleccionado")
                return
            
            # Pedir ubicación para guardar
            file_path = filedialog.asksaveasfilename(
                defaultextension=".arla",
                filetypes=[("ARLA G-code", "*.arla")],
                title="Guardar G-code ARLA"
            )
            
            if file_path:
                # Asegurarnos de que tenemos la imagen correcta
                if not hasattr(self, 'pcb_image') or not self.pcb_image:
                    messagebox.showerror("Error", "No hay imagen PCB")
                    return
                
                logger.debug(f"Generando G-code para imagen: {self.pcb_image.size}")
                logger.debug(f"Posición: {self.pcb_position}")
                
                # Recopilar datos para el generador
                gcode_data = {
                    'image': self.pcb_image,
                    'position': self.pcb_position,
                    'material': material,
                    'machine_config': self.config_manager.get_machine_config()
                }
                
                # Generar G-code
                from gcode_generator import GCodeGenerator
                generator = GCodeGenerator()
                success = generator.generate(gcode_data, file_path)
                
                if success:
                    messagebox.showinfo(
                        "Éxito",
                        "G-code generado correctamente"
                    )
                    self.dialog.destroy()
                else:
                    messagebox.showerror(
                        "Error",
                        "Error generando G-code"
                    )
                    
        except Exception as e:
            logger.error(f"Error en generate_gcode: {e}")
            messagebox.showerror(
                "Error",
                f"Error generando G-code: {str(e)}"
            )

class MaterialDialog:
    def __init__(self, parent, material=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Editar Material" if material else "Nuevo Material")
        
        # Hacer la ventana modal y fija
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.overrideredirect(True)  # Quitar marcos de la ventana
        
        # Configurar ventana
        self.dialog.configure(bg='#2d2d2d')
        
        # Tamaño fijo y centrado
        window_width = 400
        window_height = 500
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.dialog.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Asegurar que la ventana esté por encima
        self.dialog.lift()
        self.dialog.focus_force()
        
        # Borde para hacer la ventana más visible
        self.dialog.configure(highlightbackground='#3d3d3d',
                            highlightthickness=2)
        
        # Variables
        self.name_var = tk.StringVar(value=material['name'] if material else '')
        self.speed_var = tk.StringVar(value=str(material['speed']) if material else '800')
        self.power_var = tk.StringVar(value=str(material['power']) if material else '255')
        self.type_var = tk.StringVar(value=material['engrave_type'] if material else 'outline')
        self.desc_var = tk.StringVar(value=material['description'] if material else '')
        
        # Crear campos
        self.create_fields()
        
        # Resultado
        self.result = None
        
        # Evitar que se cierre con Alt+F4
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Esperar resultado
        self.dialog.wait_window()
    
    def create_fields(self):
        """Crear campos del formulario"""
        # Nombre
        self.create_field("Nombre:", self.name_var)
        
        # Velocidad
        self.create_field("Velocidad (mm/min):", self.speed_var)
        
        # Potencia
        self.create_field("Potencia (0-255):", self.power_var)
        
        # Tipo de grabado
        type_frame = tk.Frame(self.dialog, bg='#2d2d2d')
        type_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(type_frame, 
                text="Tipo de grabado:",
                bg='#2d2d2d',
                fg='white').pack(anchor='w')
        
        types = [('Contorno', 'outline'), 
                ('Relleno', 'fill'), 
                ('Mixto', 'mixed')]
        
        for text, value in types:
            tk.Radiobutton(type_frame,
                          text=text,
                          value=value,
                          variable=self.type_var,
                          bg='#2d2d2d',
                          fg='white',
                          selectcolor='#3d3d3d',
                          activebackground='#2d2d2d').pack(anchor='w')
        
        # Descripción
        desc_frame = tk.Frame(self.dialog, bg='#2d2d2d')
        desc_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(desc_frame,
                text="Descripción:",
                bg='#2d2d2d',
                fg='white').pack(anchor='w')
        
        self.desc_text = tk.Text(desc_frame,
                               height=4,
                               width=40,
                               bg='#3d3d3d',
                               fg='white')
        self.desc_text.pack(fill='x')
        if self.desc_var.get():
            self.desc_text.insert('1.0', self.desc_var.get())
        
        # Botones
        button_frame = tk.Frame(self.dialog, bg='#2d2d2d')
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame,
                  text="Guardar",
                  command=self.save).pack(side='left', padx=5)
        
        ttk.Button(button_frame,
                  text="Cancelar",
                  command=self.cancel).pack(side='left', padx=5)
    
    def create_field(self, label_text, variable):
        """Crear campo de entrada con etiqueta"""
        frame = tk.Frame(self.dialog, bg='#2d2d2d')
        frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(frame,
                text=label_text,
                bg='#2d2d2d',
                fg='white').pack(side='left')
        
        tk.Entry(frame,
                textvariable=variable,
                bg='#3d3d3d',
                fg='white',
                width=20).pack(side='right')
    
    def save(self):
        """Guardar cambios"""
        try:
            # Validar campos
            name = self.name_var.get().strip()
            speed = int(self.speed_var.get())
            power = int(self.power_var.get())
            
            if not name:
                raise ValueError("El nombre es obligatorio")
            if not (0 <= power <= 255):
                raise ValueError("La potencia debe estar entre 0 y 255")
            if speed <= 0:
                raise ValueError("La velocidad debe ser mayor que 0")
            
            # Crear resultado
            self.result = {
                'name': name,
                'speed': speed,
                'power': power,
                'engrave_type': self.type_var.get(),
                'description': self.desc_text.get('1.0', 'end-1c')
            }
            
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def cancel(self):
        """Cancelar edición"""
        self.dialog.destroy()

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
        
        # Botón de trabajo (inicialmente deshabilitado)
        self.work_button = ttk.Button(self.control_panel,
                                    text="Iniciar Trabajo",
                                    command=self.start_work,
                                    state='disabled')
        self.work_button.pack(pady=10)
    
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
                # Verificar si podemos habilitar el botón de trabajo
                self.check_work_button()
    
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
                    # Verificar si podemos habilitar el botón de trabajo
                    self.check_work_button()
            else:
                messagebox.showerror("Error", 
                                   "Error cargando archivo de imagen")
    
    def check_work_button(self):
        """Verificar si podemos habilitar el botón de trabajo"""
        if (self.arduino_manager.is_connected() and 
            self.work_area.pcb_image is not None):
            self.work_button.configure(state='normal')
            logger.info("Botón de trabajo habilitado")
        else:
            self.work_button.configure(state='disabled')
            logger.debug("Botón de trabajo deshabilitado")
    
    def start_work(self):
        """Iniciar el trabajo de grabado"""
        if not self.arduino_manager.is_connected():
            messagebox.showerror("Error", "Arduino no conectado")
            return
            
        if not self.work_area.pcb_image:
            messagebox.showerror("Error", "No hay PCB cargado")
            return
        
        # Crear diálogo de trabajo con la imagen y posición actual
        work_dialog = WorkDialog(
            self.root,
            self.work_area.pcb_image,
            self.work_area.pcb_position
        )
    
    def run(self):
        self.root.mainloop() 