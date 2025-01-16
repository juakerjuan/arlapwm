import tkinter as tk
from tkinter import ttk, messagebox
import logging
from config_manager import ConfigManager
from arduino_manager import ArduinoManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('CalibrationControl')

class CalibrationDialog:
    def __init__(self, parent, arduino_manager=None):
        logger.debug("Iniciando CalibrationDialog")
        
        self.arduino_manager = arduino_manager if arduino_manager else ArduinoManager()
        self.config_manager = ConfigManager()
        
        # Obtener el nombre de la máquina actual desde la configuración principal
        all_config = self.config_manager.config
        self.current_machine = all_config.get('machine_name')
        logger.debug(f"Máquina actual: {self.current_machine}")
        
        # Crear la ventana
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Calibración de Pasos/mm")
        self.dialog.geometry("500x750")
        self.dialog.configure(bg='#1e1e1e')
        self.dialog.resizable(False, False)
        
        # Hacer la ventana modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Crear interfaz
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, style='Dark.TFrame')
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título con nombre de máquina
        title = ttk.Label(main_frame,
                         text=f"Calibración de Pasos/mm - {self.current_machine}",
                         font=('Arial', 14, 'bold'),
                         style='Dark.TLabel')
        title.pack(pady=(0,20))
        
        # Frame de instrucciones con estilo oscuro
        instructions_frame = ttk.LabelFrame(main_frame, 
                                          text="Instrucciones",
                                          style='Dark.TLabelframe',
                                          padding=15)
        instructions_frame.pack(fill='x', pady=(0,20))
        
        instructions = [
            "Proceso de Calibración:",
            "1. Seleccione el eje a calibrar (X o Y)",
            "2. La máquina se moverá 100mm según la configuración actual",
            "3. Mida la distancia real recorrida con una regla",
            "4. Ingrese la distancia medida",
            "5. El sistema calculará los nuevos pasos/mm"
        ]
        
        for instruction in instructions:
            ttk.Label(instructions_frame,
                     text=instruction,
                     style='Dark.TLabel').pack(anchor='w', pady=2)
        
        # Frame para calibración X con estilo oscuro
        x_frame = ttk.LabelFrame(main_frame, 
                               text="Calibración Eje X",
                               style='Dark.TLabelframe',
                               padding=15)
        x_frame.pack(fill='x', pady=(0,15))
        
        # Crear la etiqueta x_steps_label
        current_steps_x = self.config_manager.get_machine_config()['steps_x']
        self.x_steps_label = ttk.Label(x_frame,
                                     text=f"Pasos/mm actuales X: {current_steps_x}",
                                     style='Dark.TLabel')
        self.x_steps_label.pack(anchor='w', pady=5)
        
        ttk.Button(x_frame,
                  text="Mover 100mm en X",
                  style='Dark.TButton',
                  command=lambda: self.move_axis('x', 100)).pack(pady=5)
        
        ttk.Label(x_frame,
                 text="Distancia medida (mm):",
                 style='Dark.TLabel').pack(pady=5)
        
        self.x_distance = ttk.Entry(x_frame, width=10, style='Dark.TEntry')
        self.x_distance.pack(pady=5)
        
        ttk.Button(x_frame,
                  text="Calcular pasos/mm X",
                  style='Dark.TButton',
                  command=lambda: self.calculate_steps('x')).pack(pady=5)
        
        # Frame para calibración Y con estilo oscuro
        y_frame = ttk.LabelFrame(main_frame,
                               text="Calibración Eje Y",
                               style='Dark.TLabelframe',
                               padding=15)
        y_frame.pack(fill='x', pady=(0,15))
        
        # Crear la etiqueta y_steps_label
        current_steps_y = self.config_manager.get_machine_config()['steps_y']
        self.y_steps_label = ttk.Label(y_frame,
                                     text=f"Pasos/mm actuales Y: {current_steps_y}",
                                     style='Dark.TLabel')
        self.y_steps_label.pack(anchor='w', pady=5)
        
        ttk.Button(y_frame,
                  text="Mover 100mm en Y",
                  style='Dark.TButton',
                  command=lambda: self.move_axis('y', 100)).pack(pady=5)
        
        ttk.Label(y_frame,
                 text="Distancia medida (mm):",
                 style='Dark.TLabel').pack(pady=5)
        
        self.y_distance = ttk.Entry(y_frame, width=10, style='Dark.TEntry')
        self.y_distance.pack(pady=5)
        
        ttk.Button(y_frame,
                  text="Calcular pasos/mm Y",
                  style='Dark.TButton',
                  command=lambda: self.calculate_steps('y')).pack(pady=5)
        
        # Botón para guardar cambios
        ttk.Button(main_frame,
                  text="Guardar y Cerrar",
                  style='Dark.TButton',
                  command=self.save_and_close).pack(pady=20)
    
    def move_axis(self, axis, distance):
        """Mover eje la distancia especificada"""
        logger.debug(f"Moviendo {axis} {distance}mm")
        if self.arduino_manager.move_mm(axis, distance):
            messagebox.showinfo("Movimiento Completado",
                              f"Por favor, mida la distancia real recorrida en {axis}")
        else:
            messagebox.showerror("Error",
                               f"Error moviendo el eje {axis}")
    
    def calculate_steps(self, axis):
        """Calcular nuevos pasos/mm"""
        try:
            # Obtener valores
            current_steps = float(self.config_manager.get_machine_config()[f'steps_{axis}'])
            expected_distance = 100.0
            logger.debug(f"Pasos actuales {axis}: {current_steps}")
            
            # Obtener distancia medida del entry correspondiente
            measured_text = self.x_distance.get() if axis == 'x' else self.y_distance.get()
            if not measured_text:
                messagebox.showerror("Error", "Por favor, ingrese la distancia medida")
                return
                
            measured_distance = float(measured_text)
            logger.debug(f"Distancia medida {axis}: {measured_distance}mm")
            
            if measured_distance <= 0:
                messagebox.showerror("Error", "La distancia medida debe ser mayor que 0")
                return
            
            # Calcular nuevos pasos/mm
            new_steps = (current_steps * expected_distance) / measured_distance
            logger.debug(f"Nuevos pasos calculados {axis}: {new_steps}")
            
            # Mostrar resultado
            if messagebox.askyesno("Confirmar Cambio",
                                 f"Pasos actuales {axis}: {current_steps}\n"
                                 f"Distancia esperada: {expected_distance}mm\n"
                                 f"Distancia medida: {measured_distance}mm\n"
                                 f"Nuevos pasos/mm: {new_steps:.2f}\n"
                                 f"¿Desea aplicar este cambio?"):
                
                try:
                    # Hacer una copia de seguridad de la configuración actual
                    import shutil
                    import time
                    backup_file = f'config_backup_{int(time.time())}.json'
                    shutil.copy('config.json', backup_file)
                    logger.debug(f"Backup creado: {backup_file}")
                    
                    # Obtener toda la configuración
                    all_config = self.config_manager.config
                    logger.debug(f"Configuración actual: {all_config}")
                    
                    # Actualizar solo el valor de steps en la máquina actual
                    if 'machines' in all_config and self.current_machine in all_config['machines']:
                        all_config['machines'][self.current_machine][f'steps_{axis}'] = str(round(new_steps, 2))
                        if all_config.get('machine_name') == self.current_machine:
                            all_config[f'steps_{axis}'] = str(round(new_steps, 2))
                    else:
                        logger.warning("No se encontró la sección 'machines' o la máquina actual")
                        if 'machines' not in all_config:
                            all_config['machines'] = {}
                        if self.current_machine not in all_config['machines']:
                            all_config['machines'][self.current_machine] = {}
                            for key in all_config:
                                if key != 'machines':
                                    all_config['machines'][self.current_machine][key] = all_config[key]
                        all_config['machines'][self.current_machine][f'steps_{axis}'] = str(round(new_steps, 2))
                        if all_config.get('machine_name') == self.current_machine:
                            all_config[f'steps_{axis}'] = str(round(new_steps, 2))
                    
                    # Guardar toda la configuración
                    self.config_manager.config = all_config
                    logger.debug(f"Configuración actualizada exitosamente para {self.current_machine}")
                    
                    # Actualizar etiqueta
                    label = self.x_steps_label if axis == 'x' else self.y_steps_label
                    label.configure(text=f"Pasos/mm actuales {axis.upper()}: {round(new_steps, 2)}")
                    
                    messagebox.showinfo("Éxito", f"Pasos/mm actualizados para eje {axis.upper()}")
                    
                except Exception as e:
                    logger.error(f"Error guardando configuración: {e}")
                    messagebox.showerror("Error", 
                                       "Error guardando la configuración\n"
                                       f"Se creó un backup en {backup_file}")
        
        except ValueError as e:
            logger.error(f"Error en cálculo: {e}")
            messagebox.showerror("Error", "Por favor, ingrese un número válido")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            messagebox.showerror("Error", f"Error inesperado: {e}")
    
    def save_and_close(self):
        """Guardar cambios y cerrar ventana"""
        try:
            logger.debug("Cerrando ventana de calibración")
            self.dialog.destroy()
            
        except Exception as e:
            logger.error(f"Error al cerrar: {e}")
            messagebox.showerror("Error", "Error al cerrar la ventana") 