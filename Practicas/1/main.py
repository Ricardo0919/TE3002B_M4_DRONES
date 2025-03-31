from djitellopy import Tello
import cv2
import threading
import time

drone = Tello()
# Establece conexión de Wifi
drone.connect()
# Inicia el stream de video
drone.streamon()
# Revisar el estado de la bateria
print(drone.get_battery())

# Iniciar la variable drone_flying
drone_flying = False


def clean_exit():
    print("\nInterrupción detectada. Cerrando el programa...")
    print("\nDeteniendo el dron...")
    drone.streamoff()
    drone.end()
    cv2.destroyAllWindows()
    print("Programa cerrado correctamente.")


def video_stream():

    while True:
        # Obteniendo el último frame del video
        frame = drone.get_frame_read().frame

        # Mostrando la imagen
        cv2.imshow("Stream de video", frame)

        # Moviendo el drone con el teclado
        key = cv2.waitkey(10) & 0xFF

        # Cerrar al presionar 'q'
        if key == ord('q'):
            clean_exit()
            break

        # Take off al presionar 't'
        elif key == ord('t'):
            if not drone_flying:
                drone.takeoff()
                drone_flying = True

        # Aterrizar con 'l'
        elif key == ord('l'):
            if drone_flying:
                drone.land()
                drone_flying = False

        # Mover hacia adelante con 'w'
        elif key == ord('w'):
            drone_fb_speed = 60

        # Mover hacia atras con 's'
        elif key == ord('s'):
            drone_fb_speed = -60

        else:
            drone_fb_speed = 0

        if drone_flying:
            drone.send_rc_control(0, drone_fb_speed, 0, 0)


def control():

    while True:
        pass


def main():

    try:
        video_stream()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        clean_exit()


if __name__ == '__main__':
    main()