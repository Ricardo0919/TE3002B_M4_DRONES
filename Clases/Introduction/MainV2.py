from djitellopy import Tello
import cv2
import time

# Conectar al drone
drone = Tello()
drone.connect()

# Iniciar stream de video
drone.streamon()
time.sleep(3)

global flying

def clean_exit():
    print("\nCerrando el programa...")

    if flying:
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(0.5)
        drone.land()
    cv2.destroyAllWindows()
    drone.streamoff()
    drone.end()
    print("Programa cerrado correctamente.")


def control():
    global flying
    flying = False
    fb_vel = 0

    while True:

        frame = drone.get_frame_read().frame
        if frame is None:
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        cv2.putText(frame, f'Bateria: {drone.get_battery()}%',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)

        cv2.putText(frame, f'Altura: {drone.get_height()}cm',
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)


        cv2.imshow('Video Stream', frame)

        key = cv2.waitKey(50) & 0xFF

        if key == ord('q'):
            clean_exit()
            break

        if key == ord('t'):
            if flying:
                pass
            else:
                drone.takeoff()
                flying = True

        if key == ord('l'):
            if flying:
                drone.land()
                time.sleep(5)
                flying = False

        if key == ord('w'):
            fb_vel = 60
        elif key == ord('s'):
            fb_vel = -60
        else:
            fb_vel = 0

        if flying: drone.send_rc_control(0, fb_vel, 0, 0)

def main():
    try:
        control()
    except KeyboardInterrupt:
        clean_exit()

if __name__ == '__main__':
    main()
