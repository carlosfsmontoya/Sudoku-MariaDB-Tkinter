#-*-coding: utf-8-*-
"""
    @author javiermontoya@unah.hn
    @author fausto.maradiaga@unah.hn
    @version 0.1.10
    @date 2021/04/03
"""

from tkinter import Tk, Canvas, Frame, Label, Button, BOTH, LEFT, RIGHT, TOP, BOTTOM, StringVar, messagebox
from time import time, strftime
from Core.User import User
import time
from Core.MySQLEngine import MySQLEngine
import sys
import io
import json

MARGIN = 20  # Pixels around the board
SIDE = 50  # Width of every board cell.
WIDTH = HEIGHT = MARGIN * 2 + SIDE * 9  # Width and height of the whole board


class SudokuError(Exception):
    """
    An application specific error.
    """
    pass


class SudokuUI(Frame):
    """
    The Tkinter UI, responsible for drawing the board and accepting user input.
    """

    #Funcion que guarda el tiempo invertido cuando se cierra la ventana
    def on_closing(self):
        # Se detiene el cronómetro
        self.i = 0
        # Se ejecuta una consulta para actualizar el tiempo del juego
        self.engine.insertUpdateDelete(
            "UPDATE SudokuGame SET tim_invested='{}' WHERE id={};"
            .format(self.time, self.idGame)
        )
        # Se guarda la acción en la bitácora
        self.engine.insertUpdateDelete(
            "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario sale de un juego de Sudoku.')"
            .format(self.user.idUser)
        )
        # Se cierra la conexión a la base de datos
        self.engine.closeCon()
        # Se destruye la ventana
        self.parent.destroy()
        # Se abre la ventana del menú
        from Core.Menu import Menu
        menu = Menu(self.user)

    def __init__(self, parent, game, idBoard, user):
        # Se configura una conexión a la base de datos
        self.engine = MySQLEngine()

        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.game = game
        self.idBoard = idBoard
        self.user = user
        Frame.__init__(self, parent)

        self.row, self.col = -1, -1

        self.__insertGameRecord()
        self.__initUI()

    # Funcion para insertar registros de Juego

    def __insertGameRecord(self):

        if self.user.status == 1:
            #si el juego se esta reanudando se debe tomar el id del juego y el tiempo guardado para asignarlo a self.idGame y a self.resumedTime respectivamente
            result = self.engine.getOne(
                "SELECT s.id, s.tim_invested FROM UserInformation u INNER JOIN SudokuGame s ON u.id = s.id_user_fk WHERE id_user_fk = {} ORDER BY s.id DESC LIMIT 1"
                .format(self.user.idUser)
            )
            self.idGame = result[0]
            self.resumedTime = result[1].total_seconds()
            #levantamos una bandera que servira para mostrar el tiempo invertido en el juego
            self.resumeTime = True
            #Agregar acción a la bitácora de juego reanudado
            self.engine.insertUpdateDelete(
                "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario reanuda juego.')"
                .format(self.user.idUser)
            )
        else:
            #De lo contrario se debe insertar un nuevo registro y se toma el id del registro recien insertado
            #se inserta un nuevo registro para almacenar datos de cada juego
            self.engine.insertUpdateDelete(
                "INSERT INTO SudokuGame(id_board_fk, id_user_fk) VALUES ({},{})"
                .format(self.idBoard,self.user.idUser)
            )
            #obtenemos el id de juego recien insertado y lo almacenamos
            self.idGame = self.engine.link.lastrowid

            #se actualiza el bit de estado de Juego actual en progreso para este usuario
            self.engine.insertUpdateDelete(
                "UPDATE UserInformation SET bit_status = 1 WHERE id = {};"
                .format(self.user.idUser)
            )
            #Agregar acción a la bitácora de inicio de nuevo juego
            self.engine.insertUpdateDelete(
                "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario inicia nuevo juego.')"
                .format(self.user.idUser)
            )
            #La bandera para reanudar el tiempo sera falsa
            self.resumeTime = False
        #Se actualiza la variable de estado del jugador
        self.user.status = 1
        #Se asigna False a la variable que determina si el usuario ha ganado el juego
        self.win = False

    def __initUI(self):
        self.parent.title("Sudoku")
        self.__draw_time()

        if self.user.status == 1:
            self.__recover_puzzle()

        self.pack(fill=BOTH)

        self.canvas = Canvas(self,
                             width=WIDTH,
                             height=HEIGHT)
        self.canvas.pack(fill=BOTH, side=TOP)
        # Boton 
        pause_button = Button(self,
                               text="Detener",
                               command=self.__stop_game)
        pause_button.pack( side=LEFT)
        finish_button = Button(self,
                               text="Terminar",
                               command=self.__finish_game)
        finish_button.pack( side=RIGHT)
        # El boton de limpiar movimientos ahora regresara un movimiento realizado por el jugador
        clear_button = Button(self,
                              text="Regresar un Movimiento",
                              command=self.__pop_move)
        clear_button.pack(fill=BOTH, side=BOTTOM)

        self.__draw_grid()
        self.__draw_puzzle()

        self.canvas.bind("<Button-1>", self.__cell_clicked)
        self.canvas.bind("<Key>", self.__key_pressed)

    def __recover_puzzle(self): 

        # Se carga el conjunto de movimientos hechos en el juego
        result = self.engine.getAll(
            "SELECT tin_row, tin_column, fn_decrypt_answer(Answer_b) AS value FROM Moveset WHERE id_sudokuGame_fk={};"
            .format(self.idGame)
        )

        # Se posiciona cada respuesta almacenada en su respectivo lugar
        for tin_row, tin_column, value in result:
            self.game.puzzle[tin_row][tin_column] = int(value)

    def __draw_time(self):
        #Variable temporal que obtendrá el tiempo de inicio del juego.
        self.temp = time.time()
        self.time = ""
        self.showTime = Label(self, text=self.time)
        self.showTime.pack()
        #Variable que servirá como interruptor:
        #Mientras esté en 1 el tiempo seguirá en marcha.
        self.i = 1
        self.__get_time()

    def __get_time(self):
        #Variable que obtendrá el tiempo actual.
        self.newtime = time.time()
        #Variable que comenzará con el tiempo en 0 segundos
        self.time = self.newtime - self.temp
        #Si el juego se ha resumido, se sumará el tiempo guardado
        if self.resumeTime:
            self.time += self.resumedTime
        #Será asignado el  formato en HH:MM:SS
        self.time = strftime("%H:%M:%S", time.gmtime(self.time))
        self.showTime.config(text=self.time)
        if(self.i == 1):
            #Se actualiza el tiempo
            self.after_id = self.showTime.after(10, self.__get_time)

    def __draw_grid(self):
        """
        Draws grid divided with blue lines into 3x3 squares
        """
        for i in range(10):
            color = "blue" if i % 3 == 0 else "gray"

            x0 = MARGIN + i * SIDE
            y0 = MARGIN
            x1 = MARGIN + i * SIDE
            y1 = HEIGHT - MARGIN
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

            x0 = MARGIN
            y0 = MARGIN + i * SIDE
            x1 = WIDTH - MARGIN
            y1 = MARGIN + i * SIDE
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

    def __draw_puzzle(self):
        self.canvas.delete("numbers")
        for i in range(9):
            for j in range(9):
                answer = self.game.puzzle[i][j]
                if answer != 0:
                    x = MARGIN + j * SIDE + SIDE / 2
                    y = MARGIN + i * SIDE + SIDE / 2
                    original = self.game.start_puzzle[i][j]
                    color = "black" if answer == original else "sea green"
                    self.canvas.create_text(
                        x, y, text=answer, tags="numbers", fill=color
                    )

    def __draw_cursor(self):
        self.canvas.delete("cursor")
        if self.row >= 0 and self.col >= 0:
            x0 = MARGIN + self.col * SIDE + 1
            y0 = MARGIN + self.row * SIDE + 1
            x1 = MARGIN + (self.col + 1) * SIDE - 1
            y1 = MARGIN + (self.row + 1) * SIDE - 1
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                outline="red", tags="cursor"
            )

    def __draw_victory(self):
        # create a oval (which will be a circle)
        x0 = y0 = MARGIN + SIDE * 2
        x1 = y1 = MARGIN + SIDE * 7
        self.canvas.create_oval(
            x0, y0, x1, y1,
            tags="victory", fill="dark orange", outline="orange"
        )
        # create text
        x = y = MARGIN + 4 * SIDE + SIDE / 2
        self.canvas.create_text(
            x, y,
            text="You win!", tags="victory",
            fill="white", font=("Arial", 32)
        )

        self.i = 0

        # Se crea una transacción de selección de datos.
        board = self.engine.getAll(
            "INSERT INTO Score(id_userInformation_fk, id_board_fk, tim_score) VALUES ({}, {}, '{}');"
            .format(str(self.user.idUser), str(self.idBoard), self.time)
        )

        args = (str(self.user.idUser),)
        self.engine.callSP("sp_deleteScore", args)

        # Se ejecuta una consulta para actualizar el tiempo del juego
        self.engine.insertUpdateDelete(
            "UPDATE SudokuGame SET tim_invested='{}' WHERE id={};"
            .format(self.time, self.idGame)
        )
        # se actualiza el estado del jugador para que ya no reanude juegos
        self.engine.insertUpdateDelete(
            "UPDATE UserInformation SET bit_status=0 WHERE id={}"
            .format(self.user.idUser)
        )
        self.user.status = 0
        self.win = True

    def __cell_clicked(self, event):
        if self.game.game_over:
            return
        x, y = event.x, event.y
        if (MARGIN < x < WIDTH - MARGIN and MARGIN < y < HEIGHT - MARGIN):
            self.canvas.focus_set()

            # get row and col numbers from x,y coordinates
            row, col = int((y - MARGIN) / SIDE), int((x - MARGIN) / SIDE)

            # if cell was selected already - deselect it
            if (row, col) == (self.row, self.col):
                self.row, self.col = -1, -1
            elif self.game.puzzle[row][col] == 0:
                self.row, self.col = row, col
        else:
            self.row, self.col = -1, -1

        self.__draw_cursor()

    def __key_pressed(self, event):

        if self.game.game_over:
            return
        if self.row >= 0 and self.col >= 0 and event.char in "1234567890":
            self.game.puzzle[self.row][self.col] = int(event.char)

            # se apila el movimiento realizado
            self.__push_move(event.char)

            self.col, self.row = -1, -1
            self.__draw_puzzle()
            self.__draw_cursor()
            if self.game.check_win():
                self.__draw_victory()

    def __clear_answers(self):
        self.game.start()
        self.canvas.delete("victory")
        self.__draw_puzzle()

    # esta funcion apilará un movimiento en la pila de movimientos hechos por el jugador
    def __push_move(self, answer):

        # Se crea una transacción de insercion del movimiento.
        # Al momento del llamado de esta funcion, el self contiene la fila y columna
        # en la que se quiere insertar una respuesta
        
        args = (self.idGame, self.row, self.col, answer)
        
        self.engine.callSP("sp_pushMove", args)

    # esta funcion desapila un movimiento realizado por el jugador
    def __pop_move(self):

        # Se crea una transacción para recuperar la posición del último movimiento hecho por el jugador.
        result = self.engine.getAll(
            "SELECT id, tin_row, tin_column FROM Moveset WHERE id_sudokuGame_fk={} ORDER BY id DESC LIMIT 1;".format(self.idGame)
        )
        # Se elimina el último movimiento de la tabla y del tablero
        for id, tin_row, tin_column in result:
            self.engine.insertUpdateDelete(
                "DELETE FROM Moveset WHERE id="+str(id)+";"
            )
            self.game.puzzle[int(tin_row)][int(tin_column)] = 0

        # Se dibuja el puzzle actualizado
        self.__draw_puzzle()

    def __stop_game(self):
        self.on_closing()

    # función para terminar el juego, desplegará un mensaje pidiendo la confirmación del usuario
    def __finish_game(self):
        # Se verifica que el usuario no haya ganado el juego
        if not self.win:
            root = Tk()
            root.withdraw()
            # se debe desplegar un mensaje que pida la confirmacion del usuario
            if messagebox.askokcancel("Terminar como derrota", "Realmente desea terminar el juego? se marcará como una derrota."):
                """ 
                Si se confirma, deben actualizarse en total 3 atributos en 2 tablas distintas: 
                    - SudokuGame(tim_invested, bit_defeated) a (self.time, 1); se accede al registro respectivo con self.user.idGame
                    - UserInformation(bit_status) a (0); se accede al registro respectivo con self.user.idUser
                """
                # Se detiene el cronómetro
                self.i = 0
                # Se ejecuta una consulta para actualizar el tiempo del juego y el bit_defeated
                self.engine.insertUpdateDelete(
                    "UPDATE SudokuGame SET tim_invested='{}', bit_defeated=1 WHERE id={};"
                    .format(self.time, self.idGame)
                )
                #Agregar acción a la bitácora de Juego terminado como derrota
                self.engine.insertUpdateDelete(
                    "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario marca como derrota juego #{}.')"
                    .format(self.user.idUser, self.idGame)
                )

                # Se actualiza el atributo bit_status del Usuario
                self.engine.insertUpdateDelete(
                    "UPDATE UserInformation SET bit_status=0 WHERE id={}"
                    .format(self.user.idUser)
                )
                self.user.status = 0
                # Se cierra la base de datos
                self.engine.closeCon()

                #se desplegara un nuevo mensaje ofreciendo iniciar un nuevo juego en el mismo tablero o en un tablero distinto
                if messagebox.askokcancel("Iniciar un nuevo juego","Desea iniciar un juego en el mismo tablero?"):
                    # Si acepta, se inicia un nuevo juego en un tablero idéntico
                    # Se crea un objeto con el identificador del tablero actual como parámetro.
                    game = SudokuGame(self.idBoard)
                    # Se inicializa el tablero.
                    game.start()
                    # Se dibuja la ventana del juego.
                    SudokuUI(self.parent, game, self.idBoard, self.user)
                    #se cierra la ventana del dialogbox
                    root.destroy()
                    #se destruye esta instancia de la UI
                    self.destroy()

                else:
                    if messagebox.askokcancel("Iniciar un nuevo juego","Desea iniciar un juego en un tablero distinto?"):
                        # Si acepta se desplega la ventana de selección de niveles
                        root.destroy()
                        self.parent.destroy()
                        from Core.LevelSelection import LevelSelection
                        levelSelection = LevelSelection(self.user)
                    else:
                        # Si no acepta se retorna el jugador al Menú
                        root.destroy()
                        self.parent.destroy()
                        from Core.Menu import Menu
                        menu = Menu(self.user)
            else:
                # Se elimina la ventana del dialog box
                root.destroy()
        
