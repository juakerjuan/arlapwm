import logging
import numpy as np
from PIL import Image
import cv2
import re
import math
from datetime import datetime

logger = logging.getLogger('GCodeGenerator')

class GCodeGenerator:
    def __init__(self):
        self.ARLA_HEADER = ";ARLA-GCODE-V1.0"
        self.MAX_RAPID_SPEED = 2000  # Límite máximo seguro para G0
    
    def generate(self, data, output_path):
        """Generar archivo G-code ARLA"""
        try:
            # Verificar datos
            if not self._validate_data(data):
                return False
            
            # Obtener velocidades (la de grabado ya viene del material)
            engrave_speed = int(data['material']['speed'])
            rapid_speed = min(engrave_speed * 2, self.MAX_RAPID_SPEED)  # G0 al doble de velocidad, con límite
            
            # Iniciar G-code con metadata
            gcode_lines = [
                self.ARLA_HEADER,
                f";Material: {data['material']['name']}",
                f";Engrave Speed: {engrave_speed}",
                f";Rapid Speed: {rapid_speed}",
                f";Power: {data['material']['power']}",
                f";Type: {data['material']['engrave_type']}",
                f";Position: X={data['position']['x']:.3f} Y={data['position']['y']:.3f}",
                f";Image Size: {data['image'].size[0]}x{data['image'].size[1]} px",
                f";Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "G90 ; Coordenadas absolutas",
                "M5  ; Láser apagado",
                f"G0 F{rapid_speed} ; Velocidad para movimientos rápidos",
                ""
            ]
            
            # Generar según tipo
            if data['material']['engrave_type'] == 'outline':
                type_gcode = self._generate_outline(data)
            elif data['material']['engrave_type'] == 'fill':
                type_gcode = self._generate_fill(data)
            else:
                type_gcode = self._generate_mixed(data)
            
            # Añadir estadísticas
            stats = self._calculate_stats(type_gcode)
            gcode_lines.extend([
                "",
                f";Total Lines: {stats['total_lines']}",
                f";Estimated Time: {stats['estimated_time']:.2f} min",
                f";Total Distance: {stats['total_distance']:.2f} mm",
                ""
            ])
            
            # Añadir código generado
            gcode_lines.extend(type_gcode)
            
            # Añadir footer
            gcode_lines.extend([
                "",
                "M5 ; Láser apagado",
                "G0 X0 Y0 ; Volver a origen",
                f";End of ARLA-GCODE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ])
            
            # Guardar archivo
            with open(output_path, 'w') as f:
                f.write('\n'.join(gcode_lines))
            
            return True
            
        except Exception as e:
            logger.error(f"Error generando G-code: {e}")
            return False
    
    def _generate_outline(self, data):
        """Generar G-code para contorno"""
        try:
            logger.debug("Iniciando generación de outline")
            
            # Obtener imagen y sus dimensiones en píxeles
            image = data['image']
            img_width, img_height = image.size
            logger.debug(f"Tamaño en píxeles: {img_width}x{img_height}")
            
            # Obtener posición inicial en la cuadrícula (mm)
            start_x = float(data['position']['x'])
            start_y = float(data['position']['y'])
            logger.debug(f"Posición inicial en cuadrícula (mm): ({start_x}, {start_y})")
            
            # Dimensiones deseadas en mm
            target_width = 80   # 120 - 40 mm
            target_height = 50  # 70 - 20 mm
            
            # Calcular factores de escala (píxeles a mm)
            scale_x = target_width / img_width
            scale_y = target_height / img_height
            logger.debug(f"Factores de escala: X={scale_x:.3f}, Y={scale_y:.3f}")
            
            # Convertir a escala de grises
            if image.mode != 'L':
                image = image.convert('L')
            
            # Convertir a array numpy
            img_array = np.array(image)
            img_array = img_array.astype(np.uint8)
            
            # Detectar bordes
            edges = cv2.Canny(img_array, 100, 200)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(edges, 
                                         cv2.RETR_EXTERNAL, 
                                         cv2.CHAIN_APPROX_SIMPLE)
            
            logger.debug(f"Contornos encontrados: {len(contours)}")
            
            # Generar G-code
            gcode_lines = []
            
            for i, contour in enumerate(contours):
                # Mover a inicio de contorno
                x = float(contour[0][0][0]) * scale_x
                y = float(contour[0][0][1]) * scale_y
                
                # Coordenadas absolutas desde la posición inicial
                abs_x = start_x + x
                abs_y = start_y + y
                
                gcode_lines.extend([
                    f"G0 X{abs_x:.3f} Y{abs_y:.3f} ; Inicio contorno {i+1}",
                    f"M3 S{data['material']['power']} ; Láser encendido"
                ])
                
                # Seguir contorno
                for point in contour[1:]:
                    x = float(point[0][0]) * scale_x
                    y = float(point[0][1]) * scale_y
                    abs_x = start_x + x
                    abs_y = start_y + y
                    gcode_lines.append(f"G1 X{abs_x:.3f} Y{abs_y:.3f}")
                
                # Cerrar contorno
                x = float(contour[0][0][0]) * scale_x
                y = float(contour[0][0][1]) * scale_y
                abs_x = start_x + x
                abs_y = start_y + y
                gcode_lines.extend([
                    f"G1 X{abs_x:.3f} Y{abs_y:.3f} ; Cerrar contorno {i+1}",
                    "M5 ; Láser apagado"
                ])
            
            return gcode_lines
            
        except Exception as e:
            logger.error(f"Error generando outline: {e}")
            logger.exception("Detalles del error:")
            return []
    
    def _generate_fill(self, data):
        """Generar G-code para relleno"""
        try:
            # Obtener imagen y dimensiones
            image = data['image']
            img_width, img_height = image.size
            
            # Obtener posición inicial (mm)
            start_x = float(data['position']['x'])
            start_y = float(data['position']['y'])
            
            # Calcular factores de escala
            target_width = 80   # mm
            target_height = 50  # mm
            scale_x = target_width / img_width
            scale_y = target_height / img_height
            
            # Convertir a escala de grises
            if image.mode != 'L':
                image = image.convert('L')
            
            # Convertir a array numpy
            img_array = np.array(image)
            img_array = img_array.astype(np.uint8)
            
            # Umbral para detectar áreas a rellenar
            _, binary = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
            
            # Generar G-code
            gcode_lines = []
            
            # Espaciado entre líneas (mm)
            line_spacing = 0.2  # Ajustar según necesidad
            
            # Generar líneas horizontales
            for y in range(img_height):
                y_mm = y * scale_y
                y_pos = start_y + y_mm
                
                # Encontrar segmentos en esta línea
                row = binary[y]
                segments = self._find_segments(row)
                
                # Si hay segmentos para grabar
                if segments and y % int(line_spacing/scale_y) == 0:
                    for start_seg, end_seg in segments:
                        # Convertir a mm
                        x1 = start_x + (start_seg * scale_x)
                        x2 = start_x + (end_seg * scale_x)
                        
                        # Mover a inicio de segmento
                        gcode_lines.extend([
                            f"G0 X{x1:.3f} Y{y_pos:.3f} ; Inicio segmento",
                            f"M3 S{data['material']['power']} ; Láser encendido",
                            f"G1 X{x2:.3f} Y{y_pos:.3f} ; Fin segmento",
                            "M5 ; Láser apagado"
                        ])
            
            return gcode_lines
            
        except Exception as e:
            logger.error(f"Error generando fill: {e}")
            logger.exception("Detalles del error:")
            return []
    
    def _find_segments(self, row):
        """Encontrar segmentos continuos en una fila"""
        segments = []
        start = None
        
        for i, val in enumerate(row):
            if val == 0 and start is None:  # Inicio de segmento negro
                start = i
            elif val == 255 and start is not None:  # Fin de segmento negro
                segments.append((start, i))
                start = None
        
        # Si hay un segmento abierto al final
        if start is not None:
            segments.append((start, len(row)))
        
        return segments
    
    def _generate_mixed(self, data):
        """Generar G-code mixto (outline + fill)"""
        try:
            # Generar ambos tipos
            outline_gcode = self._generate_outline(data)
            fill_gcode = self._generate_fill(data)
            
            # Combinar, primero fill y luego outline
            gcode_lines = []
            gcode_lines.extend([
                "; Inicio de relleno",
                "G0 F{} ; Velocidad para relleno".format(data['material']['speed'])
            ])
            gcode_lines.extend(fill_gcode)
            
            gcode_lines.extend([
                "",
                "; Inicio de contorno",
                "G0 F{} ; Velocidad para contorno".format(data['material']['speed'])
            ])
            gcode_lines.extend(outline_gcode)
            
            return gcode_lines
            
        except Exception as e:
            logger.error(f"Error generando mixed: {e}")
            logger.exception("Detalles del error:")
            return []
    
    def _validate_data(self, data):
        """Validar datos necesarios"""
        required = ['image', 'position', 'material', 'machine_config']
        return all(k in data for k in required) 
    
    def _calculate_stats(self, gcode_lines):
        """Calcular estadísticas del G-code"""
        stats = {
            'total_lines': len(gcode_lines),
            'total_distance': 0,
            'estimated_time': 0
        }
        
        last_x = last_y = None
        laser_on = False
        move_distance = 0
        engrave_distance = 0
        
        for line in gcode_lines:
            if 'M3' in line:
                laser_on = True
            elif 'M5' in line:
                laser_on = False
                
            if 'X' in line and 'Y' in line:
                try:
                    # Extraer coordenadas
                    x = float(re.search(r'X([-\d.]+)', line).group(1))
                    y = float(re.search(r'Y([-\d.]+)', line).group(1))
                    
                    if last_x is not None and last_y is not None:
                        # Calcular distancia
                        distance = math.sqrt(
                            (x - last_x)**2 + (y - last_y)**2
                        )
                        stats['total_distance'] += distance
                        
                        if laser_on:
                            engrave_distance += distance
                        else:
                            move_distance += distance
                    
                    last_x, last_y = x, y
                    
                except Exception:
                    continue
        
        # Estimar tiempo (considerando diferentes velocidades)
        move_time = move_distance / 800  # mm/min
        engrave_time = engrave_distance / 800  # mm/min
        stats['estimated_time'] = (move_time + engrave_time) * 60  # min
        
        return stats 