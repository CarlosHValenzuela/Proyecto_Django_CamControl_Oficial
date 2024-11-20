# core/utils.py
import cv2
import pytesseract
import re
import time
from core.models import Auto

# Configuración de Tesseract-OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\carlo\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Definir last_detected_plate a nivel de módulo
last_detected_plate = {'plate': None, 'registrada': False, 'persona': None}

# Función para validar y formatear la patente detectada
def format_plate(text):
    text = re.sub(r'\W+', '', text).upper()
    match = re.match(r'^([A-Z]{2}\d{4}|[A-Z]{4}\d{2})$', text)
    if match:
        return text
    return None

def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        # Procesamiento de la imagen
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(gray, 30, 200)
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        plate = None
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)
            if len(approx) == 4:
                plate = approx
                break

        if plate is not None:
            x, y, w, h = cv2.boundingRect(plate)
            roi = gray[y:y + h, x:x + w]
            roi = cv2.resize(roi, (400, 200))
            raw_text = pytesseract.image_to_string(roi, config='--psm 8').strip()
            plate_text = format_plate(raw_text)
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Color verde, grosor 2

            if plate_text:
                # Reiniciar last_detected_plate antes de asignar el nuevo valor
                last_detected_plate['plate'] = plate_text
                last_detected_plate['registrada'] = False
                last_detected_plate['persona'] = None
                
                try:
                    vehicle = Auto.objects.get(placa=plate_text)
                    last_detected_plate['registrada'] = True
                    last_detected_plate['persona'] = vehicle.persona.nombre
                except Auto.DoesNotExist:
                    # Ya se asignaron los valores por defecto arriba
                    pass

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
