import json
import os
import logging

logger = logging.getLogger('ConfigManager')

class ConfigManager:
    _instance = None
    _config = None
    _config_file = 'config.json'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self):
        """Cargar configuración desde archivo"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r') as f:
                    self._config = json.load(f)
            else:
                self._config = {}
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self._config = {}
    
    def save_config(self):
        """Guardar configuración en archivo"""
        try:
            with open(self._config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
            logger.debug("Configuración guardada exitosamente")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            raise
    
    @property
    def config(self):
        return self._config
    
    @config.setter
    def config(self, value):
        self._config = value
        self.save_config()  # Guardar automáticamente cuando se actualiza la configuración
    
    def get_machine_config(self):
        """Obtener configuración de la máquina actual"""
        machine_name = self._config.get('machine_name')
        if machine_name and 'machines' in self._config and machine_name in self._config['machines']:
            return self._config['machines'][machine_name]
        return self._config
    
    def get_pin(self, pin_name):
        """Obtiene un pin específico de la configuración"""
        return self._config.get(pin_name) if self._config else None
    
    def get_steps_per_mm(self, axis):
        """Obtiene los pasos por mm para un eje específico"""
        key = f'steps_per_mm_{axis}'
        return float(self._config.get(key, 0)) if self._config else 0
    
    def get_machine_dimensions(self):
        """Obtiene las dimensiones de la máquina"""
        if self._config:
            return {
                'length': float(self._config.get('length', 0)),
                'width': float(self._config.get('width', 0))
            }
        return {'length': 0, 'width': 0} 