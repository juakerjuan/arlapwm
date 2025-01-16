from splash_screen import SplashScreen
from config_screen import ConfigScreen

if __name__ == "__main__":
    # Mostrar splash screen
    splash = SplashScreen()
    splash.show()
    
    # Continuar con la aplicación
    config = ConfigScreen()
    config.run() 