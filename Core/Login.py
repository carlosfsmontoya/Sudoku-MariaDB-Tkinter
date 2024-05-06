#-*-coding: utf-8-*-
"""
    @author javiermontoya@unah.hn
    @version 0.1.8
    @date 2021/03/31
"""

from tkinter import Tk, Label, Entry, Button, StringVar
from functools import partial
from Core.Menu import Menu
from Core.User import User
from Core.MySQLEngine import MySQLEngine
import mysql.connector

class Login:

    def __init__(self):

        # Se crea una nueva ventana.
        self.root = Tk()
        self.root.resizable(0, 0)
        self.root.title("Login")

        # Se obtienen las coordenadas del centro de la pantalla.
        x = self.root.winfo_screenwidth() // 2 - 400//2
        y = self.root.winfo_screenheight() // 2 - 200//2

        # Se ubica la ventana.
        self.root.geometry("400x200"+"+"+str(x)+"+"+str(y))

        # Variable, etiqueta y caja de texto para el usuario.
        username = StringVar()
        Label(self.root, text="\nUsuario:").pack()
        Entry(self.root, textvariable=username).pack()

        # Variable, etiqueta y caja de texto para la contraseña.
        password = StringVar()
        Label(self.root, text="Contraseña:").pack()
        Entry(self.root, textvariable=password, show='*').pack()

        # Se congela y almacena la función.
        validateLogin = partial(self.validateLogin, username, password)

        Label(self.root, text="").pack()

        # Botón que validará el login.
        Button(self.root, text="Login", command=validateLogin).pack()

        # Variable y etiqueta que mostrará un mensaje si el usuario y/o contraseña no existen o no coinciden.
        self.text = StringVar()
        Label(self.root, textvariable=self.text, fg="red").pack()

        self.root.mainloop()

    def validateLogin(self, username, password):

        # Generar una conexión.
        engine = MySQLEngine()

        # Guardamos los datos necesarios para llamar al procedimiento almacenado que devolverá el rol si:
        # - El usuario existe.
        # - El usuario y la contraseña coinciden.
        args = (username.get(), password.get(), 'TEXT', 'TEXT', 'TEXT')

        # Llamamos al proceso almacenado y guardamos el resultado de la transacción.
        result = engine.callSP('sp_validate', args)

        # En la variable result se almacenarán los siguientes campos:
        # La posición 0 contiene el usuario.
        # La posición 1 contiene la contraseña.
        # La posición 2 contiene el id del usuario.
        # La posición 3 contiene el rol.
        # La posición 4 contiene el estado (juego pausado)
        # Si el usuario/contraseña no existen la posición 2-3-4 serán None.
        if((result[2] and result[3] and result[4]) is not None):

            # Se destruye la ventana actual.
            self.root.destroy()
            
            # Se crea un objeto User para almacenar los datos de usuario necesarios en el sistema
            # User(idUser,status,role)
            user = User(result[2], result[4], result[3])
            # Se hace una nueva intancia del Menu y se envia el objeto usuario
            menu = Menu(user)

            # Cerramos la conexión.
            engine.closeCon()

        else:
            self.text.set("Nombre de usuario o contraseña incorrecta.")