class SudokuBoard:
    """
    Sudoku Board representation
    """

    def __init__(self, board_file):
        self.board = self.__create_board(board_file)

    def __create_board(self, board_file):

        #Se configura una conexión a la base de datos
        engine = MySQLEngine()

        # Se crea una transacción de selección de datos.
        result = engine.getOne(
            "SELECT fn_jsonBoard(jso_board) FROM Board WHERE id = {};"
            .format(board_file)
        )
        # se carga el arreglo bidimensional (retornado como string por SQL)
        board = json.loads(result[0])
        # se cierra la conexión a la base de datos
        engine.closeCon()

        if len(board) != 9:
            raise SudokuError("Each sudoku puzzle must be 9 lines long")
        return board


class SudokuGame(object):
    """
    A Sudoku game, in charge of storing the state of the board and checking
    whether the puzzle is completed.
    """

    def __init__(self, board_file):
        self.board_file = board_file
        self.start_puzzle = SudokuBoard(board_file).board

    def start(self):
        self.game_over = False
        self.puzzle = []
        for i in range(9):
            self.puzzle.append([])
            for j in range(9):
                self.puzzle[i].append(self.start_puzzle[i][j])

    def check_win(self):
        for row in range(9):
            if not self.__check_row(row):
                return False
        for column in range(9):
            if not self.__check_column(column):
                return False
        for row in range(3):
            for column in range(3):
                if not self.__check_square(row, column):
                    return False
        self.game_over = True
        return True

    def __check_block(self, block):
        return set(block) == set(range(1, 10))

    def __check_row(self, row):
        return self.__check_block(self.puzzle[row])

    def __check_column(self, column):
        return self.__check_block(
            [self.puzzle[row][column] for row in range(9)]
        )

    def __check_square(self, row, column):
        return self.__check_block(
            [
                self.puzzle[r][c]
                for r in range(row * 3, (row + 1) * 3)
                for c in range(column * 3, (column + 1) * 3)
            ]
        )
