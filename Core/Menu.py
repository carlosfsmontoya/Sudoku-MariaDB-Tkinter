# -*-coding: utf-8-*-
"""
    @author javiermontoya@unah.hn
    @author fausto.maradiaga@unah.hn
    @version 0.1.5
    @date 2021/04/02
"""

from tkinter import Tk, Label, Button, messagebox
from Core.ManageUser import ManageUser
from Core.Binnacle import Binnacle
from Core.LevelSelection import LevelSelection
from Core.ScoreTable import ScoreTable
from Core.Sudoku import SudokuGame, SudokuUI
from Core.User import User
from Core.MySQLEngine import MySQLEngine
from functools import partial

class Menu:

    def on_closing(self):
        # Se ejecuta una consulta a la bitácora para guardar esta acción.
        self.engine.insertUpdateDelete(
            "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario sale del sistema.')"
            .format(self.user.idUser))

        # Se cierra la base de datos.
        self.engine.closeCon()

        # Se destruye la ventana.
        self.root.destroy()

    def __init__(self, user):
        # Se configura una conexión a la base de datos.
        self.engine = MySQLEngine()

        # Se asigna el objeto Usuario
        self.user = user

        # Se crea una nueva ventana.
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.resizable(0, 0)
        self.root.title("Menu")

        # Se obtienen las coordenadas del centro de la pantalla.
        x = self.root.winfo_screenwidth() // 2 - 400//2
        y = self.root.winfo_screenheight() // 2 - 250//2

        # Se ubica la ventana.
        self.root.geometry("400x250"+"+"+str(x)+"+"+str(y))

        # Si el usuario es administrador dispondrá de dos opciones adicionales.
        # Botón para acceder al CRUD.
        if(self.user.role == 1):
            manage = partial(self.manage, self.user)
            Label(self.root, text="").pack()
            Button(self.root, text="Administrar usuarios", command=manage).pack()

        # Botón para acceder a la Bitácora.
        if(self.user.role == 1):
            binnacle = partial(self.binnacle, self.user)
            Label(self.root, text="").pack()
            Button(self.root, text="Ver Bitácora", command=binnacle).pack()

        # Botón para iniciar un nuevo juego.
        Label(self.root, text="").pack()
        play = partial(self.play, self.user)
        Button(self.root, text="Iniciar un nuevo juego", command=play).pack()

        # Botón para reanudar un juego
        if(self.user.status == 1):
            Label(self.root, text="").pack()
            resume = partial(self.resume, self.user)
            Button(self.root, text="Reanudar juego", command=resume).pack()

        # Botón para ver los puntajes.
        Label(self.root, text="").pack()
        score = partial(self.score, self.user)
        Button(self.root, text="Scores", command=score).pack()

        self.root.mainloop()

    # Administrar usuarios.
    def manage(self, user):

        # Se destruye la ventana actual
        self.root.destroy()

        # Se accede al CRUD.
        manageUser = ManageUser(user)


    # Ver bitácora.
    def binnacle(self, user):

        # Se destruye la ventana actual
        self.root.destroy()

        # Se accede a la bitácora.
        binnacle = Binnacle(user)


    # Iniciar un nuevo juego.
    def play(self, user):

        # Si el usuario tiene un juego en progreso debe pedirse confirmación para eliminarlo.
        if user.status == 1:
            if messagebox.askokcancel("Quit", "¿Desea comenzar un nuevo juego?\nEl juego guardado se marcará como derrota."):
                # Se marca como derrota el juego que este en progreso
                # El juego que está en progreso es el último creado por el jugador, ya que un usuario solamente puede tener un juego en progreso
                # y este permanecerá en este estado hasta que se complete el juego o se finalice como derrota.

                # Se crean los argumentos para llamar un procedimiento almacenado.
                args = (user.idUser,)

                # Se llama al procedimiento almacenado.
                self.engine.callSP('sp_updateStatus', args)

                # Se cierra la conexión a la base de datos
                self.engine.closeCon()

                # Se actualiza el estado del usuario
                user.status = 0

                # Se destruye la ventana actual.
                self.root.destroy()

                # Se accede a la selección de niveles con usuario como parámetro.
                levelSelection = LevelSelection(user)
        else:
            # Se destruye la ventana actual.
            self.root.destroy()

            # Se accede a la selección de niveles con el usuario como parámetro.
            levelSelection = LevelSelection(user)

    def resume(self, user):

        # Se crea una nueva ventana.
        root = Tk()
        root.resizable(0, 0)

        # Se obtienen las coordenadas del centro de la pantalla.
        x = root.winfo_screenwidth() // 2 - 490 // 2
        y = root.winfo_screenheight() // 2 - 600 // 2

        # Se ubica la ventana.
        root.geometry("490x600"+"+"+str(x)+"+"+str(y))

        # Se ejecuta una consulta para tomar el id del board del juego que se quiere reanudar
        # Guardamos el resultado.
        result = self.engine.getOne("SELECT fn_selectBoard({})".format(user.idUser))

        # Guardamos el id del board.
        idBoard = result[0]

        # Cerramos la conexión.
        self.engine.closeCon()

        # Se crea un objeto con el nombre del tablero como parámetro.
        game = SudokuGame(idBoard)

        # Se rellena el tablero.
        game.start()

        # Se dibuja la ventana del juego.
        SudokuUI(root, game, idBoard, user)

        # Se destuye la ventana actual.
        self.root.destroy()

        root.mainloop()

    def score(self, user):

        # Se destruye la ventana actual.
        self.root.destroy()

        # Se accede a la tabla de scores con el usuario como parámetro.
        scoreTable = ScoreTable(user)
