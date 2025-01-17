from PIL import Image
import logging
import numpy as np

logger = logging.getLogger('PCBProcessor')

class PCBProcessor:
    def __init__(self):
        self.image = None
        self.width_mm = None
        self.height_mm = None
        
    def load_image(self, file_path):
        """Cargar y procesar archivo de PCB (BMP o PNG)"""
        try:
            # Cargar imagen
            self.image = Image.open(file_path)
            
            # Verificar formato soportado
            if self.image.format not in ['BMP', 'PNG']:
                logger.error("El archivo debe ser BMP o PNG")
                return False
            
            # Obtener dimensiones físicas de la imagen
            dpi_info = self.image.info.get('dpi', None)
            
            if dpi_info and isinstance(dpi_info, tuple):
                dpi = dpi_info[0]  # Usar DPI horizontal
                # Convertir pixels a mm usando DPI
                self.width_mm = (self.image.width / dpi) * 25.4
                self.height_mm = (self.image.height / dpi) * 25.4
            else:
                # Si no hay información DPI, usar la resolución física si existe
                physical = self.image.info.get('physical', None)
                if physical and isinstance(physical, tuple):
                    # physical viene en pixels/metro, convertir a mm
                    ppm_x, ppm_y = physical
                    self.width_mm = (self.image.width / ppm_x) * 1000
                    self.height_mm = (self.image.height / ppm_y) * 1000
                else:
                    # Si no hay información de tamaño físico, usar 96 DPI como estándar
                    dpi = 96
                    self.width_mm = (self.image.width / dpi) * 25.4
                    self.height_mm = (self.image.height / dpi) * 25.4
            
            logger.info(f"Imagen cargada: {self.width_mm:.2f}mm x {self.height_mm:.2f}mm")
            logger.debug(f"Formato: {self.image.format}, Modo: {self.image.mode}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando imagen: {e}")
            return False
    
    def get_dimensions(self):
        """Obtener dimensiones del PCB en mm"""
        if self.width_mm and self.height_mm:
            return {
                'width': self.width_mm,
                'height': self.height_mm
            }
        return None
    
    def get_preview_image(self):
        """Obtener imagen procesada para preview"""
        if self.image is None:
            return None
            
        try:
            # Convertir a escala de grises si no lo está
            if self.image.mode != 'L':
                preview = self.image.convert('L')
            else:
                preview = self.image.copy()
            
            # Invertir imagen (pistas en blanco)
            preview = Image.eval(preview, lambda x: 255 - x)
            
            return preview
            
        except Exception as e:
            logger.error(f"Error preparando preview: {e}")
            return None 