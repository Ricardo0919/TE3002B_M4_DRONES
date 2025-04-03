from djitellopy import Tello
import cv2
import time
import tkinter as tk
from PIL import Image, ImageTk

# Tamaño del video en la interfaz
width, height = 320, 240

# Inicializa el dron
drone = Tello()

# Establece conexión de Wifi
drone.connect()

# Inicia el stream de video
drone.streamoff()  # Asegura que el stream se reinicie
drone.streamon()
time.sleep(3)

# Revisa el estado de la batería
print(f'Bateria: {drone.get_battery()}%')

# Iniciar la variable global de estado de vuelo
flying = False

# Crear ventana principal de Tkinter
root = tk.Tk()
root.title("Drone Camera")

# Crear un label para mostrar el video
label = tk.Label(root)
label.pack()

# Variables de movimiento
lr_vel = 0  # izquierda/derecha (left/right)
fb_vel = 0  # adelante/atrás (forward/backward)
ud_vel = 0  # arriba/abajo (up/down)
yaw_vel = 0  # giro (yaw)

# Altura máxima permitida en cm (3 metros)
MAX_HEIGHT_CM = 300


def clean_exit():
    """
    Función para cerrar correctamente el programa y detener el dron.
    """
    global flying
    print("\nInterrupción detectada. Cerrando el programa...")
    print("\nDeteniendo el dron...")
    if flying:
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(0.5)
        drone.land()
        flying = False
    drone.streamoff()
    drone.end()
    print("Programa cerrado correctamente.")
    root.destroy()


def update_frame():
    """
    Función que actualiza el frame en la interfaz de Tkinter.
    También verifica batería baja durante el vuelo.
    """
    global fb_vel, lr_vel, ud_vel, yaw_vel, flying
    try:
        # Obtener el frame del dron
        frame = drone.get_frame_read().frame

        # Redimensionar y convertir a RGB
        frame = cv2.resize(frame, (width, height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Obtener datos
        bateria = drone.get_battery()
        altura = drone.get_height()
        estado = "Volando" if flying else "Detenido"

        # Mostrar datos en el frame
        cv2.putText(frame, f'Bateria: {bateria}%', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Altura: {altura}cm', (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Estado: {estado}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Convertir el frame a formato compatible con Tkinter
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)

        # Mostrar la imagen en el label
        label.imgtk = imgtk
        label.configure(image=imgtk)

        # Verificar batería durante el vuelo
        if flying and bateria <= 10:
            print("\nAdvertencia: Batería baja (<=10%). Aterrizando...")
            drone.land()
            flying = False

        # Enviar comandos de movimiento si está volando
        if flying:
            drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        # Llamar esta función de nuevo en 30ms
        label.after(30, update_frame)
    except Exception as e:
        print(f"Error al actualizar frame: {e}")
        clean_exit()


def key_press(event):
    """
    Función que detecta las teclas presionadas para controlar el dron.
    """
    global flying, fb_vel, lr_vel, ud_vel, yaw_vel

    key = event.char.lower()

    if key == 'm':  # Tecla ESC para salir
        print("\nTecla ESC presionada. Saliendo del programa...")
        clean_exit()

    elif key == 't':
        if not flying:
            if drone.get_battery() <= 15:
                print("\nAdvertencia: Batería demasiado baja para despegar (<=15%).")
                return
            print("Despegando...")
            drone.takeoff()
            flying = True

    elif key == 'l':
        if flying:
            print("Aterrizando...")
            drone.send_rc_control(0, 0, 0, 0)
            time.sleep(0.5)
            drone.land()
            flying = False

    elif key == 'w':
        fb_vel = 60
    elif key == 's':
        fb_vel = -60
    elif key == 'a':
        lr_vel = -60
    elif key == 'd':
        lr_vel = 60
    elif key == 'r':
        if drone.get_height() < MAX_HEIGHT_CM:
            ud_vel = 60
        else:
            print("\nAdvertencia: Altura máxima alcanzada (3m). No se puede subir más.")
            ud_vel = 0
    elif key == 'f':
        ud_vel = -60
    elif key == 'e':
        yaw_vel = 60
    elif key == 'q':  # Ahora solo gira, ya no sale
        yaw_vel = -60


def key_release(event):
    """
    Función para detener el movimiento al soltar la tecla.
    """
    global fb_vel, lr_vel, ud_vel, yaw_vel
    key = event.char.lower()
    if key in ['w', 's']:
        fb_vel = 0
    elif key in ['a', 'd']:
        lr_vel = 0
    elif key in ['r', 'f']:
        ud_vel = 0
    elif key in ['e', 'q']:
        yaw_vel = 0

# Enlazar eventos de teclado
root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)

# Ejecutar el stream de video en la ventana
update_frame()

# Iniciar el bucle principal de la GUI
try:
    root.mainloop()
except KeyboardInterrupt:
    clean_exit()
