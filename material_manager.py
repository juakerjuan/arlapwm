import json
import os
import logging

logger = logging.getLogger('MaterialManager')

class MaterialManager:
    def __init__(self):
        self.materials = []
        self.load_materials()
    
    def load_materials(self):
        """Cargar materiales desde el archivo JSON"""
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'materials.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.materials = data.get('materials', [])
                logger.info(f"Materiales cargados: {len(self.materials)}")
            else:
                logger.warning("Archivo de materiales no encontrado")
                self.materials = []
        except Exception as e:
            logger.error(f"Error cargando materiales: {e}")
            self.materials = []
    
    def get_materials(self):
        """Obtener lista de materiales"""
        return self.materials
    
    def get_material_names(self):
        """Obtener lista de nombres de materiales"""
        return [material['name'] for material in self.materials]
    
    def get_material_by_name(self, name):
        """Obtener material por nombre"""
        for material in self.materials:
            if material['name'] == name:
                return material
        return None
    
    def add_material(self, material):
        """Añadir nuevo material"""
        if self.get_material_by_name(material['name']):
            logger.warning(f"Material {material['name']} ya existe")
            return False
        
        self.materials.append(material)
        self.save_materials()
        return True
    
    def save_materials(self):
        """Guardar materiales en el archivo JSON"""
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'materials.json')
            with open(json_path, 'w', encoding='utf-8') as file:
                json.dump({'materials': self.materials}, file, indent=4)
            logger.info("Materiales guardados correctamente")
            return True
        except Exception as e:
            logger.error(f"Error guardando materiales: {e}")
            return False 
    
    def update_material(self, old_name, new_material):
        """Actualizar material existente"""
        for i, material in enumerate(self.materials):
            if material['name'] == old_name:
                self.materials[i] = new_material
                self.save_materials()
                return True
        return False 