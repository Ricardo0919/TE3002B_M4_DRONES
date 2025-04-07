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

from djitellopy import Tello           # Librería para controlar drones Tello
import cv2                             # Librería para visión por computadora
import time                            # Para funciones de tiempo
import tkinter as tk                   # Para interfaz gráfica (GUI)
from PIL import Image, ImageTk         # Para convertir imágenes a formato compatible con Tkinter

# Tamaño de la ventana de video
width, height = 1280, 960

# Inicialización del dron
drone = Tello()
drone.connect()          # Conecta al dron vía WiFi
drone.streamoff()        # Asegura que el stream esté apagado antes de iniciarlo
drone.streamon()         # Activa el stream de video
time.sleep(3)            # Da tiempo para que el stream se estabilice

# Muestra el nivel de batería al comenzar
print(f'Batería: {drone.get_battery()}%')

# Bandera que indica si el dron está volando
flying = False

# Altura máxima permitida en centímetros (3 metros)
MAX_HEIGHT_CM = 300

# Variables para advertencias visuales
warning_msg = ""             # Mensaje de advertencia actual
warning_time = 0             # Momento en que se mostró la advertencia
WARNING_DURATION = 3         # Duración de la advertencia en pantalla (segundos)

# Crear ventana principal
root = tk.Tk()
root.title("Drone Camera")

# Componente donde se mostrará el video
label = tk.Label(root)
label.pack()

# Variables de velocidad por cada eje de movimiento
lr_vel = 0    # Izquierda / Derecha
fb_vel = 0    # Adelante / Atrás
ud_vel = 0    # Arriba / Abajo
yaw_vel = 0   # Giro (Yaw)

def clean_exit():
    """
    Finaliza la ejecución de forma segura.
    Aterriza el dron si está volando, apaga el stream y cierra la GUI.
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
    Captura y actualiza el frame de video en la interfaz gráfica.
    También muestra información del estado y controla advertencias visuales.
    """
    global fb_vel, lr_vel, ud_vel, yaw_vel, flying, warning_msg, warning_time
    try:
        # Captura el frame actual del dron
        frame = drone.get_frame_read().frame
        frame = cv2.resize(frame, (width, height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Obtiene datos del dron
        bateria = drone.get_battery()
        altura = drone.get_height()
        estado = "Volando" if flying else "Detenido"

        # Superpone texto informativo
        cv2.putText(frame, f'Bateria: {bateria}%', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Altura: {altura}cm', (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Estado: {estado}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Muestra advertencia si sigue vigente
        if warning_msg and time.time() - warning_time < WARNING_DURATION:
            cv2.putText(frame, warning_msg, (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        else:
            warning_msg = ""

        # Convierte a formato compatible con Tkinter
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)

        # Seguridad: aterrizaje automático si batería crítica
        if flying and bateria <= 10:
            msg = "Advertencia: Bateria baja (<=10%). Aterrizando..."
            print(f"\n{msg}")
            warning_msg = msg
            warning_time = time.time()
            drone.land()
            flying = False

        # Envía comandos de movimiento si está en el aire
        if flying:
            if lr_vel == 0 and fb_vel == 0 and ud_vel == 0 and yaw_vel == 0:
                drone.send_rc_control(0, 0, 0, 0)
            else:
                drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        # Repite cada 30ms (frecuencia de actualización de video)
        label.after(30, update_frame)

    except Exception as e:
        print(f"Error al actualizar frame: {e}")
        clean_exit()

def key_press(event):
    """
    Maneja eventos de teclado cuando una tecla es presionada.
    Define comandos de vuelo y control de movimiento.
    """
    global flying, fb_vel, lr_vel, ud_vel, yaw_vel, warning_msg, warning_time
    key = event.keysym.lower()

    if key == 'm':
        print("\nTecla M presionada. Saliendo del programa...")
        clean_exit()

    elif key == 't':
        # Intenta despegar si no está volando y la batería es suficiente
        if not flying:
            if drone.get_battery() <= 15:
                msg = "Advertencia: Bateria demasiado baja para despegar (<=15%)."
                print(f"\n{msg}")
                warning_msg = msg
                warning_time = time.time()
                return
            print("Despegando...")
            drone.takeoff()
            flying = True

    elif key == 'l':
        # Aterriza si está volando
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
        # Solo sube si no ha alcanzado altura máxima
        if drone.get_height() < MAX_HEIGHT_CM:
            ud_vel = 60
        else:
            msg = "Advertencia: Altura maxima alcanzada (3m). No se puede subir más."
            print(f"\n{msg}")
            warning_msg = msg
            warning_time = time.time()
            ud_vel = 0
    elif key == 'f':
        ud_vel = -60
    elif key == 'e':
        yaw_vel = 60
    elif key == 'q':
        yaw_vel = -60

def key_release(event):
    """
    Detiene el movimiento correspondiente al soltar la tecla.
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

# Asigna funciones a eventos de teclado
root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)

# Inicia el ciclo principal de actualización de video
update_frame()

# Ejecuta la interfaz hasta que se cierre manualmente o con tecla 'm'
try:
    root.mainloop()
except KeyboardInterrupt:
    clean_exit()
