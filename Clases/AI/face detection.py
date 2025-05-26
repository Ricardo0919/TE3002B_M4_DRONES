import cv2
import mediapipe as mp

# Inicializar MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Parámetros de control
threshold_x = 50
threshold_y = 50

# Iniciar captura de video
cap = cv2.VideoCapture(0)

with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6) as face_detection:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip horizontal para efecto espejo
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detección de rostro
        results = face_detection.process(frame_rgb)

        # Calcular centro de la imagen
        centro_img = (w // 2, h // 2)

        if results.detections:
            for detection in results.detections:
                # Obtener bounding box normalizado (entre 0 y 1)
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                ancho = int(bbox.width * w)
                alto = int(bbox.height * h)

                # Calcular centro del rostro
                centro_rostro = (x + ancho // 2, y + alto // 2)

                # Dibujar bbox
                cv2.rectangle(frame, (x, y), (x + ancho, y + alto), (0, 255, 0), 2)
                cv2.circle(frame, centro_rostro, 5, (255, 0, 0), -1)
                cv2.circle(frame, centro_img, 5, (0, 0, 255), -1)

                # Comparar posiciones
                dx = centro_rostro[0] - centro_img[0]
                dy = centro_rostro[1] - centro_img[1]

                mensaje = "Buscando rostro..." 

                # Determinar movimiento
                if abs(dx) < threshold_x and abs(dy) < threshold_y:
                    mensaje = "Rostro centrado (mantener posición)"
                elif dx < -threshold_x:
                    mensaje = "Mover a la izquierda"
                elif dx > threshold_x:
                    mensaje = "Mover a la derecha"

                break  # solo procesar el primer rostro

        # Mostrar mensaje
        cv2.putText(frame, mensaje, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow("Face follower", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
