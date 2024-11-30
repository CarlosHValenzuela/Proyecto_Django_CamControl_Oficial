import cv2
import pytesseract
import re
import time
from core.models import Auto, Persona, RegistroEntradaSalida
from django.utils import timezone  # Importar timezone para obtener la hora actual

# Configuración de Tesseract-OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\carlo\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Definir last_detected_plate a nivel de módulo
last_detected_plate = {'plate': None, 'registrada': False, 'persona': None, 'last_detected_time': None}

# Función para validar y formatear la patente detectada
def format_plate(text):
    """
    Valida y formatea el texto detectado como una patente válida.
    """
    text = re.sub(r'\W+', '', text).upper()  # Limpiar texto y convertir a mayúsculas
    match = re.match(r'^([A-Z]{2}\d{4}|[A-Z]{4}\d{2})$', text)  # Validar formato de patente
    return text if match else None

# Función para buscar caracteres dentro de un contorno potencial de la matrícula
def extract_characters(roi):
    """
    Extrae caracteres individuales de la región de interés.
    """
    _, binary = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY_INV)  # Binarización invertida
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Lista para almacenar caracteres detectados
    characters = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)
        
        # Filtrar caracteres basados en tamaño y relación de aspecto
        if 0.2 < aspect_ratio < 1.0 and h > 15:
            char_roi = binary[y:y + h, x:x + w]
            char_roi = cv2.resize(char_roi, (20, 40))  # Normalizar tamaño
            characters.append(char_roi)

    return characters

# Generador de frames con detección de caracteres
def generate_frames():
    camera = cv2.VideoCapture(0) #Utilizar Camara que tiene el equipo
    camera = cv2.VideoCapture("rtsp://admin:admin2002@192.168.0.86:554/cam/realmonitor?channel=1&subtype=0") #Utilizar Camara IP
    while True:
        ret, frame = camera.read()
        if not ret:
            print("Error al capturar el video. Verifica la cámara.")
            break

        # Verificar si han pasado 30 segundos desde la última detección
        if last_detected_plate['last_detected_time']:
            elapsed_time = timezone.now() - last_detected_plate['last_detected_time']
            if elapsed_time.seconds < 10:  # Si no han pasado 30 segundos, saltar el ciclo
                print(f"Cooldown activado: {10 - elapsed_time.seconds} segundos restantes.")
                continue

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

            # Reiniciar last_detected_plate en cada detección
            last_detected_plate['plate'] = None
            last_detected_plate['registrada'] = False
            last_detected_plate['persona'] = None

            if plate_text:
                last_detected_plate['plate'] = plate_text
                last_detected_plate['last_detected_time'] = timezone.now()  # Registrar la hora de detección
                
                try:
                    vehicle = Auto.objects.get(placa=plate_text)
                    last_detected_plate['registrada'] = True
                    last_detected_plate['persona'] = vehicle.persona.nombre
                    
                    # Registrar la entrada en el modelo RegistroEntradaSalida si el vehículo está registrado
                    if last_detected_plate['registrada']:
                        now = timezone.now()  # Obtener la hora actual
                        registro = RegistroEntradaSalida(
                            persona=vehicle.persona,
                            auto=vehicle,
                            hora_entrada=now,
                            tipo_entrada='V'  # Tipo de entrada es 'V' para Vehículo
                        )
                        registro.save()  # Guardar el registro en la base de datos
                        print(f"Vehículo {plate_text} registrado a las {now}")

                except Auto.DoesNotExist:
                    print(f"Patente detectada: {plate_text} - Registrada: No")
            else:
                print("No se pudo validar la patente detectada.")

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
