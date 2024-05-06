#-*-coding: utf-8-*-
"""
    @author javiermontoya@unah.hn
    @author fausto.maradiaga@unah.hn
    @version 0.1.6
    @date 2021/04/03
"""

from tkinter import Tk, Label, OptionMenu, StringVar
from Core.Sudoku import SudokuGame, SudokuUI
from Core.User import User
from Core.MySQLEngine import MySQLEngine
import mysql.connector


class LevelSelection:

    def on_closing(self):
        #Se ejecuta consulta a la bitácora para guardar esta acción
        self.engine.insertUpdateDelete(
            "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario sale de la selección de tableros.')"
            .format(self.user.idUser))
        #se cierra la conexión a la base de datos
        self.engine.closeCon()
        #Se destruye la ventana
        self.root.destroy()
        #Se abre la ventana del menu
        from Core.Menu import Menu
        menu = Menu(self.user)

    def __init__(self, user):
        # Usuario.
        self.user = user
        # Se configura una conexion a la base de datos.
        self.engine = MySQLEngine()
        # Se crea una nueva ventana.
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.resizable(0, 0)
        self.root.title("LevelSelection")

        # Se obtienen las coordenadas del centro de la pantalla.
        x = self.root.winfo_screenwidth() // 2 - 400//2
        y = self.root.winfo_screenheight() // 2 - 200//2

        # Se ubica la ventana.
        self.root.geometry("400x200"+"+"+str(x)+"+"+str(y))

        # Este será el valor por defecto de la lista de niveles.
        default = StringVar()
        default.set("")

        # Etiqueta y menú de opciones.
        Label(self.root, text="\n\nSeleccione un tablero:").pack()
        OptionMenu(self.root, default, "debug", "n00b",
                   "l33t", "error", command=self.select).pack()

        self.root.mainloop()

    def select(self, selection):

        # Se crea una nueva ventana.
        root = Tk()
        root.resizable(0,0)

        # Se obtienen las coordenadas del centro de la pantalla.
        x = root.winfo_screenwidth() // 2 - 490 // 2
        y = root.winfo_screenheight() // 2 - 600 // 2

        # Se ubica la ventana.
        root.geometry("490x600"+"+"+str(x)+"+"+str(y))

        # Se ejecuta una consulta para seleccionar el id del tablero y se guarda el resultado.
        result = self.engine.getOne(
            "SELECT id FROM Board WHERE fn_boardName(jso_board) = '{}';"
            .format(selection))

        # Se asigna el id del board.
        idBoard = result[0]

        # Se crea un objeto con el nombre del tablero como parámetro.
        game = SudokuGame(idBoard)

        # Se rellena el tablero.
        game.start()

        # Se dibuja la ventana del juego.
        SudokuUI(root, game, idBoard, self.user)

        # Se destuye la ventana actual.
        self.root.destroy()

        root.mainloop()
