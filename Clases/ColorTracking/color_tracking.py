import cv2
# pip install opencv-python
import numpy as np
# pip install numpy

width = 800
height = 600

x_threshold = int(0.10 * width)
y_threshold = int(0.10 * width)

def callback(x):
    pass

# Inicia la captura de la webcam
cap = cv2.VideoCapture(0)

# Crea una ventana para las trackbars
cv2.namedWindow('Trackbars')
# Define un tamaño personalizado para la ventana de trackbars
cv2.resizeWindow('Trackbars', 600, 250)  # Ancho = 600 píxeles, Alto = 400 píxeles

# Crea trackbars para ajustar los valores H, S, V
# USB - Azul
#H_Min_init = 90
#H_Max_init = 150
#S_Min_init = 50
#S_Max_init = 200
#V_Min_init = 80
#V_Max_init = 170

# Cubo rubix - Verde
H_Min_init = 50
H_Max_init = 80
S_Min_init = 80
S_Max_init = 255
V_Min_init = 60
V_Max_init = 255

area_min = 0.05 * (width * height)

# Crea trackbars para ajustar los valores H, S, V
cv2.createTrackbar('H Min', 'Trackbars', H_Min_init , 179, callback)
cv2.createTrackbar('H Max', 'Trackbars', H_Max_init , 179, callback)
cv2.createTrackbar('S Min', 'Trackbars', S_Min_init, 255, callback)
cv2.createTrackbar('S Max', 'Trackbars', S_Max_init, 255, callback)
cv2.createTrackbar('V Min', 'Trackbars', V_Min_init, 255, callback)
cv2.createTrackbar('V Max', 'Trackbars', V_Max_init, 255, callback)

while True:
    # Lee la imagen de la webcam
    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.resize(frame, (width, height)) 

    # Convierte la imagen de BGR a HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Obtiene los valores de las trackbars
    h_min = cv2.getTrackbarPos('H Min', 'Trackbars')
    s_min = cv2.getTrackbarPos('S Min', 'Trackbars')
    v_min = cv2.getTrackbarPos('V Min', 'Trackbars')
    h_max = cv2.getTrackbarPos('H Max', 'Trackbars')
    s_max = cv2.getTrackbarPos('S Max', 'Trackbars')
    v_max = cv2.getTrackbarPos('V Max', 'Trackbars')

    # Define los límites del filtro HSV
    lower_hsv = np.array([h_min, s_min, v_min])
    upper_hsv = np.array([h_max, s_max, v_max])

    # Aplica desenfoque gaussiano para reducir el ruido
    blurred = cv2.GaussianBlur(hsv, (15, 15), 0)

    # Aplica el filtro de color en la imagen desenfocada
    mask = cv2.inRange(blurred, lower_hsv, upper_hsv)

    # Erosión y dilatación para eliminar ruido en la máscara
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Aplica la máscara a la imagen original
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Encuentra objetos segun el filtro de color
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < area_min:
            cv2.drawContours(frame, contour, -1, (255, 0, 255), 7)
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            x, y, w, h = cv2.boundingRect(approx)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 5)
            center = (x + w // 2, y + h // 2)
            cv2.circle(frame, center, 5, (0, 0, 255), cv2.FILLED)

            #Revisamos si el objeto esta de lado derecho o izquierdo
            objeto_x = x + w // 2

            if objeto_x < (width // 2 - x_threshold):
                cv2.putText(frame, f"Objeto a la izquierda", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            elif objeto_x > (width // 2 + x_threshold):
                cv2.putText(frame, f"Objeto a la derecha", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            else:
                cv2.putText(frame, f"Objeto en rango", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            #Revisamos si el objeto esta arriba o abajo
            objeto_y = y + h // 2

            if objeto_y < (height // 2 - y_threshold):
                cv2.putText(frame, f"Objeto arriba", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            elif objeto_y > (height // 2 + y_threshold):
                cv2.putText(frame, f"Objeto abajo", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            else:
                cv2.putText(frame, f"Objeto en rango", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


    # Dibujar lineas de referencia
    # Para x
    cv2.line(frame, (width//2 - x_threshold, 0), (width//2 - x_threshold, height), (255,0,0), 3)
    cv2.line(frame, (width//2 + x_threshold, 0), (width//2 + x_threshold, height), (255,0,0), 3)
    # Para y
    cv2.line(frame, (0, height//2 - y_threshold), (width, height//2 - y_threshold), (255,0,0), 3)
    cv2.line(frame, (0, height//2 + y_threshold), (width, height//2 + y_threshold), (255,0,0), 3)


    # Muestra la imagen original, la imagen filtrada y la imagen filtrada sobrepuesta en la original
    cv2.imshow('Original', frame)
    cv2.imshow('Mask', mask)
    cv2.imshow('Filtrado', result)

    # Salir cuando se presiona 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera la captura y cierra las ventanas
cap.release()
cv2.destroyAllWindows()
