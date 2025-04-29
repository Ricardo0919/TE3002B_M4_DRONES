import cv2
import numpy as np
import time
from djitellopy import Tello

# =========================
# Configuración Inicial
# =========================

width, height = 640, 480  # Baja resolución para menor latencia
x_threshold = int(0.10 * width)
y_threshold = int(0.10 * width)
area_min = 0.001 * (width * height)

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
# Trackbars OpenCV (HSV + Speed)
# =========================

cv2.namedWindow('Trackbars')
cv2.resizeWindow('Trackbars', 400, 250)

def nothing(x):
    pass

cv2.createTrackbar('H Min', 'Trackbars', H_Min_init , 179, nothing)
cv2.createTrackbar('H Max', 'Trackbars', H_Max_init , 179, nothing)
cv2.createTrackbar('S Min', 'Trackbars', S_Min_init, 255, nothing)
cv2.createTrackbar('S Max', 'Trackbars', S_Max_init, 255, nothing)
cv2.createTrackbar('V Min', 'Trackbars', V_Min_init, 255, nothing)
cv2.createTrackbar('V Max', 'Trackbars', V_Max_init, 255, nothing)
cv2.createTrackbar('Speed', 'Trackbars', speed, 100, nothing)

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
    cv2.destroyAllWindows()

def main_loop():
    global fb_vel, lr_vel, ud_vel, yaw_vel, flying, warning_msg, warning_time, speed

    while True:
        frame_read = drone.get_frame_read()
        frame = frame_read.frame

        if frame is None:
            continue  # Si no hay frame válido, lo saltamos

        frame = cv2.resize(frame, (width, height))

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

        blurred = cv2.GaussianBlur(hsv, (5, 5), 0)
        mask = cv2.inRange(blurred, lower_hsv, upper_hsv)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > area_min:
                x, y, w, h = cv2.boundingRect(contour)
                center = (x + w // 2, y + h // 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame, center, 4, (0, 0, 255), cv2.FILLED)

                if center[0] < (width // 2 - x_threshold):
                    cv2.putText(frame, "Izquierda", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                elif center[0] > (width // 2 + x_threshold):
                    cv2.putText(frame, "Derecha", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                else:
                    cv2.putText(frame, "Centro X", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

                if center[1] < (height // 2 - y_threshold):
                    cv2.putText(frame, "Arriba", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                elif center[1] > (height // 2 + y_threshold):
                    cv2.putText(frame, "Abajo", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                else:
                    cv2.putText(frame, "Centro Y", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.line(frame, (width//2 - x_threshold, 0), (width//2 - x_threshold, height), (255, 0, 0), 2)
        cv2.line(frame, (width//2 + x_threshold, 0), (width//2 + x_threshold, height), (255, 0, 0), 2)
        cv2.line(frame, (0, height//2 - y_threshold), (width, height//2 - y_threshold), (255, 0, 0), 2)
        cv2.line(frame, (0, height//2 + y_threshold), (width, height//2 + y_threshold), (255, 0, 0), 2)

        bateria = drone.get_battery()
        altura = drone.get_height()
        estado = "Volando" if flying else "Detenido"

        cv2.putText(frame, f'Bateria: {bateria}%', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Altura: {altura}cm', (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Estado: {estado}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Speed: {speed}', (width - 150, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if warning_msg and time.time() - warning_time < WARNING_DURATION:
            cv2.putText(frame, warning_msg, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        if flying and bateria <= 10:
            warning_msg = "Advertencia: Bateria crítica (<=10%)"
            warning_time = time.time()
            drone.land()
            flying = False

        if flying:
            drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        cv2.imshow('Drone Camera', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 27 or key == ord('m'):
            clean_exit()
            break
        elif key == ord('t') and not flying:
            if drone.get_battery() > 15:
                drone.takeoff()
                flying = True
        elif key == ord('l') and flying:
            drone.land()
            flying = False
        elif key == ord('w'):
            fb_vel = speed
        elif key == ord('s'):
            fb_vel = -speed
        elif key == ord('a'):
            lr_vel = -speed
        elif key == ord('d'):
            lr_vel = speed
        elif key == ord('r'):
            if drone.get_height() < MAX_HEIGHT_CM:
                ud_vel = speed
        elif key == ord('f'):
            ud_vel = -speed
        elif key == ord('e'):
            yaw_vel = speed
        elif key == ord('q'):
            yaw_vel = -speed
        else:
            fb_vel = 0
            lr_vel = 0
            ud_vel = 0
            yaw_vel = 0

        time.sleep(0.01)  # Pausa ligera para no saturar CPU

# =========================
# Main Loop
# =========================

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        clean_exit()
