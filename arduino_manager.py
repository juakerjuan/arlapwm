from config_manager import ConfigManager
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('ArduinoManager')

class ArduinoManager:
    _instance = None
    _board = None
    _current_power = 0
    
    def __new__(cls):
        if cls._instance is None:
            logger.debug("Creando nueva instancia de ArduinoManager")
            cls._instance = super(ArduinoManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            logger.debug("Inicializando ArduinoManager")
            self._board = None
            self._current_power = 0
            self._initialized = True
    
    @property
    def board(self):
        return self._board
    
    @board.setter
    def board(self, value):
        logger.debug(f"Estableciendo nueva conexión Arduino: {value is not None}")
        self._board = value
        if value:
            try:
                config_manager = ConfigManager()
                pwm_pin = int(config_manager.config['pwm_pin'])
                logger.debug(f"Configurando pin PWM {pwm_pin}")
                
                # Configurar pin como PWM y apagar
                value.set_pin_mode_pwm_output(pwm_pin)
                value.pwm_write(pwm_pin, 0)
                self._current_power = 0
                logger.debug("Pin PWM configurado y láser apagado")
            except Exception as e:
                logger.error(f"Error configurando pin PWM: {e}")
    
    def is_connected(self):
        connected = self._board is not None
        logger.debug(f"Estado de conexión: {connected}")
        return connected
    
    def set_laser_power(self, power):
        """Método específico para controlar el láser"""
        if not self.is_connected():
            logger.error("No hay conexión con Arduino")
            return False
            
        try:
            config_manager = ConfigManager()
            pwm_pin = int(config_manager.config['pwm_pin'])
            
            logger.debug(f"Estableciendo potencia del láser a {power} en pin {pwm_pin}")
            self._board.pwm_write(pwm_pin, power)
            self._current_power = power
            logger.debug(f"Potencia establecida correctamente a {power}")
            return True
            
        except Exception as e:
            logger.error(f"Error al establecer potencia: {e}")
            return False 