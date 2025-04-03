from djitellopy import tello
import cv2
import time
import tkinter as tk
from PIL import Image, ImageTk

# Configuración del tamaño del video
width, height = 320, 240

# Inicializar el dron
drone = tello.Tello()
drone.connect()

# Iniciar el stream de video
drone.streamoff()
drone.streamon()

# Crear la ventana principal
root = tk.Tk()
root.title("Drone Camera")

# Crear un label para mostrar el video
label = tk.Label(root)
label.pack()

def update_frame():
    # Leer el frame del dron
    frame_read = drone.get_frame_read()
    frame = frame_read.frame
    frame = cv2.resize(frame, (width, height))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convertir a RGB para PIL

    # Convertir a imagen compatible con Tkinter
    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)

    # Mostrar la imagen
    label.imgtk = imgtk
    label.configure(image=imgtk)

    # Llamar de nuevo a esta función después de 30ms
    label.after(30, update_frame)

# Iniciar el loop de actualización de video
update_frame()

# Iniciar el loop principal de Tkinter
root.mainloop()
