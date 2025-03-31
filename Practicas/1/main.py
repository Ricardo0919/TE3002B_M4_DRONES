from djitellopy import Tello
import cv2
import threading
import time

drone = Tello()
#Establece conexión de Wifi
drone.connect()
#Inicia el stream de video
drone.streamon()
#Revisar el estado de la bateria
print(drone.get_battery())


def clean_exit():
    print("\nInterrupción detectada. Cerrando el programa...")
    print("\nDeteniendo el dron...")
    drone.streamoff()
    drone.end()
    print("Programa cerrado correctamente.")


def video_stream():

    while True:
        pass


def control():

    while True:
        pass


def main():

    try:
        threading.Thread(target=video_stream, daemon=True).start()
        threading.Thread(target=control, daemon=True).start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        clean_exit()


if __name__ == '__main__':
    main()