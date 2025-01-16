class ConfigManager:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    @property
    def config(self):
        return self._config
    
    @config.setter
    def config(self, value):
        self._config = value
    
    def get_machine_config(self):
        """Retorna la configuración actual de la máquina"""
        return self._config
    
    def get_pin(self, pin_name):
        """Obtiene un pin específico de la configuración"""
        return self._config.get(pin_name) if self._config else None
    
    def get_steps_per_mm(self, axis):
        """Obtiene los pasos por mm para un eje específico"""
        key = f'steps_{axis}'
        return float(self._config.get(key, 0)) if self._config else 0
    
    def get_machine_dimensions(self):
        """Obtiene las dimensiones de la máquina"""
        if self._config:
            return {
                'length': float(self._config.get('length', 0)),
                'width': float(self._config.get('width', 0))
            }
        return {'length': 0, 'width': 0} 