#-*-coding: utf-8-*-
"""
    @author javiermontoya@unah.hn
    @author fausto.maradiaga@unah.hn
    @version 0.1.0
    @date 2021/03/30
"""

from Core.SplashScreen import SplashScreen
from Core.Login import Login

if __name__ == '__main__':

    #Ventana splash screen de bienvenida.
    splashScreen = SplashScreen()

    #Ventana de login.
    login = Login()