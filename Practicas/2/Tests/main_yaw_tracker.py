"""
Práctica 1: Movimientos Básicos + Detección de Objetos HSV + Seguimiento en eje yaw (con prioridad manual)
Implementación de Robótica Inteligente
"""

# ───────────────────────────
# Imports
# ───────────────────────────
from djitellopy import Tello
import cv2
import numpy as np
import time
import tkinter as tk
from PIL import Image, ImageTk
import sys

# ───────────────────────────
# Configuración general
# ───────────────────────────
width, height = 640, 480
x_threshold = int(0.10 * width)
y_threshold = int(0.10 * height)
area_min = 0.001 * (width * height)

MAX_HEIGHT_CM = 300
WARNING_DURATION = 3
speed = 60

# ───────────────────────────
# Variables de estado globales
# ───────────────────────────
flying = False
lr_vel = 0
fb_vel = 0
ud_vel = 0
yaw_vel = 0
warning_msg = ""
warning_time = 0
follow_yaw = True
manual_yaw = False
center_object_x = None

# ───────────────────────────
# Rango HSV inicial - Verde Rubik
# ───────────────────────────
H_Min_init, H_Max_init = 40, 80
S_Min_init, S_Max_init = 50, 255
V_Min_init, V_Max_init = 50, 255
#original
#H_Min_init, H_Max_init = 50, 80
#S_Min_init, S_Max_init = 80, 255
#V_Min_init, V_Max_init = 60, 255

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
# Trackbars
# ───────────────────────────
def nothing(x): pass

def setup_trackbars():
    cv2.namedWindow('Trackbars')
    cv2.resizeWindow('Trackbars', 400, 250)
    cv2.createTrackbar('H Min',  'Trackbars', H_Min_init, 179, nothing)
    cv2.createTrackbar('H Max',  'Trackbars', H_Max_init, 179, nothing)
    cv2.createTrackbar('S Min',  'Trackbars', S_Min_init, 255, nothing)
    cv2.createTrackbar('S Max',  'Trackbars', S_Max_init, 255, nothing)
    cv2.createTrackbar('V Min',  'Trackbars', V_Min_init, 255, nothing)
    cv2.createTrackbar('V Max',  'Trackbars', V_Max_init, 255, nothing)
    cv2.createTrackbar('Speed',  'Trackbars', speed,      100, nothing)

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
# Detección de objetos
# ───────────────────────────
def detect_and_draw(frame, hsv, lower, upper):
    global center_object_x
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    center_object_x = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > area_min:
            x, y, w, h = cv2.boundingRect(contour)
            center = (x + w // 2, y + h // 2)
            center_object_x = center[0]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)
            cv2.circle(frame, center, 4, (0,0,255), cv2.FILLED)
            label_direction(frame, center)

def label_direction(frame, center):
    if center[0] < (width//2 - x_threshold):
        cv2.putText(frame, "Izquierda", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    elif center[0] > (width//2 + x_threshold):
        cv2.putText(frame, "Derecha", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    else:
        cv2.putText(frame, "Centro X", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

    if center[1] < (height//2 - y_threshold):
        cv2.putText(frame, "Arriba", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    elif center[1] > (height//2 + y_threshold):
        cv2.putText(frame, "Abajo", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
    else:
        cv2.putText(frame, "Centro Y", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

def draw_guides(frame):
    cv2.line(frame, (width//2 - x_threshold, 0), (width//2 - x_threshold, height), (255,0,0), 2)
    cv2.line(frame, (width//2 + x_threshold, 0), (width//2 + x_threshold, height), (255,0,0), 2)
    cv2.line(frame, (0, height//2 - y_threshold), (width, height//2 - y_threshold), (255,0,0), 2)
    cv2.line(frame, (0, height//2 + y_threshold), (width, height//2 + y_threshold), (255,0,0), 2)

def draw_status(frame, speed):
    global warning_msg, warning_time, flying
    bateria = drone.get_battery()
    altura = drone.get_height()
    estado = "Volando" if flying else "Detenido"

    cv2.putText(frame, f'Bateria: {bateria}%', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.putText(frame, f'Altura: {altura}cm', (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.putText(frame, f'Estado: {estado}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.putText(frame, f'Speed: {speed}', (width-150, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

    if warning_msg and time.time() - warning_time < WARNING_DURATION:
        cv2.putText(frame, warning_msg, (10, height-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

    if flying and bateria <= 10:
        warning_msg = "Advertencia: Bateria crítica (<=10%)"
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
# Control manual y eventos
# ───────────────────────────
def clean_exit():
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
    global flying, lr_vel, fb_vel, ud_vel, yaw_vel, warning_msg, warning_time, speed, manual_yaw
    key = event.keysym.lower()
    if key == 'm':
        clean_exit()
    elif key == 't' and not flying:
        if drone.get_battery() <= 15:
            warning_msg = "Advertencia: Bateria baja (<=15%)"
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
    elif key == 'w': fb_vel = speed
    elif key == 's': fb_vel = -speed
    elif key == 'a': lr_vel = -speed
    elif key == 'd': lr_vel = speed
    elif key == 'r':
        if drone.get_height() < MAX_HEIGHT_CM:
            ud_vel = speed
        else:
            warning_msg = "Altura máxima alcanzada (3 m)."
            warning_time = time.time()
            ud_vel = 0
    elif key == 'f': ud_vel = -speed
    elif key == 'e':
        yaw_vel = speed
        manual_yaw = True
    elif key == 'q':
        yaw_vel = -speed
        manual_yaw = True

def key_release(event):
    global lr_vel, fb_vel, ud_vel, yaw_vel, manual_yaw
    key = event.keysym.lower()
    if key in ['w','s']: fb_vel = 0
    elif key in ['a','d']: lr_vel = 0
    elif key in ['r','f']: ud_vel = 0
    elif key in ['e','q']:
        yaw_vel = 0
        manual_yaw = False

root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)

# ───────────────────────────
# Loop de video y seguimiento
# ───────────────────────────
def update_frame():
    global lr_vel, fb_vel, ud_vel, yaw_vel, flying, warning_msg, warning_time, speed, center_object_x, manual_yaw

    try:
        frame = drone.get_frame_read().frame
        frame = cv2.resize(frame, (width, height))
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        vals = get_trackbar_values()
        speed = vals['speed']
        lower = np.array([vals['h_min'], vals['s_min'], vals['v_min']])
        upper = np.array([vals['h_max'], vals['s_max'], vals['v_max']])

        detect_and_draw(frame, hsv, lower, upper)
        draw_guides(frame)
        draw_status(frame, speed)

        # Seguimiento automático yaw (si no hay input manual)
        if flying and follow_yaw and center_object_x is not None and not manual_yaw:
            center_x = width // 2
            if center_object_x < (center_x - x_threshold):
                yaw_vel = -15
            elif center_object_x > (center_x + x_threshold):
                yaw_vel = 15
            else:
                yaw_vel = 0  # En el centro

        # Enviar comandos de movimiento
        if flying:
            drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        # Mostrar en GUI
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)
        label.after(30, update_frame)

    except Exception as e:
        print(f"Error en update_frame: {e}")
        clean_exit()

# ───────────────────────────
# Inicio
# ───────────────────────────
setup_trackbars()
update_frame()
try:
    root.mainloop()
except KeyboardInterrupt:
    clean_exit()
