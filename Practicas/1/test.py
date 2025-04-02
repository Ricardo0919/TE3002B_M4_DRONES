from djitellopy import tello
import cv2
import time

width = 320 
height = 240

# Inicializar el dron
drone = tello.Tello()
drone.connect()

drone.streamoff()
drone.streamon()

while True:
    frame_read = drone.get_frame_read()
    frame = frame_read.frame
    img = cv2.resize(frame, (width, height))

    cv2.imshow("Drone Camera", img)