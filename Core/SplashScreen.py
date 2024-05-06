#-*-coding: utf-8-*-
"""
    @author javiermontoya@unah.hn
    @version 0.1.0
    @date 2021/03/30
"""

from tkinter import Tk, Canvas, PhotoImage

class SplashScreen:

    def __init__(self):

        root = Tk()

        #Se ocultan las opciones de ventana.
        root.overrideredirect(True)

        #Se obtiene el tamaño de la pantalla.
        width = root.winfo_screenwidth() // 2
        height = root.winfo_screenheight() // 2

        #Se obtienen las coordenadas del centro de la pantalla.
        x = root.winfo_screenwidth() // 2 - width // 2
        y = root.winfo_screenheight() // 2 - height // 2

        #Se ubica la ventana
        root.geometry(str(width)+"x"+str(height)+"+"+str(x)+"+"+str(y))

        #Se guarda la imagen en una variable.
        image = PhotoImage(file="Core//images//splashScreen.gif")
        image = image.subsample(2, 2) 

        #Se construye el lienzo.
        canvas = Canvas(root, height=height, width=width, bg="black")

        #Se muestra la imagen.
        canvas.create_image(x, y, image=image)
        canvas.pack()

        #Se muestra la ventana splash screen por 1500 milisegundos y después se destruye.
        root.after(1500, root.destroy)

        root.mainloop()