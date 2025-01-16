from config_manager import ConfigManager
import logging
import time
import threading

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
                # Configurar pin PWM para el láser
                config_manager = ConfigManager()
                pwm_pin = int(config_manager.config['pwm_pin'])
                logger.debug(f"Configurando pin PWM {pwm_pin}")
                value.set_pin_mode_pwm_output(pwm_pin)
                value.pwm_write(pwm_pin, 0)
                self._current_power = 0
                logger.debug("Pin PWM configurado y láser apagado")
                
                # Configurar pines CNC
                logger.debug("Configurando pines CNC")
                self.setup_cnc_pins()
                
            except Exception as e:
                logger.error(f"Error configurando pines: {e}")
    
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
    
    def setup_cnc_pins(self):
        """Configurar pines para CNC"""
        if not self.is_connected():
            logger.error("No hay conexión con Arduino")
            return False
            
        try:
            config = ConfigManager().get_machine_config()
            
            # Obtener y validar pines
            x_step = int(config['x_step'])
            x_dir = int(config['x_dir'])
            x_home = int(config['x_home'])
            y_step = int(config['y_step'])
            y_dir = int(config['y_dir'])
            y_home = int(config['y_home'])
            
            logger.debug(f"Configurando pines X - step:{x_step}, dir:{x_dir}, home:{x_home}")
            logger.debug(f"Configurando pines Y - step:{y_step}, dir:{y_dir}, home:{y_home}")
            
            # Configurar pines de step y dirección como salidas
            self._board.set_pin_mode_digital_output(x_step)
            self._board.set_pin_mode_digital_output(x_dir)
            self._board.set_pin_mode_digital_output(y_step)
            self._board.set_pin_mode_digital_output(y_dir)
            
            # Configurar pines de endstop con pullup interno
            self._board.set_pin_mode_digital_input_pullup(x_home)
            self._board.set_pin_mode_digital_input_pullup(y_home)
            
            # Verificar estado inicial de endstops
            x_home_state = self._board.digital_read(x_home)[0]
            y_home_state = self._board.digital_read(y_home)[0]
            logger.debug(f"Estado inicial endstops - X:{x_home_state}, Y:{y_home_state}")
            
            logger.debug("Pines CNC configurados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando pines CNC: {e}")
            return False
    
    def move_steps(self, axis, steps, direction):
        """Mover motor el número especificado de pasos"""
        if not self.is_connected():
            logger.error("No hay conexión con Arduino")
            return False
            
        try:
            config = ConfigManager().get_machine_config()
            
            # Seleccionar pines según el eje
            if axis.lower() == 'x':
                step_pin = int(config['x_step'])
                dir_pin = int(config['x_dir'])
                home_pin = int(config['x_home'])
                logger.debug(f"Moviendo eje X - step_pin:{step_pin}, dir_pin:{dir_pin}, home_pin:{home_pin}")
            else:  # eje Y
                step_pin = int(config['y_step'])
                dir_pin = int(config['y_dir'])
                home_pin = int(config['y_home'])
                logger.debug(f"Moviendo eje Y - step_pin:{step_pin}, dir_pin:{dir_pin}, home_pin:{home_pin}")
            
            # Establecer dirección
            logger.debug(f"Estableciendo dirección: {'positiva' if direction > 0 else 'negativa'}")
            self._board.digital_write(dir_pin, 1 if direction > 0 else 0)
            time.sleep(0.001)  # Pequeño delay para estabilizar la señal de dirección
            
            logger.debug(f"Iniciando secuencia de {abs(steps)} pasos")
            # Realizar pasos
            for step in range(abs(steps)):
                # Verificar endstop
                endstop_state = self._board.digital_read(home_pin)[0]
                if endstop_state == 0:  # Activo en bajo
                    logger.warning(f"Endstop {axis} activado")
                    return False
                    
                # Paso
                self._board.digital_write(step_pin, 1)
                time.sleep(0.001)  # 1ms de delay
                self._board.digital_write(step_pin, 0)
                time.sleep(0.001)  # 1ms de delay
                
                if step % 10 == 0:  # Log cada 10 pasos
                    logger.debug(f"Completados {step} pasos")
            
            logger.debug(f"Movimiento completado: {abs(steps)} pasos")
            return True
            
        except Exception as e:
            logger.error(f"Error moviendo motor {axis}: {e}")
            return False
    
    def move_mm(self, axis, distance):
        """Mover el eje la distancia especificada en mm"""
        try:
            config = ConfigManager().get_machine_config()
            steps_per_mm = float(config[f'steps_{axis.lower()}'])
            steps = int(abs(distance) * steps_per_mm)
            direction = 1 if distance > 0 else -1
            
            logger.debug(f"Moviendo {axis} {distance}mm ({steps} pasos, {steps_per_mm} pasos/mm)")
            return self.move_steps(axis, steps, direction)
            
        except Exception as e:
            logger.error(f"Error calculando pasos para {axis}: {e}")
            return False
    
    def home_axis(self, axis):
        """Inicia el proceso de home en un thread separado"""
        thread = threading.Thread(target=self._home_axis_thread, args=(axis,))
        thread.daemon = True  # El thread se cerrará cuando el programa principal termine
        thread.start()
        
    def _home_axis_thread(self, axis):
        """Proceso de home que corre en un thread separado"""
        if not self.is_connected():
            logger.error("No hay conexión con Arduino")
            return False
            
        try:
            config = ConfigManager().get_machine_config()
            
            # Seleccionar pines según el eje
            if axis.lower() == 'x':
                step_pin = int(config['x_step'])
                dir_pin = int(config['x_dir'])
                home_pin = int(config['x_home'])
            else:  # eje Y
                step_pin = int(config['y_step'])
                dir_pin = int(config['y_dir'])
                home_pin = int(config['y_home'])
            
            # Establecer dirección negativa (hacia home)
            self._board.digital_write(dir_pin, 0)  # 0 = dirección hacia home
            time.sleep(0.001)
            
            # Mover hasta activar endstop
            while True:
                # Leer estado del endstop
                endstop_state = self._board.digital_read(home_pin)[0]
                if endstop_state == 0:  # Endstop activado (activo en bajo)
                    logger.info(f"¡ENDSTOP {axis.upper()} ACTIVADO!")
                    break
                
                # Dar un paso
                self._board.digital_write(step_pin, 1)
                time.sleep(0.001)
                self._board.digital_write(step_pin, 0)
                time.sleep(0.001)
            
            return True
            
        except Exception as e:
            logger.error(f"Error en home {axis}: {e}")
            return False 