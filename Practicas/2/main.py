import cv2
import numpy as np
import time
import tkinter as tk
from PIL import Image, ImageTk
from djitellopy import Tello

# =========================
# Configuración Inicial
# =========================

width, height = 1280, 960
x_threshold = int(0.10 * width)
y_threshold = int(0.10 * width)
area_min = 0.05 * (width * height)

# Variables globales de movimiento
lr_vel = 0
fb_vel = 0
ud_vel = 0
yaw_vel = 0
speed = 60
flying = False

# Advertencias
warning_msg = ""
warning_time = 0
WARNING_DURATION = 3
MAX_HEIGHT_CM = 300

# Cubo rubix - Verde
H_Min_init = 50
H_Max_init = 80
S_Min_init = 80
S_Max_init = 255
V_Min_init = 60
V_Max_init = 255

# Inicializar el dron
drone = Tello()
drone.connect()
drone.streamoff()
drone.streamon()
time.sleep(3)
print(f'Batería: {drone.get_battery()}%')

# =========================
# Interfaz Gráfica (Tkinter)
# =========================

root = tk.Tk()
root.title("Drone + Vision Tracking")
label = tk.Label(root)
label.pack()

# =========================
# Trackbars OpenCV (HSV + Speed)
# =========================

cv2.namedWindow('Trackbars')
cv2.resizeWindow('Trackbars', 600, 300)

def nothing(x):
    pass

# Trackbars HSV
nothing

# Trackbar Speed
cv2.createTrackbar('H Min', 'Trackbars', H_Min_init , 179, nothing)
cv2.createTrackbar('H Max', 'Trackbars', H_Max_init , 179, nothing)
cv2.createTrackbar('S Min', 'Trackbars', S_Min_init, 255, nothing)
cv2.createTrackbar('S Max', 'Trackbars', S_Max_init, 255, nothing)
cv2.createTrackbar('V Min', 'Trackbars', V_Min_init, 255, nothing)
cv2.createTrackbar('V Max', 'Trackbars', V_Max_init, 255, nothing)

# =========================
# Funciones Principales
# =========================

def clean_exit():
    global flying
    print("\nCerrando programa...")
    if flying:
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(0.5)
        drone.land()
    drone.streamoff()
    drone.end()
    root.destroy()

def update_frame():
    global fb_vel, lr_vel, ud_vel, yaw_vel, flying, warning_msg, warning_time, speed
    try:
        # Frame del dron
        frame = drone.get_frame_read().frame
        frame = cv2.resize(frame, (width, height))

        # Procesamiento HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h_min = cv2.getTrackbarPos('H Min', 'Trackbars')
        s_min = cv2.getTrackbarPos('S Min', 'Trackbars')
        v_min = cv2.getTrackbarPos('V Min', 'Trackbars')
        h_max = cv2.getTrackbarPos('H Max', 'Trackbars')
        s_max = cv2.getTrackbarPos('S Max', 'Trackbars')
        v_max = cv2.getTrackbarPos('V Max', 'Trackbars')
        speed = cv2.getTrackbarPos('Speed', 'Trackbars')

        lower_hsv = np.array([h_min, s_min, v_min])
        upper_hsv = np.array([h_max, s_max, v_max])

        blurred = cv2.GaussianBlur(hsv, (15, 15), 0)
        mask = cv2.inRange(blurred, lower_hsv, upper_hsv)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Detección de contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > area_min:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                x, y, w, h = cv2.boundingRect(approx)
                center = (x + w // 2, y + h // 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 5)
                cv2.circle(frame, center, 5, (0, 0, 255), cv2.FILLED)

                # Mensajes de posición
                if center[0] < (width // 2 - x_threshold):
                    cv2.putText(frame, "Izquierda", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                elif center[0] > (width // 2 + x_threshold):
                    cv2.putText(frame, "Derecha", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                else:
                    cv2.putText(frame, "Centro X", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

                if center[1] < (height // 2 - y_threshold):
                    cv2.putText(frame, "Arriba", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                elif center[1] > (height // 2 + y_threshold):
                    cv2.putText(frame, "Abajo", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                else:
                    cv2.putText(frame, "Centro Y", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        # Líneas de referencia
        cv2.line(frame, (width//2 - x_threshold, 0), (width//2 - x_threshold, height), (255, 0, 0), 2)
        cv2.line(frame, (width//2 + x_threshold, 0), (width//2 + x_threshold, height), (255, 0, 0), 2)
        cv2.line(frame, (0, height//2 - y_threshold), (width, height//2 - y_threshold), (255, 0, 0), 2)
        cv2.line(frame, (0, height//2 + y_threshold), (width, height//2 + y_threshold), (255, 0, 0), 2)

        # Datos del dron
        bateria = drone.get_battery()
        altura = drone.get_height()
        estado = "Volando" if flying else "Detenido"

        cv2.putText(frame, f'Bateria: {bateria}%', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Altura: {altura}cm', (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Estado: {estado}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f'Speed: {speed}', (width - 200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if warning_msg and time.time() - warning_time < WARNING_DURATION:
            cv2.putText(frame, warning_msg, (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Seguridad batería
        if flying and bateria <= 10:
            warning_msg = "Advertencia: Bateria crítica (<=10%)"
            warning_time = time.time()
            drone.land()
            flying = False

        # Enviar comandos
        if flying:
            drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        # Mostrar en Tkinter
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)

        label.after(30, update_frame)

    except Exception as e:
        print(f"Error en update_frame: {e}")
        clean_exit()

# =========================
# Control de Teclado
# =========================

def key_press(event):
    global flying, fb_vel, lr_vel, ud_vel, yaw_vel, speed
    key = event.keysym.lower()

    if key == 'm':
        clean_exit()
    elif key == 't':
        if not flying:
            if drone.get_battery() > 15:
                drone.takeoff()
                flying = True
    elif key == 'l':
        if flying:
            drone.land()
            flying = False
    elif key == 'w':
        fb_vel = speed
    elif key == 's':
        fb_vel = -speed
    elif key == 'a':
        lr_vel = -speed
    elif key == 'd':
        lr_vel = speed
    elif key == 'r':
        if drone.get_height() < MAX_HEIGHT_CM:
            ud_vel = speed
    elif key == 'f':
        ud_vel = -speed
    elif key == 'e':
        yaw_vel = speed
    elif key == 'q':
        yaw_vel = -speed

def key_release(event):
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

# =========================
# Main Loop
# =========================

root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)

update_frame()
try:
    root.mainloop()
except KeyboardInterrupt:
    clean_exit()
