# -*-coding: utf-8-*-
"""
    @author javiermontoya@unah.hn
    @version 0.1.0
    @date 2021/04/08
"""

from tkinter import Tk, Label, ttk, CENTER, END
from Core.User import User
from Core.MySQLEngine import MySQLEngine


class ScoreTable:

    def on_closing(self):
        # Se destrue la ventana
        self.root.destroy()
        # Aca se puede ejecutar una consulta a la bitácora para guardar esta acción
        self.engine.insertUpdateDelete(
            "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario deja de visualizar Scores.');"
            .format(self.user.idUser))
        #Se cierra la conexion a la base de datos
        self.engine.closeCon()

        from Core.Menu import Menu
        menu = Menu(self.user)
        

    def __init__(self, user):
        # Se instancia una conexion a la base de datos.
        self.engine = MySQLEngine()

        # Se asigna el objeto Usuario
        self.user = user
        #Se inserta la accion a la bitácora
        self.engine.insertUpdateDelete(
            "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario entra a visualizar Scores.');"
            .format(self.user.idUser))
        # Se crea una nueva ventana.
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.resizable(0, 0)
        self.root.title("Puntajes")

        # Se obtienen las coordenadas del centro de la pantalla.
        x = self.root.winfo_screenwidth() // 2 - 800//2
        y = self.root.winfo_screenheight() // 2 - 400//2

        # Se ubica la ventana.
        self.root.geometry("800x400"+"+"+str(x)+"+"+str(y))

        # Guardamos el resultado de la transacción.
        result = self.engine.getAll(
            "SELECT tim_date, tim_score, tex_tableName FROM vw_allScores WHERE id_user = {} LIMIT 10;"
            .format(self.user.idUser)
        )
        i = 0
        # Se crea una tabla.
        self.table = ttk.Treeview(self.root, columns=('#1', '#2', '#3', "#4"))
        self.table.pack()
        self.table['show'] = 'headings'
        self.table.heading("#1", text="Posición", anchor=CENTER)
        self.table.heading("#2", text="Tiempo", anchor=CENTER)
        self.table.heading("#3", text="Tablero", anchor=CENTER)
        self.table.heading("#4", text="Fecha", anchor=CENTER)

        # Se insertan los datos en el tree.
        for tim_date, tim_score, tex_tableName in result:
            i = i + 1
            self.table.insert(
                "", END, values=[i, tim_score, tex_tableName, tim_date])

