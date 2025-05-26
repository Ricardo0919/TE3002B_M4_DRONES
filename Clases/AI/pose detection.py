import cv2
import mediapipe as mp

# Inicializar MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Captura de video
cap = cv2.VideoCapture(0)

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Espejo
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = pose.process(rgb)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            hombro_izq = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            codo_izq = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW.value]
            muneca_izq = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST.value]

            hombro_der = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            codo_der = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            muneca_der = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST.value]

            # Verificar si ambas muñecas están por encima de los hombros y extendidas hacia arriba
            if (muneca_izq.y < hombro_izq.y) and (codo_izq.y < hombro_izq.y) and (muneca_der.y < hombro_der.y) and (codo_der.y < hombro_der.y):
                mensaje = "Despegue activado"
            else:
                mensaje = "Esperando comando"
        # Mostrar mensaje
        cv2.putText(frame, mensaje, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow("Pose detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
