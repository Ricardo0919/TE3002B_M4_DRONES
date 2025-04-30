"""
Práctica 1: Movimientos Básicos + Detección de Objetos HSV
Implementación de Robótica Inteligente

Alumnos:
    Jonathan Arles Guevara Molina    A01710380
    Ezzat Alzahouri Campos           A01710709
    José Ángel Huerta Ríos           A01710607
    Ricardo Sierra Roa              A01709887

Profesor:
    Josué González García
Fecha de entrega: 7 de abril de 2025
"""

# ───────────────────────────
# Imports
# ───────────────────────────
from djitellopy import Tello           # Control del dron
import cv2                             # Visión por computadora
import numpy as np                     # Cálculo numérico
import time                            # Funciones de tiempo
import tkinter as tk                   # Interfaz gráfica
from PIL import Image, ImageTk         # Conversión a formato Tk
import sys

# ───────────────────────────
# Configuración general
# ───────────────────────────

width, height = 640, 480            
x_threshold = int(0.10 * width)
y_threshold = int(0.10 * height)
area_min = 0.001 * (width * height)

MAX_HEIGHT_CM     = 300               # Altura máxima permitida (3 m)
WARNING_DURATION  = 3                 # Segundos que se muestran advertencias
speed             = 60                # Velocidad inicial (se ligará a trackbar)

# ───────────────────────────
# Variables de estado globales
# ───────────────────────────
flying      = False
lr_vel      = 0      # Izq-Der
fb_vel      = 0      # Adelante-Atrás
ud_vel      = 0      # Arriba-Abajo
yaw_vel     = 0      # Yaw
warning_msg = ""
warning_time= 0

# ───────────────────────────
# Rango HSV inicial  (cubo Rubix verde)
# ───────────────────────────
H_Min_init, H_Max_init = 50, 80
S_Min_init, S_Max_init = 80, 255
V_Min_init, V_Max_init = 60, 255

# ───────────────────────────
# Inicialización del dron
# ───────────────────────────
drone = Tello()
drone.connect()
drone.streamoff()
drone.streamon()
time.sleep(3)
print(f'Batería: {drone.get_battery()}%')

# ───────────────────────────
# Configuración de Trackbars
# ───────────────────────────
def nothing(x):
    pass

def setup_trackbars():
    cv2.namedWindow('Trackbars')
    cv2.resizeWindow('Trackbars', 400, 250)
    cv2.createTrackbar('H Min',  'Trackbars', H_Min_init, 179, nothing)
    cv2.createTrackbar('H Max',  'Trackbars', H_Max_init, 179, nothing)
    cv2.createTrackbar('S Min',  'Trackbars', S_Min_init, 255, nothing)
    cv2.createTrackbar('S Max',  'Trackbars', S_Max_init, 255, nothing)
    cv2.createTrackbar('V Min',  'Trackbars', V_Min_init, 255, nothing)
    cv2.createTrackbar('V Max',  'Trackbars', V_Max_init, 255, nothing)
    cv2.createTrackbar('Speed',  'Trackbars', speed,        100, nothing)

def get_trackbar_values():
    return {
        'h_min': cv2.getTrackbarPos('H Min', 'Trackbars'),
        'h_max': cv2.getTrackbarPos('H Max', 'Trackbars'),
        's_min': cv2.getTrackbarPos('S Min', 'Trackbars'),
        's_max': cv2.getTrackbarPos('S Max', 'Trackbars'),
        'v_min': cv2.getTrackbarPos('V Min', 'Trackbars'),
        'v_max': cv2.getTrackbarPos('V Max', 'Trackbars'),
        'speed': cv2.getTrackbarPos('Speed', 'Trackbars')
    }

