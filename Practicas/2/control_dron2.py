import cv2
from djitellopy import Tello
import time
import numpy as np

# Inicializar el dron
drone = Tello()
drone.connect()
print(f'Batería: {drone.get_battery()}%')

# Inicializar la cámara
drone.streamon()

# Variables de control
flying = False
vel = 30  # Velocidad de movimiento (puedes ajustarla)

# Configuración de rango de color (ejemplo: rojo)
lower = np.array([32, 95, 54])
upper = np.array([167, 255, 160])

while True:
    frame = drone.get_frame_read().frame
    frame = cv2.resize(frame, (640, 480))

    # Convertir a HSV para la detección de color
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)

    # Encontrar contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    target_cX = None
    cY = None
    area = 0

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)

        if area > 500:  # Filtro para ignorar ruidos pequeños
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                target_cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])

            # Dibujar centro del objeto detectado
            cv2.circle(frame, (target_cX, cY), 5, (255, 0, 0), -1)

    # --- Control automático basado en detección ---
    if target_cX is not None and cY is not None:
        frame_center_x = frame.shape[1] // 2
        frame_center_y = frame.shape[0] // 2

        offset_x = target_cX - frame_center_x  # Desviación horizontal
        offset_y = cY - frame_center_y         # Desviación vertical

        lr = ud = fb = yaw = 0

        # --- Control de YAW (horizontal) ---
        if abs(offset_x) > 20:  # Tolerancia
            yaw = vel if offset_x > 0 else -vel

        # --- Control de Altitud (vertical) ---
        if abs(offset_y) > 20:  # Tolerancia
            ud = vel if offset_y < 0 else -vel

        # --- Control de Acercamiento/Alejamiento (profundidad) ---
        if area < 6000:
            fb = vel  # Acercarse
        elif area > 12000:
            fb = -vel  # Alejarse

        if flying:
            drone.send_rc_control(lr, fb, ud, yaw)
            time.sleep(0.1)
            drone.send_rc_control(0, 0, 0, 0)

    # Mostrar las imágenes
    cv2.imshow('Tello - Cámara', frame)
    cv2.imshow('Mascara de color', mask)

    # Control manual por teclado
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('t'):
        drone.takeoff()
        flying = True
    elif key == ord('l'):
        drone.land()
        flying = False
    elif flying:
        if key == ord('w'):
            drone.send_rc_control(0, vel, 0, 0)
        elif key == ord('s'):
            drone.send_rc_control(0, -vel, 0, 0)
        elif key == ord('a'):
            drone.send_rc_control(-vel, 0, 0, 0)
        elif key == ord('d'):
            drone.send_rc_control(vel, 0, 0, 0)
        elif key == ord('e'):
            drone.send_rc_control(0, 0, 0, vel)
        elif key == ord('q'):
            drone.send_rc_control(0, 0, 0, -vel)
        elif key == ord('r'):
            drone.send_rc_control(0, 0, vel, 0)
        elif key == ord('f'):
            drone.send_rc_control(0, 0, -vel, 0)
        else:
            drone.send_rc_control(0, 0, 0, 0)

# Finalizar
drone.streamoff()
cv2.destroyAllWindows()
