import serial.tools.list_ports
from tkinter import ttk, Toplevel, messagebox
from pymata4 import pymata4

class ArduinoConnectionDialog:
    def __init__(self, parent):
        self.dialog = Toplevel(parent)
        self.dialog.title("Conectar Arduino")
        self.dialog.geometry("300x400")
        self.dialog.configure(bg='#1e1e1e')
        
        # Hacer la ventana modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar la ventana
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Estilo
        self.style = ttk.Style()
        self.style.configure("Port.TButton", 
                           padding=10, 
                           font=('Arial', 10))
        
        # Título
        title = ttk.Label(self.dialog, 
                         text="Seleccione un Puerto",
                         font=('Arial', 12, 'bold'),
                         foreground='white',
                         background='#1e1e1e')
        title.pack(pady=20)
        
        # Frame para los botones de puertos
        self.ports_frame = ttk.Frame(self.dialog)
        self.ports_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Botón de actualizar
        refresh_button = ttk.Button(self.dialog, 
                                  text="↻ Actualizar Puertos",
                                  command=self.refresh_ports)
        refresh_button.pack(pady=10)
        
        # Variable para almacenar la conexión Arduino
        self.board = None
        
        # Mostrar puertos disponibles
        self.refresh_ports()
    
    def refresh_ports(self):
        # Limpiar botones anteriores
        for widget in self.ports_frame.winfo_children():
            widget.destroy()
        
        # Obtener puertos disponibles
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            ttk.Label(self.ports_frame,
                     text="No se encontraron puertos disponibles",
                     foreground='#888888',
                     background='#1e1e1e').pack(pady=20)
            return
        
        # Crear botón para cada puerto
        for port in ports:
            btn = ttk.Button(self.ports_frame,
                           text=f"{port.device}\n{port.description}",
                           style="Port.TButton",
                           command=lambda p=port.device: self.connect_to_port(p))
            btn.pack(fill='x', pady=5)
    
    def connect_to_port(self, port):
        try:
            # Intentar conectar con Arduino
            self.board = pymata4.Pymata4(com_port=port)
            
            # Si la conexión es exitosa
            messagebox.showinfo("Éxito", 
                              f"Conectado exitosamente a {port}")
            
            # Actualizar el ArduinoManager
            arduino_manager = ArduinoManager()
            arduino_manager.board = self.board
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"No se pudo conectar a {port}\n{str(e)}")
            self.board = None

class ArduinoManager:
    _instance = None
    _board = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ArduinoManager, cls).__new__(cls)
        return cls._instance
    
    @property
    def board(self):
        return self._board
    
    @board.setter
    def board(self, value):
        self._board = value
    
    def is_connected(self):
        return self._board is not None
    
    def disconnect(self):
        if self._board:
            try:
                self._board.shutdown()
                self._board = None
                return True
            except:
                return False
        return True 