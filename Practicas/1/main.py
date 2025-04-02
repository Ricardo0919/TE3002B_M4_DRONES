from djitellopy import Tello
import cv2
import time


drone = Tello()
# Establece conexión de Wifi
drone.connect()
# Inicia el stream de video
drone.streamon()
time.sleep(3)

# Revisar el estado de la bateria
print(drone.get_battery())

# Iniciar la variable drone_flying
global flying

def clean_exit():
    print("\nInterrupción detectada. Cerrando el programa...")
    print("\nDeteniendo el dron...")
    if flying:
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(0.5)
        drone.land()
    cv2.destroyAllWindows()
    drone.streamoff()
    drone.end()
    print("Programa cerrado correctamente.")
    

def control():
    # Iniciar la variable flying
    global flying
    flying = False

    # Iniciar velocidad de inicial de vuelo
    fb_vel = 0

    while True:
        # Obteniendo el último frame del video
        frame = drone.get_frame_read().frame
        if frame is None:
            continue
        
        # Convertir el frame a RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Mostrar bateria en el frame 
        cv2.putText(frame, f'Bateria: {drone.get_battery()}%',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)

        # Mostrar la altura del drone en el frame
        cv2.putText(frame, f'Altura: {drone.get_height()}cm',
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)

        # Mostrar la imagen
        cv2.imshow('Video Stream', frame)

        # Mover el drone con el teclado
        key = cv2.waitKey(50) & 0xFF

        # Cerrar al presionar 'q'
        if key == ord('q'):
            clean_exit()
            break

        # Take off al presionar 't'
        if key == ord('t'):
            if flying:
                pass
            else:
                drone.takeoff()
                flying = True

        # Aterrizar con 'l'
        if key == ord('l'):
            if flying:
                drone.land()
                time.sleep(5)
                flying = False

        # Mover hacia adelante con 'w'
        if key == ord('w'):
            fb_vel = 60

        # Mover hacia atras con 's'
        elif key == ord('s'):
            fb_vel = -60
        
        
        # Detener el movimiento
        else:
            fb_vel = 0

        # Enviar el comando al drone
        if flying: drone.send_rc_control(0, fb_vel, 0, 0)


def main():
    try:
        control()
    except KeyboardInterrupt:
        clean_exit()

if __name__ == '__main__':
    main()