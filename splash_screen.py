import tkinter as tk
from PIL import Image, ImageTk

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        
        # Eliminar bordes de la ventana
        self.root.overrideredirect(True)
        
        # Obtener dimensiones de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Dimensiones del splash
        width = 650
        height = 450  # Aumentado para dar espacio a la imagen
        
        # Calcular posición centrada
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Configurar geometría
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configurar color de fondo
        self.root.configure(bg='#1e1e1e')
        
        try:
            # Cargar y redimensionar la imagen
            img = Image.open("logo.png")  # Asegúrate de tener este archivo
            img = img.resize((400, 250))  # Ajusta el tamaño según necesites
            self.logo = ImageTk.PhotoImage(img)
            
            # Mostrar la imagen
            logo_label = tk.Label(self.root, 
                                image=self.logo,
                                bg='#1e1e1e')
            logo_label.pack(pady=(20,10))
            
        except Exception as e:
            print(f"No se pudo cargar la imagen: {e}")
        
        # Título principal
        title = tk.Label(self.root, 
                        text="ARLA PWM",
                        font=('Arial', 24, 'bold'),
                        fg='#00ff00',
                        bg='#1e1e1e')
        title.pack(pady=(10,10))
        
        # Subtítulo
        subtitle = tk.Label(self.root,
                          text="Control CNC Láser",
                          font=('Arial', 14),
                          fg='white',
                          bg='#1e1e1e')
        subtitle.pack()
        
        # Versión
        version = tk.Label(self.root,
                         text="v1.0",
                         font=('Arial', 10),
                         fg='#888888',
                         bg='#1e1e1e')
        version.pack(pady=(5,0))
        
        # Loading text
        self.loading = tk.Label(self.root,
                              text="Iniciando...",
                              font=('Arial', 10, 'italic'),
                              fg='#666666',
                              bg='#1e1e1e')
        self.loading.pack(side='bottom', pady=20)
        
        # Centrar la ventana
        self.root.update_idletasks()
        
        # Hacer la ventana semi-transparente (solo en Windows)
        try:
            self.root.attributes('-alpha', 0.95)
        except:
            pass
        
        # Mantener la ventana siempre arriba
        self.root.attributes('-topmost', True)
        
    def show(self):
        # Mostrar por 5 segundos
        self.root.after(5000, self.root.destroy)
        self.root.mainloop() 