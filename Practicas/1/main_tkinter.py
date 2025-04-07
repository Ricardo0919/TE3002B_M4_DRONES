"""
Práctica 1: Movimientos Básicos
Implementación de Robótica Inteligente

Alumnos:
    Jonathan Arles Guevara Molina    A01710380
    Ezzat Alzahouri Campos           A01710709
    José Ángel Huerta Ríos           A01710607
    Ricardo Sierra Roa              A01709887

Profesor:
    Josué González García

Fecha de entrega:
    7 de abril de 2025
"""

from djitellopy import Tello
import cv2
import time
import tkinter as tk
from PIL import Image, ImageTk

# Configuración del tamaño de la ventana de video
width, height = 320, 240

# Inicialización y conexión con el dron
drone = Tello()
drone.connect()
drone.streamoff()  # Reinicia el stream en caso de que estuviera activo previamente
drone.streamon()
time.sleep(3)  # Espera a que el stream esté completamente listo

# Imprime el nivel de batería actual al iniciar
print(f'Batería: {drone.get_battery()}%')

# Variable global que indica si el dron está en el aire
flying = False

# Altura máxima permitida (300 cm = 3 metros)
MAX_HEIGHT_CM = 300

# Crear la ventana principal de la interfaz gráfica
root = tk.Tk()
root.title("Drone Camera")

# Label de Tkinter donde se mostrará el video
label = tk.Label(root)
label.pack()

# Variables de velocidad para cada grado de libertad
lr_vel = 0    # izquierda/derecha (Left/Right)
fb_vel = 0    # adelante/atrás (Forward/Backward)
ud_vel = 0    # arriba/abajo (Up/Down)
yaw_vel = 0   # giro (Yaw)

def clean_exit():
    """
    Finaliza correctamente el programa:
    - Detiene al dron si está volando.
    - Apaga el stream y cierra la conexión.
    - Cierra la interfaz gráfica.
    """
    global flying
    print("\nInterrupción detectada. Cerrando el programa...")
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
    Captura un frame del video del dron, le agrega información relevante como batería, altura y estado,
    y actualiza la interfaz gráfica con esa imagen.
    También maneja la lógica de control de movimiento y seguridad por batería baja.
    """
    global fb_vel, lr_vel, ud_vel, yaw_vel, flying
    try:
        frame = drone.get_frame_read().frame
        frame = cv2.resize(frame, (width, height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Información en tiempo real
        bateria = drone.get_battery()
        altura = drone.get_height()
        estado = "Volando" if flying else "Detenido"

        # Superponer datos al video
        cv2.putText(frame, f'Bateria: {bateria}%', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Altura: {altura}cm', (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Estado: {estado}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Convertir el frame a formato compatible con Tkinter
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)

        # Seguridad: aterriza si la batería es críticamente baja
        if flying and bateria <= 10:
            print("\nAdvertencia: Batería baja (<=10%). Aterrizando...")
            drone.land()
            flying = False

        # Envía comandos de movimiento solo si está volando
        if flying:
            if lr_vel == 0 and fb_vel == 0 and ud_vel == 0 and yaw_vel == 0:
                drone.send_rc_control(0, 0, 0, 0)
            else:
                drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        # Llama recursivamente cada 30 ms
        label.after(30, update_frame)

    except Exception as e:
        print(f"Error al actualizar frame: {e}")
        clean_exit()

def key_press(event):
    """
    Maneja los eventos cuando se presiona una tecla:
    - Controla el despegue, aterrizaje, salida segura
    - Asigna las velocidades de movimiento según la tecla
    """
    global flying, fb_vel, lr_vel, ud_vel, yaw_vel
    key = event.keysym.lower()

    if key == 'm':
        print("\nTecla M presionada. Saliendo del programa...")
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

    # Movimiento direccional
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
    elif key == 'q':
        yaw_vel = -60

def key_release(event):
    """
    Detiene el movimiento cuando se suelta una tecla asociada a control de movimiento.
    """
    global fb_vel, lr_vel, ud_vel, yaw_vel
    key = event.keysym.lower()
    if key in ['w', 's']:
        fb_vel = 0
    elif key in ['a', 'd']:
        lr_vel = 0
    elif key in ['r', 'f']:
        ud_vel = 0
    elif key in ['e', 'q']:
        yaw_vel = 0

# Asignar eventos de teclado a la ventana
root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)

# Iniciar la actualización del video en tiempo real
update_frame()

# Ejecutar la interfaz gráfica hasta que se cierre manualmente o con tecla 'm'
try:
    root.mainloop()
except KeyboardInterrupt:
    clean_exit()
