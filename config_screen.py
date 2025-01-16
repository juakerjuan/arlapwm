import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from PIL import Image, ImageTk
from config_manager import ConfigManager

class ConfigScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ARLA PWM - Configuración")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e1e')
        
        # Estilo mejorado
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.setup_styles()
        
        # Contenedor principal con padding
        self.main_frame = ttk.Frame(self.root, style="Config.TFrame")
        self.main_frame.pack(padx=30, pady=20, fill='both', expand=True)
        
        # Selector de configuración existente
        config_selector = ttk.Frame(self.main_frame, style="Config.TFrame")
        config_selector.pack(fill='x', pady=(0,10))
        
        ttk.Label(config_selector, 
                 text="Cargar configuración:", 
                 style="Subtitle.TLabel").pack(side='left', padx=5)
        
        self.machine_selector = ttk.Combobox(config_selector, width=30)
        self.machine_selector.pack(side='left', padx=5)
        
        ttk.Button(config_selector, 
                  text="Cargar",
                  command=self.load_selected_config).pack(side='left', padx=5)
        
        # Actualizar lista de máquinas disponibles
        self.update_machine_list()
        
        # Título principal
        title = ttk.Label(self.main_frame, 
                         text="Configuración del Sistema CNC",
                         style="Title.TLabel")
        title.pack(pady=(0,20))
        
        # Pines disponibles
        self.available_pins = [str(i) for i in range(2,14) if i != 3]
        
        # Sección de Ejes
        self.create_axis_config()
        
        # Separador visual
        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=20)
        
        # Sección de Máquina
        self.create_machine_config()
        
        # Botón guardar
        self.save_button = ttk.Button(self.main_frame, 
                                    text="✓ Guardar y Continuar",
                                    style="Save.TButton",
                                    command=self.validate_and_save)
        self.save_button.pack(pady=30)

        # Cargar configuración si existe
        self.load_config()

    def setup_styles(self):
        self.style.configure("Title.TLabel", 
                           background='#1e1e1e', 
                           foreground='#00ff00',
                           font=('Arial', 12, 'bold'))
        
        self.style.configure("Subtitle.TLabel",
                           background='#1e1e1e',
                           foreground='#ffffff',
                           font=('Arial', 10))
        
        self.style.configure("Config.TFrame", background='#1e1e1e', padding=10)
        self.style.configure("Config.TLabelframe", 
                           background='#1e1e1e',
                           foreground='#00ff00',
                           padding=15)
        
        self.style.configure("Config.TLabelframe.Label", 
                           background='#1e1e1e',
                           foreground='#00ff00',
                           font=('Arial', 11, 'bold'))
        
        self.style.configure("Save.TButton",
                           padding=10,
                           font=('Arial', 10, 'bold'))
        
        # Agregar estilo específico para el Entry readonly
        self.style.map('TEntry',
            fieldbackground=[('readonly', '#404040')],
            foreground=[('readonly', 'white')]
        )

    def validate_numeric(self, P):
        if P == "": return True
        try:
            float(P)
            return True
        except ValueError:
            return False

    def create_axis_config(self):
        axis_frame = ttk.LabelFrame(self.main_frame, 
                                  text="Configuración de Ejes",
                                  style="Config.TLabelframe")
        axis_frame.pack(fill='x', pady=10)
        
        # Eje X
        x_frame = ttk.Frame(axis_frame, style="Config.TFrame")
        x_frame.pack(fill='x', pady=10)
        
        ttk.Label(x_frame, text="Eje X:", style="Subtitle.TLabel").pack(side='left', padx=(0,20))
        
        self.x_dir = ttk.Combobox(x_frame, values=self.available_pins, width=5)
        self.x_step = ttk.Combobox(x_frame, values=self.available_pins, width=5)
        self.x_home = ttk.Combobox(x_frame, values=self.available_pins, width=5)
        self.x_end = ttk.Combobox(x_frame, values=self.available_pins, width=5)
        
        for widget, label in [(self.x_dir, "DIR"), (self.x_step, "STEP"), 
                            (self.x_home, "HOME"), (self.x_end, "END")]:
            ttk.Label(x_frame, text=label, style="Subtitle.TLabel").pack(side='left', padx=(0,5))
            widget.pack(side='left', padx=(0,20))
        
        # Eje Y
        y_frame = ttk.Frame(axis_frame, style="Config.TFrame")
        y_frame.pack(fill='x', pady=10)
        
        ttk.Label(y_frame, text="Eje Y:", style="Subtitle.TLabel").pack(side='left', padx=(0,20))
        
        self.y_dir = ttk.Combobox(y_frame, values=self.available_pins, width=5)
        self.y_step = ttk.Combobox(y_frame, values=self.available_pins, width=5)
        self.y_home = ttk.Combobox(y_frame, values=self.available_pins, width=5)
        self.y_end = ttk.Combobox(y_frame, values=self.available_pins, width=5)
        
        for widget, label in [(self.y_dir, "DIR"), (self.y_step, "STEP"), 
                            (self.y_home, "HOME"), (self.y_end, "END")]:
            ttk.Label(y_frame, text=label, style="Subtitle.TLabel").pack(side='left', padx=(0,5))
            widget.pack(side='left', padx=(0,20))
        
        # PWM Pin
        pwm_frame = ttk.Frame(axis_frame, style="Config.TFrame")
        pwm_frame.pack(fill='x', pady=10)
        ttk.Label(pwm_frame, text="PWM Pin:", style="Subtitle.TLabel").pack(side='left', padx=5)
        self.pwm_pin = ttk.Entry(pwm_frame, width=5)
        self.pwm_pin.insert(0, "3")
        self.pwm_pin.configure(state='readonly')
        self.pwm_pin.pack(side='left', padx=5)

    def create_machine_config(self):
        machine_frame = ttk.LabelFrame(self.main_frame, 
                                     text="Detalles de la Máquina",
                                     style="Config.TLabelframe")
        machine_frame.pack(fill='x', pady=10)
        
        # Validación numérica
        vcmd = (self.root.register(self.validate_numeric), '%P')
        
        # Primera fila
        row1 = ttk.Frame(machine_frame, style="Config.TFrame")
        row1.pack(fill='x', pady=5)
        
        ttk.Label(row1, text="Largo (mm):", style="Subtitle.TLabel").pack(side='left', padx=5)
        self.length = ttk.Entry(row1, width=10, validate='key', validatecommand=vcmd)
        self.length.pack(side='left', padx=(0,20))
        
        ttk.Label(row1, text="Ancho (mm):", style="Subtitle.TLabel").pack(side='left', padx=5)
        self.width = ttk.Entry(row1, width=10, validate='key', validatecommand=vcmd)
        self.width.pack(side='left')
        
        # Segunda fila
        row2 = ttk.Frame(machine_frame, style="Config.TFrame")
        row2.pack(fill='x', pady=5)
        
        ttk.Label(row2, text="Pasos/mm X:", style="Subtitle.TLabel").pack(side='left', padx=5)
        self.steps_x = ttk.Entry(row2, width=10, validate='key', validatecommand=vcmd)
        self.steps_x.pack(side='left', padx=(0,20))
        
        ttk.Label(row2, text="Pasos/mm Y:", style="Subtitle.TLabel").pack(side='left', padx=5)
        self.steps_y = ttk.Entry(row2, width=10, validate='key', validatecommand=vcmd)
        self.steps_y.pack(side='left')
        
        # Tercera fila
        row3 = ttk.Frame(machine_frame, style="Config.TFrame")
        row3.pack(fill='x', pady=5)
        
        ttk.Label(row3, text="Nombre:", style="Subtitle.TLabel").pack(side='left', padx=5)
        self.machine_name = ttk.Entry(row3, width=30)
        self.machine_name.pack(side='left', padx=(0,20))
        
        ttk.Label(row3, text="Tipo/Potencia Láser:", style="Subtitle.TLabel").pack(side='left', padx=5)
        self.laser_type = ttk.Entry(row3, width=30)
        self.laser_type.pack(side='left')
        
        # Nota sobre pasos/mm
        note_frame = ttk.Frame(machine_frame, style="Config.TFrame")
        note_frame.pack(fill='x', pady=10)
        note = ttk.Label(note_frame, 
                        text="Nota: Si desconoce el número de pasos por mm, " +
                             "use 50 como valor inicial. Podrá ajustarlo posteriormente en calibración.",
                        style="Note.TLabel",
                        wraplength=500)  # Para que el texto se ajuste al ancho
        note.pack(pady=5)
        
        # Agregar estilo para la nota
        self.style.configure("Note.TLabel",
                           background='#1e1e1e',
                           foreground='#888888',  # Gris claro
                           font=('Arial', 9, 'italic'))

    def validate_and_save(self):
        # Recopilar todos los pines seleccionados
        selected_pins = [
            self.x_dir.get(), self.x_step.get(), self.x_home.get(), self.x_end.get(),
            self.y_dir.get(), self.y_step.get(), self.y_home.get(), self.y_end.get()
        ]
        
        # Validar campos vacíos
        if '' in selected_pins or not all([
            self.length.get(), self.width.get(), 
            self.steps_x.get(), self.steps_y.get(),
            self.machine_name.get(), self.laser_type.get()
        ]):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        
        # Validar pines únicos
        if len(set(selected_pins)) != len(selected_pins):
            messagebox.showerror("Error", "Los pines no pueden repetirse")
            return
        
        # Validar números en campos numéricos
        try:
            float(self.length.get())
            float(self.width.get())
            float(self.steps_x.get())
            float(self.steps_y.get())
        except ValueError:
            messagebox.showerror("Error", "Las dimensiones y pasos deben ser números")
            return
        
        # Crear el diccionario de configuración
        config_data = {
            'x_dir': self.x_dir.get(),
            'x_step': self.x_step.get(),
            'x_home': self.x_home.get(),
            'x_end': self.x_end.get(),
            'y_dir': self.y_dir.get(),
            'y_step': self.y_step.get(),
            'y_home': self.y_home.get(),
            'y_end': self.y_end.get(),
            'pwm_pin': '3',
            'length': self.length.get(),
            'width': self.width.get(),
            'steps_x': self.steps_x.get(),
            'steps_y': self.steps_y.get(),
            'machine_name': self.machine_name.get(),
            'laser_type': self.laser_type.get()
        }
        
        # Guardar en el archivo
        configs = {'machines': {}}
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    configs = json.load(f)
                    if 'machines' not in configs:
                        configs['machines'] = {}
            except:
                pass
        
        configs['machines'][self.machine_name.get()] = config_data
        
        with open('config.json', 'w') as f:
            json.dump(configs, f)
        
        # Guardar en el ConfigManager
        config_manager = ConfigManager()
        config_manager.config = config_data
        
        # Continuar con la siguiente ventana
        from main_window import MainWindow
        self.root.destroy()
        main = MainWindow()
        main.run()

    def load_config(self):
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                
                self.x_dir.set(config['x_dir'])
                self.x_step.set(config['x_step'])
                self.x_home.set(config['x_home'])
                self.x_end.set(config['x_end'])
                self.y_dir.set(config['y_dir'])
                self.y_step.set(config['y_step'])
                self.y_home.set(config['y_home'])
                self.y_end.set(config['y_end'])
                self.length.insert(0, config['length'])
                self.width.insert(0, config['width'])
                self.steps_x.insert(0, config['steps_x'])
                self.steps_y.insert(0, config['steps_y'])
                self.machine_name.insert(0, config['machine_name'])
                self.laser_type.insert(0, config['laser_type'])
            except:
                pass

    def run(self):
        self.root.mainloop()

    def update_machine_list(self):
        """Actualiza la lista de máquinas disponibles en el selector"""
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    configs = json.load(f)
                if 'machines' in configs:
                    machines = list(configs['machines'].keys())
                    self.machine_selector['values'] = machines
            except:
                pass

    def load_selected_config(self):
        """Carga la configuración de la máquina seleccionada"""
        selected = self.machine_selector.get()
        if not selected:
            return
            
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    configs = json.load(f)
                if 'machines' in configs and selected in configs['machines']:
                    config = configs['machines'][selected]
                    
                    # Limpiar campos existentes
                    self.clear_fields()
                    
                    # Cargar configuración
                    self.x_dir.set(config['x_dir'])
                    self.x_step.set(config['x_step'])
                    self.x_home.set(config['x_home'])
                    self.x_end.set(config['x_end'])
                    self.y_dir.set(config['y_dir'])
                    self.y_step.set(config['y_step'])
                    self.y_home.set(config['y_home'])
                    self.y_end.set(config['y_end'])
                    self.length.insert(0, config['length'])
                    self.width.insert(0, config['width'])
                    self.steps_x.insert(0, config['steps_x'])
                    self.steps_y.insert(0, config['steps_y'])
                    self.machine_name.insert(0, config['machine_name'])
                    self.laser_type.insert(0, config['laser_type'])
            except:
                pass

    def clear_fields(self):
        """Limpia todos los campos del formulario"""
        self.x_dir.set('')
        self.x_step.set('')
        self.x_home.set('')
        self.x_end.set('')
        self.y_dir.set('')
        self.y_step.set('')
        self.y_home.set('')
        self.y_end.set('')
        self.length.delete(0, tk.END)
        self.width.delete(0, tk.END)
        self.steps_x.delete(0, tk.END)
        self.steps_y.delete(0, tk.END)
        self.machine_name.delete(0, tk.END)
        self.laser_type.delete(0, tk.END)

if __name__ == "__main__":
    app = ConfigScreen()
    app.run() 