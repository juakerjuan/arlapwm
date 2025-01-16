import tkinter as tk
from tkinter import ttk

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ARLA PWM")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Configuración del tema oscuro
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background='#2b2b2b')
        self.style.configure("TLabel", background='#2b2b2b', foreground='white')
        self.style.configure("TButton", background='#404040', foreground='white')
        
    def run(self):
        self.root.mainloop() 