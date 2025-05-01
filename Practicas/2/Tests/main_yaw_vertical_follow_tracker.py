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
x_threshold = int(0.15 * width)
y_threshold = int(0.15 * height)
area_min = 0.001 * (width * height)

MAX_HEIGHT_CM = 300
WARNING_DURATION = 3
speed = 20

AREA_TOO_SMALL = 1500
AREA_TOO_LARGE = 20000

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
manual_ud = False
manual_fb = False
center_object_x = None
center_object_y = None
area = None

# ───────────────────────────
# Rango HSV inicial - Amarillo Rubix
# ───────────────────────────
#H_Min_init, H_Max_init = 20, 40
#S_Min_init, S_Max_init = 148, 255
#V_Min_init, V_Max_init = 89, 255

# ───────────────────────────
# Rango HSV inicial - Verde Rubix
# ───────────────────────────
H_Min_init, H_Max_init = 40, 80
S_Min_init, S_Max_init = 50, 255
V_Min_init, V_Max_init = 50, 255

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
    cv2.createTrackbar('Area Min', 'Trackbars', int(area_min), 30000, nothing)


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
    global center_object_x, center_object_y, area

    center_object_x = None
    center_object_y = None
    area = None

    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    area_min_dynamic = cv2.getTrackbarPos('Area Min', 'Trackbars')

    for cnt in contours:
        a = cv2.contourArea(cnt)
        if a > area_min_dynamic:
            area = a
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            x, y, w, h = cv2.boundingRect(approx)

            cx = x + w // 2
            cy = y + h // 2
            center_object_x = cx
            center_object_y = cy

            # Dibujar info visual
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
            cv2.line(frame, (width//2, height//2), (cx, cy), (0, 0, 255), 2)

            # Dirección estimada
            if cx < width // 2 - x_threshold:
                cv2.putText(frame, "Izquierda", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            elif cx > width // 2 + x_threshold:
                cv2.putText(frame, "Derecha", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Centro X", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if cy < height // 2 - y_threshold:
                cv2.putText(frame, "Arriba", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            elif cy > height // 2 + y_threshold:
                cv2.putText(frame, "Abajo", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Centro Y", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

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

    if center_object_x is not None and center_object_y is not None:
        texto_centro = f'Centro: ({center_object_x}, {center_object_y})'
        cv2.putText(frame, texto_centro, (10, height - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    if area is not None:
        texto_area = f'Area: {int(area)}'
        cv2.putText(frame, texto_area, (10, height - 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

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
    global flying, lr_vel, fb_vel, ud_vel, yaw_vel, warning_msg, warning_time, speed, manual_yaw, manual_ud
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
    elif key == 'w': 
        fb_vel = speed
        manual_fb = True
    elif key == 's': 
        fb_vel = -speed
        manual_fb = True
    elif key == 'a': 
        lr_vel = -speed
    elif key == 'd': 
        lr_vel = speed
    elif key == 'r':
        if drone.get_height() < MAX_HEIGHT_CM:
            ud_vel = speed
            manual_ud = True
        else:
            warning_msg = "Altura máxima alcanzada (3 m)."
            warning_time = time.time()
            ud_vel = 0
    elif key == 'f':
        ud_vel = -speed
        manual_ud = True
    elif key == 'e':
        yaw_vel = speed
        manual_yaw = True
    elif key == 'q':
        yaw_vel = -speed
        manual_yaw = True

def key_release(event):
    global lr_vel, fb_vel, ud_vel, yaw_vel, manual_yaw, manual_ud
    key = event.keysym.lower()
    if key in ['w','s']: 
        fb_vel = 0
        manual_fb = False
    elif key in ['a','d']: 
        lr_vel = 0
    elif key in ['r','f']:
        ud_vel = 0
        manual_ud = False
    elif key in ['e','q']:
        yaw_vel = 0
        manual_yaw = False

root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)

# ───────────────────────────
# Loop de video y seguimiento
# ───────────────────────────
def update_frame():
    global lr_vel, fb_vel, ud_vel, yaw_vel, flying, warning_msg, warning_time, speed, center_object_x, center_object_y, manual_yaw, manual_ud

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

        # Seguimiento automático yaw
        if flying and follow_yaw and center_object_x is not None and not manual_yaw:
            center_x = width // 2
            if center_object_x < (center_x - x_threshold):
                yaw_vel = -speed
            elif center_object_x > (center_x + x_threshold):
                yaw_vel = speed
            else:
                yaw_vel = 0

        # Seguimiento automático vertical (ud_vel)
        if flying and follow_yaw and center_object_y is not None and not manual_ud:
            center_y = height // 2
            if center_object_y < (center_y - y_threshold):
                ud_vel = speed
            elif center_object_y > (center_y + y_threshold):
                ud_vel = -speed
            else:
                ud_vel = 0
        
        # Seguimiento automático adelante/atrás basado en el área
        if flying and area is not None and not manual_fb:
            if area < AREA_TOO_SMALL:
                fb_vel = speed  # Avanzar
            elif area > AREA_TOO_LARGE:
                fb_vel = -speed  # Retroceder
            else:
                fb_vel = 0


        if flying:
            drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)
        cv2.waitKey(1)
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