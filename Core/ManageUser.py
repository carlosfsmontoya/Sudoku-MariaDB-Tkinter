# -*-coding: utf-8-*-
"""
    @author javiermontoya@unah.hn
    @author fausto.maradiaga@unah.hn
    @version 0.1.5
    @date 2021/04/05
"""

from tkinter import Tk, Label, Entry, Button, Listbox, StringVar, ttk, Scrollbar, CENTER, END
from functools import partial
from Core.User import User
from Core.MySQLEngine import MySQLEngine
import mysql.connector


class ManageUser:

    def on_closing(self):
        # Se ejecuta una consulta a la bitácora para guardar esta acción.
        self.engine.insertUpdateDelete(
            "INSERT INTO Log(id_user_fk, tex_description) VALUES({},'Usuario sale de la ventana de administrar usuarios.')"
            .format(self.user.idUser))

        # Se cierra la base de datos.
        self.engine.closeCon()
        # Se destruye la ventana.
        self.root.destroy()
        # Se abre la ventana del Menu.
        from Core.Menu import Menu
        menu = Menu(self.user)

    def __init__(self, user):
        # Se asigna el objeto Usuario.
        self.user = user
        
        # Se configura una conexión a la base de datos.
        self.engine = MySQLEngine()

        # Se crea una nueva ventana.
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        #self.root.resizable(0, 0)
        self.root.title("Tareas de administración")

        # Se obtienen las coordenadas del centro de la pantalla.
        x = self.root.winfo_screenwidth() // 2 - 800//2
        y = self.root.winfo_screenheight() // 2 - 650//2

        # Se ubica la ventana.
        self.root.geometry("800x650"+"+"+str(x)+"+"+str(y))

        # Etiqueta y caja de texto para el usuario.
        username = StringVar()
        Label(self.root, text="\nUsuario:").pack()
        Entry(self.root, textvariable=username).pack()

        # Etiqueta y caja de texto para la contraseña.
        password = StringVar()
        Label(self.root, text="Contraseña:").pack()
        Entry(self.root, textvariable=password).pack()

        # Se congela y almacena la función.
        createUser = partial(self.createUser, username, password)
        deleteUser = partial(self.deleteUser, username, password)
        updateUser = partial(self.updateUser, username, password)

        Label(self.root, text="").pack()

        # Botón que tendrá la función de crear usuarios.
        Button(self.root, text="Crear usuario", command=createUser).pack()

        # Botón que tendrá la función de actualizar usuarios.
        Button(self.root, text="Actualizar usuario", command=updateUser).pack()

        # Botón que tendrá la función de eliminar usuarios.
        Button(self.root, text="Borrar usuario", command=deleteUser).pack()

        # Esta variable y etiqueta mostrarán mensajes de error.
        self.textError = StringVar()
        Label(self.root, textvariable=self.textError, fg="red").pack()

        # Esta variable y etiqueta mostrarán mensajes de éxito.
        self.textSuccess = StringVar()
        Label(self.root, textvariable=self.textSuccess, fg="green").pack()

        Label(self.root, text="_______________________________________").pack()

        # Variable, etiqueta, caja de texto y botón para buscar.
        self.search = StringVar()
        Label(self.root, text="\nIngrese una coincidencia a buscar:").pack()
        Entry(self.root, textvariable=self.search).pack()
        self.search.trace('w', self.searchUser)

        # Se crea un tree.
        self.table = ttk.Treeview(self.root, columns=('#1', '#2', '#3', "#4"))
        
        # Mostrar el tree.
        self.table.pack()

        # Crear un scrollbar para mover la lista
        self.scroll = ttk.Scrollbar(self.root, orient="horizontal", command=self.table.yview)

        # Mostrar el scrollbar.
        self.scroll.pack()

        # Evento doble click izquierdo.
        self.table.bind("<Double-Button-1>", self.selectColumn)

        # Estructura del tree.
        self.table['show'] = 'headings'
        self.table.heading("#1", text="ID", anchor=CENTER)
        self.table.heading("#2", text="Usuario", anchor=CENTER)
        self.table.heading("#3", text="Contraseña", anchor=CENTER)
        self.table.heading("#4", text="Rol", anchor=CENTER)

        scrollbar = Scrollbar(self.root)
        # Variables temporales.
        self.textUpdate = StringVar()
        self.oldId = StringVar()
        self.oldUsername = StringVar()
        self.oldPassword = StringVar()

        Label(self.root, text="Seleccione un registro para actualizarlo: {}".format(
            self.oldId.get())).pack()
        Label(self.root, textvariable=self.textUpdate, fg="green").pack()

        # Se recuperan los registros para mostrarlos en la tabla.
        self.updateTable()

        self.root.mainloop()

    def searchUser(self, name, index, mode):

        # Se eliminan los registros del tree para no tener registros repetidos.
        tmp = self.table.get_children()
        for i in tmp:
            self.table.delete(i)

        # Se realiza una transacción para obtener los registros actualizados en la tabla.
        if (self.search.get() != ""):
            
            self.result = self.engine.getAll("SELECT id, IF(id_rol_fk = 1, 'admin', 'player') AS 'tex_rol', tex_user, tex_password FROM UserInformation WHERE bit_enable = 1 HAVING id REGEXP '{}' OR tex_user REGEXP '{}' OR tex_password REGEXP '{}' OR tex_user REGEXP '{}' OR tex_rol REGEXP '{}';".format(
                self.search.get(), self.search.get(), self.search.get(), self.search.get(), self.search.get()))

        else:
            self.connection(
                )
            self.result = self.engine.getAll("SELECT id, IF(id_rol_fk = 1, 'admin', 'player') AS 'tex_rol', tex_user, tex_password FROM UserInformation WHERE bit_enable = 1;")

        # Se muestran los registros en la tabla.
        for id, tex_rol, tex_user, tex_password, in self.result:
            self.table.insert(
                "", END, values=[id, tex_user, tex_password, tex_rol])

    def createUser(self, username, password):

        self.textSuccess.set("")

        # Se verifica que los campos no estén vacíos.
        if((username.get() and password.get()) != ""):

            # Se crea una transacción que llamará a una función, esta función devolverá:
            # - 0, si el usuario no existe.
            # - 1, si el usuario si existe.
            
            self.result = self.engine.getAll("SELECT fn_searchUser('{}')".format(username.get()))

            # Si el usuario ya existe no se ingresará.
            if(self.result[0][0] == 1):
                self.textError.set("El usuario que intenta crear ya existe.")

            else:
                # Se crea la transacción.
                self.result = self.engine.insertUpdateDelete("INSERT INTO UserInformation(tex_user, tex_password, id_rol_fk) VALUES('{}', '{}', 2);".format(
                    username.get(), password.get()))

                # Se actualizan los registros en la tabla.
                self.updateTable()

                self.textSuccess.set(
                    "Se creó el usuario {} exitosamente.".format(username.get()))

                # Se limpian las entradas de texto y los mensajes.
                username.set("")
                password.set("")
                self.textError.set("")

        else:
            self.textError.set("No puede ingresar registros en blanco.")

    def updateUser(self, username, password):

        self.textSuccess.set("")

        # Se verifica que los campos no estén vacíos.
        if((self.oldUsername.get() and self.oldPassword.get()) != ""):

            # Se crea una transacción que llamará a una función, esta función devolverá:
            # - 0, si el usuario no existe.
            # - 1, si el usuario si existe.
            self.result = self.engine.getAll("SELECT fn_searchUser('{}')".format(username.get()))

            # Si el usuario ya existe no se actualizará.
            if((username.get() and password.get()) == "" or self.result[0][0] == 1):
                self.textError.set(
                    "No puede ingresar registros en blanco o usuario que ya existan.")

            else:
                # Se hace la tranasacción de actualización.
                self.engine.insertUpdateDelete("UPDATE UserInformation SET tex_user = '{}', tex_password ='{}' WHERE id = {};".format(username.get(
                ), password.get(), self.oldId.get()))

                # Se actualizan los registros en la tabla.
                self.updateTable()

                self.textSuccess.set("Se actualizó el registo 'username: {}', 'password: {}' a 'username: {}', 'password: {}'".format(
                    self.oldUsername.get(), self.oldPassword.get(), username.get(), password.get()))

                # Se limpian las entradas de texto y los mensajes.
                username.set("")
                password.set("")
                self.oldId.set("")
                self.oldUsername.set("")
                self.oldPassword.set("")
                self.textUpdate.set("")
                self.textError.set("")
                self.textError.set("")

        else:
            self.textError.set("No ha seleccionado un registro.")

    def deleteUser(self, username, password):

        self.textSuccess.set("")

        # Se verifica que los campos no estén vacíos.
        if((username.get() and password.get()) != ""):

            # Se crea una transacción que llamará a una función, esta función devolverá:
            # - 0, si el usuario no existe.
            # - 1, si el usuario si existe.
            self.result = self.engine.getAll("SELECT fn_searchUser('{}')".format(username.get()))

            # Verificar que el usuario exista.
            if(self.result[0][0] != 1):
                self.textError.set("El usuario que intenta borrar no existe.")

            else:

                # Se verifica que el usuario ingresado no sea admin, para evitar borrar el admin.
                self.result = self.engine.getAll(
                    "SELECT id_rol_fk FROM UserInformation WHERE tex_user = '{}' AND tex_password ='{}';"
                    .format(username.get(), password.get()))

                if(self.result[0][0] != 1):

                    # Se realiza la transacción.
                    # Aquí con el grupo se consideró el aspecto de que los usuarios eliminados persistan, por este motivo
                    # Se decidió implementar que los usuarios sean deshabilitados.
                    self.engine.insertUpdateDelete(
                        "UPDATE UserInformation SET bit_enable = 0 WHERE tex_user = '{}' AND tex_password ='{}';"
                        .format(username.get(), password.get()))

                    # Se actualizan los registros en la tabla.
                    self.updateTable()

                    # Se envía un mensaje de éxito.
                    self.textSuccess.set(
                        "Se eliminó el usuario {} exitosamente.".format(username.get()))

                    # Se limpian las entradas de texto y los mensajes.
                    username.set("")
                    password.set("")

                else:
                    self.textError.set(
                        "No puede borrar el usuario administrador.")
        else:
            self.textError.set("No se pueden borrar registros en blanco.")

    def updateTable(self):

        # Limpiamos los registros de la tabla para que no se duplique la información.
        tmp = self.table.get_children()
        for i in tmp:
            self.table.delete(i)

        # Se realiza una transacción.
        self.result = self.engine.getAll(
            "SELECT id, tex_user, tex_password, IF(id_rol_fk = 1, 'admin', 'player') AS 'tex_rol' FROM UserInformation WHERE bit_enable = 1;")

        # Se muestran los registros en la tabla.
        for id, tex_user, tex_password, tex_rol in self.result:
            self.table.insert(
                "", END, values=[id, tex_user, tex_password, tex_rol])

    def selectColumn(self, event):

        # Se capturará una excepción para sobrellevar el caso en el que no se seleccioné un registro en el rango de la lista.
        try:
            # Obtenemos los valores seleccionados en el tree.
            self.oldId.set(self.table.item(
                self.table.selection())["values"][0])
            self.oldUsername.set(self.table.item(
                self.table.selection())["values"][1])
            self.oldPassword.set(self.table.item(
                self.table.selection())["values"][2])

        except:
            pass

        self.textUpdate.set("Ingrese nuevos valores para \n id: {}, username: {}, password: {}".format(
            self.oldId.get(), self.oldUsername.get(), self.oldPassword.get()))

