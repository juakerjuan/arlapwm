import svgpathtools
import numpy as np
import logging
import xml.etree.ElementTree as ET
from math import pi, cos, sin, sqrt

logger = logging.getLogger('SVGProcessor')

class SVGProcessor:
    def __init__(self):
        self.paths = []
        self.bounds = None
        self.svg_elements = []
        self.viewbox = None
        self.svg_width = None
        self.svg_height = None
        
    def load_file(self, file_path):
        """Cargar y procesar archivo SVG"""
        try:
            # Cargar el SVG
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Obtener namespace
            self.ns = {'svg': 'http://www.w3.org/2000/svg'}
            
            # Obtener dimensiones del SVG
            self._parse_svg_dimensions(root)
            logger.debug(f"Dimensiones SVG: {self.svg_width}x{self.svg_height}, Viewbox: {self.viewbox}")
            
            # Procesar elementos
            self.svg_elements = []
            self._process_element(root)
            logger.debug(f"Elementos procesados: {len(self.svg_elements)}")
            
            # Imprimir información de elementos para debug
            for i, elem in enumerate(self.svg_elements):
                logger.debug(f"Elemento {i}: tipo={elem['type']}, puntos={len(elem['points']) if 'points' in elem else 'N/A'}")
            
            # Calcular dimensiones
            if self._calculate_bounds():
                logger.debug(f"Bounds calculados: {self.bounds}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error cargando SVG: {e}")
            return False
    
    def _parse_svg_dimensions(self, root):
        """Parsear dimensiones y viewBox del SVG"""
        # Obtener viewBox
        if 'viewBox' in root.attrib:
            self.viewbox = [float(x) for x in root.attrib['viewBox'].split()]
        
        # Obtener width y height
        width = root.attrib.get('width', '100%')
        height = root.attrib.get('height', '100%')
        
        # Convertir dimensiones a números
        self.svg_width = float(width.replace('px', '')) if 'px' in width else None
        self.svg_height = float(height.replace('px', '')) if 'px' in height else None
        
        # Si no hay viewBox, crear uno basado en width/height
        if not self.viewbox and self.svg_width and self.svg_height:
            self.viewbox = [0, 0, self.svg_width, self.svg_height]
    
    def _process_element(self, element, transform_matrix=None):
        """Procesar cada elemento SVG con transformaciones"""
        try:
            # Obtener transformación del elemento
            transform = element.get('transform', '')
            current_transform = self._parse_transform(transform, transform_matrix)
            
            # Procesar por tipo
            tag = element.tag.split('}')[-1]
            
            if tag == 'rect':
                self._process_rect(element, current_transform)
            elif tag == 'circle':
                self._process_circle(element, current_transform)
            elif tag == 'path':
                self._process_path(element, current_transform)
            elif tag == 'text':
                self._process_text(element, current_transform)
            
            # Procesar elementos hijos
            for child in element:
                self._process_element(child, current_transform)
                
        except Exception as e:
            logger.error(f"Error procesando elemento {tag}: {e}")
    
    def _parse_transform(self, transform_str, parent_transform=None):
        """Parsear transformación SVG"""
        matrix = np.identity(3)
        
        if transform_str:
            # Implementar parsing de matrix, translate, scale, rotate
            # Por ahora solo manejamos translate y scale
            if 'translate' in transform_str:
                nums = [float(n) for n in transform_str.split('(')[1].split(')')[0].split(',')]
                trans_matrix = np.identity(3)
                trans_matrix[0,2] = nums[0]
                trans_matrix[1,2] = nums[1] if len(nums) > 1 else 0
                matrix = matrix @ trans_matrix
                
            elif 'scale' in transform_str:
                nums = [float(n) for n in transform_str.split('(')[1].split(')')[0].split(',')]
                scale_matrix = np.identity(3)
                scale_matrix[0,0] = nums[0]
                scale_matrix[1,1] = nums[1] if len(nums) > 1 else nums[0]
                matrix = matrix @ scale_matrix
        
        if parent_transform is not None:
            matrix = parent_transform @ matrix
            
        return matrix
    
    def _transform_point(self, x, y, matrix):
        """Aplicar transformación a un punto"""
        point = np.array([x, y, 1])
        transformed = matrix @ point
        return transformed[0], transformed[1]
    
    def _process_rect(self, element, transform):
        """Procesar elemento rectangle"""
        x = float(element.get('x', 0))
        y = float(element.get('y', 0))
        width = float(element.get('width', 0))
        height = float(element.get('height', 0))
        
        # Crear puntos del rectángulo
        points = [
            self._transform_point(x, y, transform),
            self._transform_point(x + width, y, transform),
            self._transform_point(x + width, y + height, transform),
            self._transform_point(x, y + height, transform),
            self._transform_point(x, y, transform)  # Cerrar el rectángulo
        ]
        
        self.svg_elements.append({
            'type': 'polygon',
            'points': points
        })
    
    def _process_circle(self, element, transform):
        """Procesar elemento circle"""
        cx = float(element.get('cx', 0))
        cy = float(element.get('cy', 0))
        r = float(element.get('r', 0))
        
        # Generar puntos del círculo
        points = []
        num_points = 36  # Más puntos para círculos más suaves
        for i in range(num_points + 1):
            angle = 2 * pi * i / num_points
            x = cx + r * cos(angle)
            y = cy + r * sin(angle)
            points.append(self._transform_point(x, y, transform))
        
        self.svg_elements.append({
            'type': 'polygon',
            'points': points
        })
    
    def get_preview_data(self):
        """Obtener datos para vista previa"""
        if not self.svg_elements:
            return None
        
        return self.svg_elements
    
    def _calculate_bounds(self):
        """Calcular dimensiones del diseño"""
        if not self.svg_elements:
            logger.warning("No hay elementos SVG para calcular dimensiones")
            return False
            
        try:
            points = []
            for element in self.svg_elements:
                if element['type'] == 'polygon' and 'points' in element:
                    points.extend(element['points'])
                elif element['type'] == 'text':
                    points.append((element['x'], element['y']))
            
            if not points:
                logger.warning("No se encontraron puntos para calcular dimensiones")
                return False
            
            x_coords, y_coords = zip(*points)
            
            self.bounds = {
                'xmin': min(x_coords),
                'xmax': max(x_coords),
                'ymin': min(y_coords),
                'ymax': max(y_coords),
                'width': max(x_coords) - min(x_coords),
                'height': max(y_coords) - min(y_coords)
            }
            
            logger.debug(f"Dimensiones calculadas: {self.bounds}")
            return True
            
        except Exception as e:
            logger.error(f"Error calculando dimensiones: {e}")
            return False 
    
    def _process_path(self, element, transform):
        """Procesar elemento path"""
        try:
            # Obtener el atributo d del path
            d = element.get('d', '')
            if not d:
                return
            
            # Convertir el path a objetos Path
            path = svgpathtools.parse_path(d)
            
            # Obtener puntos del path
            points = []
            num_points = 20  # Puntos por segmento
            
            for segment in path:
                segment_points = [segment.point(t) for t in np.linspace(0, 1, num_points)]
                for point in segment_points:
                    x, y = float(point.real), float(point.imag)
                    points.append(self._transform_point(x, y, transform))
            
            if points:
                self.svg_elements.append({
                    'type': 'polygon',
                    'points': points
                })
                
        except Exception as e:
            logger.error(f"Error procesando path: {e}")
    
    def _process_text(self, element, transform):
        """Procesar elemento text"""
        try:
            x = float(element.get('x', 0))
            y = float(element.get('y', 0))
            text = element.text or ''
            
            # Transformar posición del texto
            x, y = self._transform_point(x, y, transform)
            
            self.svg_elements.append({
                'type': 'text',
                'x': x,
                'y': y,
                'text': text
            })
            
        except Exception as e:
            logger.error(f"Error procesando texto: {e}")
    
    def get_dimensions(self):
        """Obtener dimensiones del diseño"""
        return self.bounds 