"""
Práctica 3. Reconocimiento de señas para control del drone
Implementación de Robótica Inteligente

Alumnos:
    Jonathan Arles Guevara Molina    A01710380
    Ezzat Alzahouri Campos           A01710709
    José Ángel Huerta Ríos           A01710607
    Ricardo Sierra Roa              A01709887

Profesor:
    Josué González García

Fecha de entrega:
    9 de junio de 2025
"""


import cv2                             # OpenCV: procesar imágenes y acceso a cámaras
import mediapipe as mp                 # MediaPipe: detección de manos
import time                            # Para temporizaciones
import tkinter as tk                   # Tkinter: GUI
from PIL import Image, ImageTk         # Para convertir frames a formato compatible con Tkinter
from djitellopy import Tello           # djitellopy: control del dron Tello

# =====================================================================
# LANDMARKS DE INTERÉS (dedos) – índices fijos de MediaPipe Hands
# =====================================================================
THUMB_TIP = 4
THUMB_IP = 3
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

# =====================================================================
# UTILIDADES DE GESTOS – clasificadores sencillos basados en posiciones Y
# =====================================================================
def contar_dedos(lm):
    # Cuenta dedos levantados (índice/middle/anular/meñique)
    return sum(lm[i].y < lm[i - 2].y for i in [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP])


def pulgar_extendido(lm):
    # Pulgar extendido si la punta (TIP) está a la izquierda de la articulación (IP)
    return lm[THUMB_TIP].x < lm[THUMB_IP].x


def is_fist(lm):
    # Fist = todos los dedos (índice, medio, anular, meñique) doblados
    return all(lm[i].y > lm[i - 2].y for i in [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP])


def is_only_pinky(lm):
    # Solo meñique levantado
    return (contar_dedos(lm) == 1 and lm[PINKY_TIP].y < lm[PINKY_TIP - 2].y)


def is_cuernito(lm):
    # “Cuernito” = índice y meñique levantados, resto doblados
    return (lm[INDEX_TIP].y < lm[INDEX_TIP - 2].y and
            lm[PINKY_TIP].y < lm[PINKY_TIP - 2].y and
            all(lm[i].y > lm[i - 2].y for i in [MIDDLE_TIP, RING_TIP]))


def is_CW(lm):
    # Gesto CW = pulgar + solo índice levantado, resto doblado
    return (pulgar_extendido(lm) and 
            lm[INDEX_TIP].y < lm[INDEX_TIP - 2].y and
            all(lm[i].y > lm[i - 2].y for i in [MIDDLE_TIP, RING_TIP, PINKY_TIP]))


# =====================================================================
# CONFIGURACIÓN DEL DRON TELLO
# =====================================================================
DRONE_WIDTH, DRONE_HEIGHT = 640, 320

drone = Tello()
drone.connect()
drone.streamoff()
drone.streamon()
time.sleep(3)
print(f'🔋 Batería inicial: {drone.get_battery()}%')

flying = False
MAX_HEIGHT_CM = 300          # Altura máxima = 3 m

# Advertencias visuales
warning_msg = ""
warning_time = 0
WARNING_DURATION = 3

# Velocidades globales de rc_control
lr_vel = fb_vel = ud_vel = yaw_vel = 0

# Indicador si hay alguna tecla presionada
key_active = False

# Variable de speed (se ajustará con trackbar)
speed = 60

# =====================================================================
# CONFIG DE MEDIAPIPE + CÁMARA LAPTOP (res 320×240)
# =====================================================================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

gesture_cap = cv2.VideoCapture(0)
# Forzar resolución reducida en la laptop para no saturar:
gesture_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
gesture_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Variables de control del puño (1 s hold)
fist_start_time = None
fist_confirmed = False


# =====================================================================
# GUI TKINTER – dos paneles: feed del dron + feed de gestos
# =====================================================================
root = tk.Tk()
root.title("🚀 Drone & Gesture Control (Optimizado)")

