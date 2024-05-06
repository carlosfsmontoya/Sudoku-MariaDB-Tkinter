#-*-coding: utf-8-*-
'''
    @author ggomezg@unah.hn
    @version 0.1.0
    @date 2021/04/24
'''
from tkinter import Tk, Label, ttk, CENTER, END
from Core.User import User
from Core.MySQLEngine import MySQLEngine

class Binnacle:

    def on_closing(self):
        #Se ejecuta una consulta a la bitácora para guardar esta acción
        self.engine.insertUpdateDelete(
            "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Sale de visualizar bitácora.')"
            .format(self.user.idUser)
        )
        #Cerramos la conexión a la base de datos
        self.engine.closeCon()
        # Se destruye la ventana de bitácora
        self.root.destroy()
        # Se abre la ventana del Menu
        from Core.Menu import Menu
        menu = Menu(self.user)
    
    def __init__(self, user):
        #Se asigna el objeto Usuario
        self.user = user

        # Se crea una nueva ventana.
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # self.root.resizable(0, 0)
        self.root.title("Bitácora")

        # Se obtienen las coordenadas del centro de la pantalla.
        x = self.root.winfo_screenwidth() // 2 - 800//2
        y = self.root.winfo_screenheight() // 2 - 400//2

        # Se ubica la ventana.
        self.root.geometry("800x400"+"+"+str(x)+"+"+str(y))

        # Generar una conexión.
        self.engine = MySQLEngine()

        #Insertamos en la bitácora esta acción
        self.engine.insertUpdateDelete(
            "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Visualización de bitácora.')"
            .format(self.user.idUser)
        )

        # Se realiza una consulta y se guarda el resultado de la transacción.
        result = self.engine.getAll("SELECT id_user_fk, tex_description, dat_on FROM Log;")
        #Se inicializa un contador de entradas a la bitácora
        i = 0
        # Se crea una tabla.
        self.table = ttk.Treeview(self.root, columns=('#1', '#2', '#3', '#4'))
        self.table.pack()

        # Crear un scrollbar para mover la lista
        self.scroll = ttk.Scrollbar(self.root, orient="horizontal", command=self.table.yview)
        # Mostrar el scrollbar.
        self.scroll.pack()
        
        self.table['show'] = 'headings'
        self.table.heading("#1", text="No. de Fila", anchor=CENTER)
        self.table.heading("#2", text="ID de Usuario", anchor=CENTER)
        self.table.heading("#3", text="Descripción", anchor=CENTER)
        self.table.heading("#4", text="Fecha y Hora", anchor=CENTER)

        for id_user_fk, tex_description, dat_on in result:
            i = i + 1
            self.table.insert("", END, values=[i, id_user_fk, tex_description, dat_on])