# ───────────────────────────
# Funciones de detección y dibujo
# ───────────────────────────
def detect_and_draw(frame, hsv, lower, upper):
    """
    Dibuja bounding box y centro si el contorno supera area_min.
    Además escribe la dirección relativa.
    """
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.erode(mask,  None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > area_min:
            x, y, w, h = cv2.boundingRect(contour)
            center = (x + w // 2, y + h // 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)
            cv2.circle(frame, center, 4, (0,0,255), cv2.FILLED)
            label_direction(frame, center)

def label_direction(frame, center):
    # Eje X
    if center[0] < (width//2 - x_threshold):
        cv2.putText(frame, "Izquierda", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    elif center[0] > (width//2 + x_threshold):
        cv2.putText(frame, "Derecha",   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    else:
        cv2.putText(frame, "Centro X",  (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    # Eje Y
    if center[1] < (height//2 - y_threshold):
        cv2.putText(frame, "Arriba",    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    elif center[1] > (height//2 + y_threshold):
        cv2.putText(frame, "Abajo",     (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    else:
        cv2.putText(frame, "Centro Y",  (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

def draw_guides(frame):
    # Líneas guía para indicar zona de “centro”
    cv2.line(frame, (width//2 - x_threshold, 0), (width//2 - x_threshold, height), (255,0,0), 2)
    cv2.line(frame, (width//2 + x_threshold, 0), (width//2 + x_threshold, height), (255,0,0), 2)
    cv2.line(frame, (0, height//2 - y_threshold), (width, height//2 - y_threshold), (255,0,0), 2)
    cv2.line(frame, (0, height//2 + y_threshold), (width, height//2 + y_threshold), (255,0,0), 2)

def draw_status(frame, speed):
    global warning_msg, warning_time, flying
    bateria = drone.get_battery()
    altura  = drone.get_height()
    estado  = "Volando" if flying else "Detenido"

    cv2.putText(frame, f'Bateria: {bateria}%', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.putText(frame, f'Altura: {altura}cm',  (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.putText(frame, f'Estado: {estado}',    (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.putText(frame, f'Speed: {speed}',      (width-150, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

    # Mensajes de advertencia
    if warning_msg and time.time() - warning_time < WARNING_DURATION:
        cv2.putText(frame, warning_msg, (10, height-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

    # Batería crítica → aterriza
    if flying and bateria <= 10:
        warning_msg  = "Advertencia: Bateria crítica (<=10%)"
        warning_time = time.time()
        drone.land()
        flying = False

# ───────────────────────────
# GUI Tkinter
# ───────────────────────────
root = tk.Tk()
root.title("Drone Camera")

label = tk.Label(root)
label.pack()

# ───────────────────────────
# Funciones de control
# ───────────────────────────
def clean_exit():
    """Cierra programa de forma segura."""
    global flying
    print("\nCerrando programa...")
    if flying:
        drone.send_rc_control(0,0,0,0)
        time.sleep(0.5)
        drone.land()
    drone.streamoff()
    drone.end()
    cv2.destroyAllWindows()
    root.destroy()
    sys.exit()

def key_press(event):
    """Gestiona pulsaciones de tecla."""
    global flying, lr_vel, fb_vel, ud_vel, yaw_vel, warning_msg, warning_time, speed
    key = event.keysym.lower()

    if key == 'm':
        clean_exit()

    elif key == 't':
        if not flying:
            if drone.get_battery() <= 15:
                warning_msg  = "Advertencia: Bateria baja (<=15%)."
                warning_time = time.time()
                return
            print("Despegando...")
            drone.takeoff()
            flying = True

    elif key == 'l' and flying:
        print("Aterrizando...")
        drone.send_rc_control(0,0,0,0)
        time.sleep(0.5)
        drone.land()
        flying = False

    # Movimiento – velocidad tomada de trackbar
    elif key == 'w':
        fb_vel =  speed
    elif key == 's':
        fb_vel = -speed
    elif key == 'a':
        lr_vel = -speed
    elif key == 'd':
        lr_vel =  speed
    elif key == 'r':
        if drone.get_height() < MAX_HEIGHT_CM:
            ud_vel =  speed
        else:
            warning_msg  = "Altura maxima alcanzada (3 m)."
            warning_time = time.time()
            ud_vel = 0
    elif key == 'f':
        ud_vel = -speed
    elif key == 'e':
        yaw_vel =  speed
    elif key == 'q':
        yaw_vel = -speed

def key_release(event):
    """Detiene movimiento al soltar la tecla."""
    global lr_vel, fb_vel, ud_vel, yaw_vel
    key = event.keysym.lower()
    if key in ['w','s']:           fb_vel = 0
    elif key in ['a','d']:         lr_vel = 0
    elif key in ['r','f']:         ud_vel = 0
    elif key in ['e','q']:         yaw_vel = 0

root.bind("<KeyPress>",   key_press)
root.bind("<KeyRelease>", key_release)

# ───────────────────────────
# Loop de actualización de frame
# ───────────────────────────
def update_frame():
    global lr_vel, fb_vel, ud_vel, yaw_vel, flying, warning_msg, warning_time, speed

    try:
        frame = drone.get_frame_read().frame
        frame = cv2.resize(frame, (width, height))

        # --- Detección ---
        hsv        = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        vals       = get_trackbar_values()
        speed      = vals['speed']          # actualizamos velocidad global
        lower      = np.array([vals['h_min'], vals['s_min'], vals['v_min']])
        upper      = np.array([vals['h_max'], vals['s_max'], vals['v_max']])

        detect_and_draw(frame, hsv, lower, upper)
        draw_guides(frame)
        draw_status(frame, speed)

        # --- Control de movimiento ---
        if flying:
            if lr_vel==fb_vel==ud_vel==yaw_vel==0:
                drone.send_rc_control(0,0,0,0)
            else:
                drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        # --- Mostrar en Tkinter ---
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img       = Image.fromarray(frame_rgb)
        imgtk     = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)

        # Re-ejecutar tras ~30 ms
        label.after(30, update_frame)

    except Exception as e:
        print(f"Error en update_frame: {e}")
        clean_exit()

# ───────────────────────────
# Arranque de trackbars y GUI
# ───────────────────────────
setup_trackbars()
update_frame()

try:
    root.mainloop()
except KeyboardInterrupt:
    clean_exit()
