from djitellopy import Tello
import cv2
import time
import tkinter as tk
from PIL import Image, ImageTk

# Tamaño del video en la interfaz
width, height = 640, 480

# Inicializa el dron
drone = Tello()

# Establece conexión de Wifi
drone.connect()

# Inicia el stream de video
drone.streamoff()
drone.streamon()
time.sleep(3)

# Revisa el estado de la batería
print(f'Batería: {drone.get_battery()}%')

# Variable global de estado de vuelo
flying = False

# Crear ventana principal de Tkinter
root = tk.Tk()
root.title("Drone Camera")

# Crear un label para mostrar el video
label = tk.Label(root)
label.pack()

# Variables de movimiento
lr_vel = 0
fb_vel = 0
ud_vel = 0
yaw_vel = 0

# Altura máxima permitida en cm
MAX_HEIGHT_CM = 300

def clean_exit():
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

def draw_help(frame):
    """
    Dibuja el panel de ayuda con los controles sobre el frame.
    """
    lines = [
        "Controles:",
        "W/S: Adelante / Atrás",
        "A/D: Izquierda / Derecha",
        "↑/↓: Subir / Bajar",
        "←/→: Girar izq / der",
        "R: Despegar   F: Aterrizar   M: Salir",
        "I/K/J/L: Flips (adelante / atrás / izq / der)"
    ]
    y = 100
    for line in lines:
        cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 255, 255), 1)
        y += 18

def update_frame():
    global fb_vel, lr_vel, ud_vel, yaw_vel, flying
    try:
        frame = drone.get_frame_read().frame
        frame = cv2.resize(frame, (width, height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        bateria = drone.get_battery()
        altura = drone.get_height()
        estado = "Volando" if flying else "Detenido"

        cv2.putText(frame, f'Bateria: {bateria}%', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Altura: {altura}cm', (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Estado: {estado}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        draw_help(frame)

        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)

        if flying and bateria <= 10:
            print("\nAdvertencia: Batería baja (<=10%). Aterrizando...")
            drone.land()
            flying = False

        if flying:
            if lr_vel == 0 and fb_vel == 0 and ud_vel == 0 and yaw_vel == 0:
                drone.send_rc_control(0, 0, 0, 0)
            else:
                drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        label.after(30, update_frame)

    except Exception as e:
        print(f"Error al actualizar frame: {e}")
        clean_exit()

def key_press(event):
    global flying, fb_vel, lr_vel, ud_vel, yaw_vel
    key = event.keysym.lower()

    if key == 'm':
        print("\nTecla M presionada. Saliendo del programa...")
        clean_exit()

    elif key == 'r':
        if not flying:
            if drone.get_battery() <= 15:
                print("\nAdvertencia: Batería demasiado baja para despegar (<=15%).")
                return
            print("Despegando...")
            drone.takeoff()
            flying = True

    elif key == 'f':
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
    elif key == 'up':
        if drone.get_height() < MAX_HEIGHT_CM:
            ud_vel = 60
        else:
            print("\nAdvertencia: Altura máxima alcanzada (3m). No se puede subir más.")
            ud_vel = 0
    elif key == 'down':
        ud_vel = -60
    elif key == 'right':
        yaw_vel = 60
    elif key == 'left':
        yaw_vel = -60

    # Flips
    elif key == 'i':
        if flying:
            print("Flip hacia adelante")
            drone.flip_forward()
    elif key == 'k':
        if flying:
            print("Flip hacia atrás")
            drone.flip_back()
    elif key == 'j':
        if flying:
            print("Flip a la izquierda")
            drone.flip_left()
    elif key == 'l':
        if flying:
            print("Flip a la derecha")
            drone.flip_right()

def key_release(event):
    global fb_vel, lr_vel, ud_vel, yaw_vel
    key = event.keysym.lower()
    if key in ['w', 's']:
        fb_vel = 0
    elif key in ['a', 'd']:
        lr_vel = 0
    elif key in ['up', 'down']:
        ud_vel = 0
    elif key in ['right', 'left']:
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