# Frame del dron y trackbar
frame_drone = tk.Frame(root)
frame_drone.pack(side=tk.LEFT, padx=5, pady=5)

drone_label = tk.Label(frame_drone)
drone_label.pack()

tk.Label(frame_drone, text="Speed").pack(pady=(5, 0))
scale_speed = tk.Scale(frame_drone, from_=0, to=100, orient='horizontal', length=200, resolution=1)
scale_speed.set(speed)
scale_speed.pack(pady=(0, 10))


# Frame de gestos
gesture_label = tk.Label(root)
gesture_label.pack(side=tk.RIGHT, padx=5, pady=5)


def clean_exit():
    """
    Aterriza si está volando, libera recursos y cierra la ventana.
    """
    global flying
    print("\n🛑 Cerrando programa...")
    if flying:
        try:
            drone.send_rc_control(0, 0, 0, 0)
            time.sleep(0.3)
            drone.land()
        except Exception:
            pass
        flying = False

    try:
        drone.streamoff()
        drone.end()
    except Exception:
        pass

    if gesture_cap.isOpened():
        gesture_cap.release()

    print("✅ Programa cerrado.")
    root.destroy()


def process_gestures_and_commands():
    """
    Captura frame de la laptop (320×240), detecta:
      - Puño (hold 1 s) → toggle takeoff/land
      - Otros gestos: pulgar solo, meñique, cuernito, CW, conteo dedos (adelante/atrás/izq/der/CCW)
    Actualiza: lr_vel, fb_vel, ud_vel, yaw_vel, flying
    Retorna frame RGB 320×240 para mostrar en GUI.
    """
    global fist_start_time, fist_confirmed, flying
    global lr_vel, fb_vel, ud_vel, yaw_vel, warning_msg, warning_time, key_active, speed

    try:
        ret, frame = gesture_cap.read()
    except Exception:
        return None

    if not ret or frame is None:
        return None

    # Leer valor de speed del trackbar
    speed = scale_speed.get()

    # Ya está en 320×240, no hace falta rescálalo. Solo flip + RGB:
    frame = cv2.flip(frame, 1)
    rgb_small = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_small)

    label = "No se detecta mano"
    tiempo_actual = time.time()

    # Si no se detecta mano:
    if not result.multi_hand_landmarks:
        if not key_active:
            # Sin gesto y sin tecla → detener movimientos
            lr_vel = fb_vel = ud_vel = yaw_vel = 0
        # Overlay de estado de vuelo + texto de gesto
        estado_text = "VOLANDO" if flying else "EN TIERRA"
        color_estado = (0, 255, 0) if flying else (0, 0, 255)
        cv2.putText(frame, f"🚩 {estado_text}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_estado, 2)
        cv2.putText(frame, label, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Si hay mano detectada:
    manos = result.multi_hand_landmarks
    puño_actual = any(is_fist(hand.landmark) for hand in manos)

    # —— PUÑO (1 s hold) = toggle estado vuelo —— 
    if puño_actual:
        if fist_start_time is None:
            fist_start_time = tiempo_actual
            fist_confirmed = False
        elif tiempo_actual - fist_start_time >= 1.0 and not fist_confirmed:
            # Toggle: si no vuela, takeoff; si vuela, land
            if not flying:
                if drone.get_battery() > 15:
                    print("💥 Puño: Despegando")
                    try:
                        drone.takeoff()
                    except Exception:
                        pass
                    flying = True
                else:
                    msg = "⚠️ Batería <15%. NO despega."
                    print(f"\n{msg}")
                    warning_msg = msg
                    warning_time = tiempo_actual
            else:
                print("💀 Puño: Aterrizando")
                try:
                    drone.send_rc_control(0, 0, 0, 0)
                    time.sleep(0.3)
                    drone.land()
                except Exception:
                    pass
                flying = False

            fist_confirmed = True

        label = "PUÑO"  # Mientras se mantiene, muestra “PUÑO”
    else:
        # Reset para próximo puño
        fist_start_time = None
        fist_confirmed = False

        # —— OTROS GESTOS (solo si no hay puño) ——
        if not key_active:
            lr_vel = fb_vel = ud_vel = yaw_vel = 0

        for hand in manos:
            lm = hand.landmark

            # → PULGAR solo (si todos los demás dedos están abajo)
            if pulgar_extendido(lm) and contar_dedos(lm) == 0:
                label = "PULGAR (Solo)"
                ud_vel = speed // 2
                break

            # → Meñique levantado → SUBIR
            if is_only_pinky(lm):
                label = "SUBIR (Meñique)"
                ud_vel = speed
                break

            # → Cuernito → BAJAR
            if is_cuernito(lm):
                label = "BAJAR (Cuernito)"
                ud_vel = -speed
                break

            # → CW → Girar derecha (Yaw +)
            if is_CW(lm):
                label = "CW (Girando)"
                yaw_vel = speed
                break

            # → Conteo dedos (1-4) → adelante/atrás/izq/der o CCW
            dedos = contar_dedos(lm)
            if dedos == 1 and not pulgar_extendido(lm):
                label = "ADELANTE (1 dedo)"
                fb_vel = speed
                break
            elif dedos == 2:
                label = "ATRÁS (2 dedos)"
                fb_vel = -speed
                break
            elif dedos == 3:
                label = "DERECHA (3 dedos)"
                lr_vel = speed
                break
            elif dedos == 4:
                if not pulgar_extendido(lm):
                    label = "IZQUIERDA (4 dedos)"
                    lr_vel = -speed
                else:
                    label = "CCW (Girando)"
                    yaw_vel = -speed
                break

        # Dibujar landmarks (en 320×240)
        for hand in manos:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    # Overlay de estado de vuelo + texto de gesto
    estado_text = "VOLANDO" if flying else "EN TIERRA"
    color_estado = (0, 255, 0) if flying else (0, 0, 255)
    cv2.putText(frame, f"🚩 {estado_text}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_estado, 2)
    cv2.putText(frame, label, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # RGB para Tkinter


def update_frame():
    """
    Ciclo principal (cada 50 ms):
      1) Captura feed del dron y overlay de batería/altura/estado
      2) Captura feed de la laptop con detección de gestos (320×240)
      3) Seguridad: si batería ≤ 10 % y está volando → land()
      4) Envío rc_control según lr_vel, fb_vel, ud_vel, yaw_vel (si volando)
      5) Programar próxima iteración (~50 ms)
    """
    global flying, warning_msg, warning_time

    try:
        # —— 1) STREAM DRON —— 
        try:
            drone_frame = drone.get_frame_read().frame
        except Exception:
            drone_frame = None

        if drone_frame is not None:
            drone_frame = cv2.resize(drone_frame, (DRONE_WIDTH, DRONE_HEIGHT))
            drone_frame = cv2.cvtColor(drone_frame, cv2.COLOR_BGR2RGB)

            bateria = drone.get_battery()
            altura = drone.get_height()
            estado_text = "Volando" if flying else "Detenido"

            cv2.putText(drone_frame, f'🔋 {bateria}%', (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(drone_frame, f'📏 Altura: {altura} cm', (10, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(drone_frame, f'🚩 {estado_text}', (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            if warning_msg and time.time() - warning_time < WARNING_DURATION:
                cv2.putText(drone_frame, warning_msg, (10, DRONE_HEIGHT - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            else:
                warning_msg = ""

            img_drone = Image.fromarray(drone_frame)
            imgtk_drone = ImageTk.PhotoImage(image=img_drone)
            drone_label.imgtk = imgtk_drone
            drone_label.configure(image=imgtk_drone)

        # —— 2) STREAM LAPTOP (GESTOS) —— 
        disp_gesture = process_gestures_and_commands()
        if disp_gesture is not None:
            img_gesture = Image.fromarray(disp_gesture)
            imgtk_gesture = ImageTk.PhotoImage(image=img_gesture)
            gesture_label.imgtk = imgtk_gesture
            gesture_label.configure(image=imgtk_gesture)

        # —— 3) SEGURIDAD: BATERÍA CRÍTICA —— 
        try:
            bateria_actual = drone.get_battery()
        except Exception:
            bateria_actual = 100

        if flying and bateria_actual <= 10:
            adv = "⚠️ Batería ≤ 10 %. Aterrizando..."
            print(f"\n{adv}")
            warning_msg = adv
            warning_time = time.time()
            try:
                drone.land()
            except Exception:
                pass
            flying = False

        # —— 4) ENVIAR COMANDOS RC_CONTROL —— 
        if flying:
            # Si no hay movimiento, mandar 0s (hover)
            if lr_vel == 0 and fb_vel == 0 and ud_vel == 0 and yaw_vel == 0:
                try:
                    drone.send_rc_control(0, 0, 0, 0)
                except Exception:
                    pass
            else:
                try:
                    drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)
                except Exception:
                    pass

        # —— 5) PRÓXIMA ITERACIÓN —— 
        root.after(50, update_frame)

    except Exception as e:
        print(f"Error en update_frame: {e}")
        clean_exit()


def key_press(event):
    """
    Teclas de emergencia/control manual:
      - 'm': cerrar app (land si volando)
      - 't': takeoff manual (si batería >15 %)
      - 'l': land manual
      - 'w','s','a','d','r','f','e','q': control direccional rc_control
    """
    global flying, fb_vel, lr_vel, ud_vel, yaw_vel, warning_msg, warning_time, key_active, speed

    key = event.keysym.lower()
    key_active = True  # Hay una tecla presionada
    speed = scale_speed.get()

    if key == 'm':
        print("\n🟥 KEY 'm': Saliendo...")
        clean_exit()

    elif key == 't':
        if not flying:
            try:
                bat = drone.get_battery()
            except Exception:
                bat = 100
            if bat <= 15:
                msg = "⚠️ Batería < 15 %. NO despega."
                print(f"\n{msg}")
                warning_msg = msg
                warning_time = time.time()
            else:
                print("🟢 KEY 't': Despegando...")
                try:
                    drone.takeoff()
                except Exception:
                    pass
                flying = True

    elif key == 'l':
        if flying:
            print("🔴 KEY 'l': Aterrizando...")
            try:
                drone.send_rc_control(0, 0, 0, 0)
                time.sleep(0.3)
                drone.land()
            except Exception:
                pass
            flying = False

    # Movimiento direccional manual
    elif key == 'w':
        fb_vel = speed
    elif key == 's':
        fb_vel = -speed
    elif key == 'a':
        lr_vel = -speed
    elif key == 'd':
        lr_vel = speed
    elif key == 'r':
        try:
            altura = drone.get_height()
        except Exception:
            altura = 0
        if altura < MAX_HEIGHT_CM:
            ud_vel = speed
        else:
            msg = "⚠️ Altura máx (3 m) alcanzada."
            print(f"\n{msg}")
            warning_msg = msg
            warning_time = time.time()
            ud_vel = 0
    elif key == 'f':
        ud_vel = -speed
    elif key == 'e':
        yaw_vel = speed
    elif key == 'q':
        yaw_vel = -speed


def key_release(event):
    """Reset de velocidad al soltar tecla."""
    global fb_vel, lr_vel, ud_vel, yaw_vel, key_active
    key = event.keysym.lower()
    key_active = False  # Ya no hay tecla presionada

    if key in ['w', 's']:
        fb_vel = 0
    elif key in ['a', 'd']:
        lr_vel = 0
    elif key in ['r', 'f']:
        ud_vel = 0
    elif key in ['e', 'q']:
        yaw_vel = 0


# Bindings y loop principal
root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)
update_frame()

try:
    root.mainloop()
except KeyboardInterrupt:
    clean_exit()
