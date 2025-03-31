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
    cv2.destroyAllWindows()
    print("Programa cerrado correctamente.")


def video_stream():

    while True:
        # Obteniendo el último frame del video
        frame = drone.get_frame_read().frame

        #Mostrando la imagen
        cv2.imshow("Stream de video", frame)

        #Cerrar al presionar 'q'
        if cv2.waitKey(10) & 0xFF == ord('q'):
            clean_exit()
            break


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