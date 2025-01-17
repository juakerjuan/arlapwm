import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from svg_processor import SVGProcessor

logger = logging.getLogger('SVGImport')

class SVGImportWindow:
    def __init__(self, parent, arduino_manager):
        self.arduino_manager = arduino_manager
        
        # Crear ventana modal
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Importar SVG")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg='#1e1e1e')
        self.dialog.resizable(False, False)
        
        # Hacer la ventana modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Inicializar procesador SVG
        self.svg_processor = SVGProcessor()
        
        # Añadir variables para zoom y pan
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.last_x = 0
        self.last_y = 0
        self.dragging = False
        
        # Crear interfaz
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, style='Dark.TFrame')
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title = ttk.Label(main_frame,
                         text="Importar Archivo SVG",
                         font=('Arial', 14, 'bold'),
                         style='Dark.TLabel')
        title.pack(pady=(0,20))
        
        # Botón para seleccionar archivo
        ttk.Button(main_frame,
                  text="Seleccionar Archivo SVG",
                  command=self.load_svg,
                  style='Dark.TButton').pack(pady=10)
        
        # Canvas para vista previa con scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(expand=True, fill='both', pady=20)
        
        self.canvas = tk.Canvas(canvas_frame,
                              width=600,
                              height=400,
                              bg='#2d2d2d',
                              highlightthickness=1,
                              highlightbackground='#3d3d3d')
        self.canvas.pack(expand=True, fill='both')
        
        # Bindear eventos
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)  # Windows
        self.canvas.bind('<Button-4>', self.on_mousewheel)    # Linux scroll up
        self.canvas.bind('<Button-5>', self.on_mousewheel)    # Linux scroll down
        self.canvas.bind('<Button-3>', self.start_pan)        # Botón derecho
        self.canvas.bind('<B3-Motion>', self.update_pan)      # Arrastrar con botón derecho
        self.canvas.bind('<ButtonRelease-3>', self.stop_pan)  # Soltar botón derecho
        
        # Botón de reset zoom
        ttk.Button(main_frame,
                  text="Reset Zoom",
                  command=self.reset_view,
                  style='Dark.TButton').pack(pady=5)
        
        # Label para información
        self.info_label = ttk.Label(main_frame,
                                  text="Ningún archivo seleccionado",
                                  style='Dark.TLabel')
        self.info_label.pack(pady=10)
        
    def load_svg(self):
        """Cargar archivo SVG"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Archivos SVG", "*.svg")]
        )
        if file_path:
            if self.svg_processor.load_file(file_path):
                self.show_preview()
                logger.debug(f"SVG cargado: {file_path}")
            else:
                messagebox.showerror("Error",
                                   "Error al cargar el archivo SVG")
    
    def on_mousewheel(self, event):
        """Manejar zoom con la rueda del ratón"""
        # Obtener posición del ratón
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Determinar dirección del zoom
        if event.num == 5 or event.delta < 0:  # Zoom out
            self.zoom_scale = max(0.1, self.zoom_scale * 0.9)
        else:  # Zoom in
            self.zoom_scale = min(5.0, self.zoom_scale * 1.1)
        
        # Actualizar vista
        self.show_preview()
        
    def start_pan(self, event):
        """Iniciar arrastre"""
        self.dragging = True
        self.last_x = event.x
        self.last_y = event.y
        
    def update_pan(self, event):
        """Actualizar posición durante arrastre"""
        if self.dragging:
            # Calcular diferencia
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            
            # Actualizar posición
            self.pan_x += dx
            self.pan_y += dy
            
            # Guardar posición actual
            self.last_x = event.x
            self.last_y = event.y
            
            # Actualizar vista
            self.show_preview()
        
    def stop_pan(self, event):
        """Detener arrastre"""
        self.dragging = False
        
    def reset_view(self):
        """Resetear zoom y pan"""
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.show_preview()
    
    def show_preview(self):
        """Mostrar vista previa del SVG"""
        # Limpiar canvas
        self.canvas.delete("all")
        
        # Obtener datos
        preview_data = self.svg_processor.get_preview_data()
        dimensions = self.svg_processor.get_dimensions()
        
        if not preview_data or not dimensions:
            return
        
        try:
            # Obtener dimensiones del canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Calcular escala base manteniendo proporción
            scale_x = (canvas_width - 40) / dimensions['width']
            scale_y = (canvas_height - 40) / dimensions['height']
            base_scale = min(scale_x, scale_y)
            
            # Aplicar zoom
            scale = base_scale * self.zoom_scale
            
            # Calcular offset base para centrar
            offset_x = (canvas_width - dimensions['width'] * scale) / 2
            offset_y = (canvas_height - dimensions['height'] * scale) / 2
            
            # Aplicar pan
            offset_x += self.pan_x
            offset_y += self.pan_y
            
            # Actualizar información
            self.info_label.config(
                text=f"Dimensiones: {dimensions['width']:.1f} x {dimensions['height']:.1f} mm | Zoom: {self.zoom_scale:.1f}x"
            )
            
            # Dibujar elementos
            for element in preview_data:
                if element['type'] == 'polygon' and 'points' in element:
                    scaled_points = []
                    for x, y in element['points']:
                        px = offset_x + (x - dimensions['xmin']) * scale
                        py = offset_y + (dimensions['height'] - (y - dimensions['ymin'])) * scale
                        scaled_points.append((px, py))
                    
                    if scaled_points:
                        self.canvas.create_line(scaled_points,
                                             fill='#00ff00',
                                             width=max(1, 2 * self.zoom_scale))
                
                elif element['type'] == 'text':
                    x = offset_x + (element['x'] - dimensions['xmin']) * scale
                    y = offset_y + (dimensions['height'] - (element['y'] - dimensions['ymin'])) * scale
                    self.canvas.create_text(x, y,
                                         text=element['text'],
                                         fill='#00ff00',
                                         anchor='sw',
                                         font=('Arial', int(12 * self.zoom_scale)))
            
        except Exception as e:
            logger.error(f"Error mostrando preview: {e}") 