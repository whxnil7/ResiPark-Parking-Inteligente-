import sys
import datetime
import time
import cv2
import re
import sqlite3
import os
from collections import defaultdict

from paddleocr import PaddleOCR
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QMainWindow, QTabWidget
)
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import QTimer, Qt, pyqtSignal

from ultralytics import YOLO

# --- Configuración Global ---
# Modelos de Acceso
MODELO_PLACAS_PATH = 'models/runs/detect/placas_v112/weights/best.pt'
MODELO_VEHICULOS_PATH = "models/best_type.pt"
# Modelo de Monitoreo de Estacionamiento
MODELO_PARKING_SLOTS_PATH = 'models/parkinslotrun/parking/weights/best.pt'

# Base de datos
DATABASE_PATH = 'database/estacionamiento.db'

# Parámetros de Detección de Acceso
CONFIDENCE_THRESHOLD_PLACAS = 0.6
CONFIDENCE_THRESHOLD_VEHICLE = 0.5
NOMBRES_VEHICULOS = [
    "Persona", "Auto", "Bicicleta", "Bus", "Bus Interurbano", 
    "Bus Articulado", "Camion", "Camionmas2ejes", "Ciclos", "Minibus rural",
    "Moto", "Taxi basico", "Taxi Bus Publico", "Taxi Colectivo", "Taxi bus privado",
    "Transporte Escolar", "Semáforo", "Camioneta (Pickup)"
]
CONFIRMATION_THRESHOLD = 4
PAUSE_AFTER_DETECTION_MS = 3000
VIDEO_DISPLAY_SIZE = (800, 450)
OCR_CONFIDENCE_THRESHOLD = 0.6
COOLDOWN_SECONDS = 15 # Reducido para pruebas más rápidas

# --- Funciones de Base de Datos ---
# --- Funciones de Base de Datos ---
def inicializar_base_de_datos():
    """
    Inicializa la base de datos.
    1. Asegura que el directorio y las tablas existan.
    2. Limpia todos los estacionamientos, poniéndolos en estado 'Libre'.
    """
    db_dir = os.path.dirname(DATABASE_PATH)
    os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Crear tablas si no existen (no hará nada si ya existen)
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        patente TEXT PRIMARY KEY,
        tipo TEXT NOT NULL CHECK(tipo IN ('Estudiante', 'Profesor')),
        activo INTEGER NOT NULL DEFAULT 1
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS estacionamientos (
        id_espacio TEXT PRIMARY KEY,
        estado TEXT NOT NULL CHECK(estado IN ('Libre', 'Ocupado', 'Reservado')),
        patente_ocupante TEXT,
        hora_ingreso TEXT,
        FOREIGN KEY (patente_ocupante) REFERENCES usuarios(patente)
    )''')

    # --- INICIO DE LA MODIFICACIÓN ---
    # Limpiar el estado de todos los estacionamientos al iniciar la aplicación.
    # Esto elimina reservas y ocupaciones de la sesión anterior.
    print("[INFO] Limpiando estados de estacionamiento de la sesión anterior...")
    cursor.execute("""
        UPDATE estacionamientos 
        SET 
            estado = 'Libre', 
            patente_ocupante = NULL, 
            hora_ingreso = NULL
    """)
    # --- FIN DE LA MODIFICACIÓN ---
    
    conn.commit()
    conn.close()
    print("[INFO] Base de datos inicializada y limpia en:", DATABASE_PATH)
# --- Pestaña 1: Control de Acceso ---
class AccessControlTab(QWidget):
    # Señal que se emitirá cuando el estado de un estacionamiento cambie
    spot_state_changed = pyqtSignal()

    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self.video_path = None
        self.cap = None
        
        print("[INFO] [Acceso] Cargando modelos...")
        self.model_placas = YOLO(MODELO_PLACAS_PATH)
        self.model_vehiculos = YOLO(MODELO_VEHICULOS_PATH)
        self.ocr_reader = PaddleOCR(use_angle_cls=True, lang='en')
        
        # Zona de detección
        w, h = VIDEO_DISPLAY_SIZE
        zone_width = int(w * 0.4)
        self.detection_zone = ((w - zone_width) // 2, 200, zone_width, (h - zone_width) // 2)

        self.timer_video = QTimer(self)
        self.timer_video.timeout.connect(self.update_frame)
        self.pause_timer = QTimer(self)
        self.pause_timer.setSingleShot(True)
        self.pause_timer.timeout.connect(self.resume_detection)
        
        self.detection_paused = False
        self.detection_buffer = defaultdict(int)
        self.recent_plates = {}
        
        self.initUI()
    
    def initUI(self):
        main_layout = QVBoxLayout()
        video_group = QGroupBox("📷 Video en vivo: Circulación Vehicular")
        video_layout = QVBoxLayout()

        self.video_label = QLabel("Seleccione un video para comenzar el monitoreo.")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 16px;")
        self.video_label.setFixedSize(*VIDEO_DISPLAY_SIZE)

        video_layout.addWidget(self.video_label)
        choose_video_btn = QPushButton("📁 Elegir archivo de video")
        choose_video_btn.clicked.connect(self.choose_video)
        video_layout.addWidget(choose_video_btn)
        video_group.setLayout(video_layout)

        detect_group = QGroupBox("🔎 Detección en Vivo")
        detect_layout = QGridLayout()
        self.patente_lbl = QLabel("Patente: --")
        self.vehiculo_tipo_lbl = QLabel("Tipo Vehículo: --")
        self.tipo_lbl = QLabel("Tipo de usuario: --")
        self.hora_lbl = QLabel("Hora ingreso: --:--:--")
        self.estac_lbl = QLabel("Estacionamiento: --")
        self.estado_lbl = QLabel("Estado: Esperando vehículo...")
        
        for lbl in [self.patente_lbl, self.vehiculo_tipo_lbl, self.tipo_lbl, self.hora_lbl, self.estac_lbl]:
            lbl.setStyleSheet("font-size: 14px;")
        self.estado_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #888888;")
        
        detect_layout.addWidget(self.patente_lbl, 0, 0)
        detect_layout.addWidget(self.vehiculo_tipo_lbl, 0, 1)
        detect_layout.addWidget(self.tipo_lbl, 1, 0)
        detect_layout.addWidget(self.hora_lbl, 1, 1)
        detect_layout.addWidget(self.estac_lbl, 2, 0)
        detect_layout.addWidget(self.estado_lbl, 3, 0, 1, 2)
        detect_group.setLayout(detect_layout)

        table_group = QGroupBox("🗂️ Registros de Ingreso Recientes")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Patente", "Tipo Vehículo", "Tipo Usuario", "Hora ingreso", "Estac."])
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)

        sim_btn = QPushButton("Simular entrada de vehículo (BCFG34)")
        sim_btn.clicked.connect(self.simulate_entry)

        main_layout.addWidget(video_group)
        main_layout.addWidget(detect_group)
        main_layout.addWidget(table_group)
        main_layout.addWidget(sim_btn)
        self.setLayout(main_layout)

    def choose_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de video", "", "Videos (*.mp4 *.avi *.mov)")
        if file_path:
            self.video_path = file_path
            if self.cap: self.cap.release()
            self.cap = cv2.VideoCapture(self.video_path)
            self.reset_detection_state()
            self.timer_video.start(30) # Un poco más lento para dar tiempo a la CPU

    def update_frame(self):
        if not self.cap or not self.cap.isOpened(): return
        ret, frame = self.cap.read()
        if not ret: self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0); return

        frame = cv2.resize(frame, VIDEO_DISPLAY_SIZE)
        display_frame = frame.copy()

        if not self.detection_paused:
            self.process_frame_with_zone(frame, display_frame)
        else:
            self.estado_lbl.setText("Estado: Procesando entrada...")
            self.estado_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #E67E22;")

        self.clean_cooldown_list()
        self.update_display(display_frame)

    def process_frame_with_zone(self, frame_original, frame_to_annotate):
        resultados_veh = self.model_vehiculos(frame_original, conf=CONFIDENCE_THRESHOLD_VEHICLE, verbose=False, classes=[1, 10, 11, 12, 13, 14, 15, 17])[0]
        
        for box in resultados_veh.boxes:
            coords = box.xyxy[0].int().tolist()
            if self.box_intersects_zone(coords):
                x1v, y1v, x2v, y2v = coords
                cv2.rectangle(frame_to_annotate, (x1v, y1v), (x2v, y2v), (0, 255, 0), 3)
                
                vehicle_crop = frame_original[y1v:y2v, x1v:x2v]
                if vehicle_crop.size == 0: continue

                resultados_placas = self.model_placas(vehicle_crop, conf=CONFIDENCE_THRESHOLD_PLACAS, verbose=False)[0]
                if not resultados_placas.boxes: continue

                for box_placa in resultados_placas.boxes:
                    x1p_crop, y1p_crop, x2p_crop, y2p_crop = box_placa.xyxy[0].int().tolist()
                    roi = vehicle_crop[y1p_crop:y2p_crop, x1p_crop:x2p_crop]
                    plate_found = self.ocr_on_plate(roi)

                    if plate_found and plate_found not in self.recent_plates:
                        self.detection_buffer[plate_found] += 1
                        if self.detection_buffer[plate_found] >= CONFIRMATION_THRESHOLD:
                            cls_id = int(box.cls[0])
                            tipo_vehiculo = NOMBRES_VEHICULOS[cls_id] if cls_id < len(NOMBRES_VEHICULOS) else "Desconocido"
                            self.process_confirmed_plate(plate_found, tipo_vehiculo)
                            self.detection_buffer.clear()
                            return
                break

    def process_confirmed_plate(self, plate, tipo_vehiculo):
        current_time = time.time()
        if plate in self.recent_plates and current_time - self.recent_plates[plate] < COOLDOWN_SECONDS:
            return

        print(f"[INFO] [Acceso] Patente '{plate}' confirmada. Verificando...")
        self.recent_plates[plate] = current_time
        
        tipo_usuario = self.check_user_in_db(plate)
        hora = datetime.datetime.now().strftime("%H:%M:%S")

        estado_msg, color_hex, estac_asignado = "", "", "---"

        if tipo_usuario:
            estac_asignado = self.asignar_espacio_libre(plate, hora)
            if estac_asignado:
                estado_msg = f"Ingreso exitoso. Diríjase a {estac_asignado}"
                color_hex = "#2ECC71"  # Verde
                self.spot_state_changed.emit() # ¡EMITIR SEÑAL!
            else:
                estado_msg = "ACCESO DENEGADO: Estacionamiento LLENO"
                color_hex = "#F39C12" # Naranja
        else:
            estado_msg = "ACCESO DENEGADO: Patente no registrada"
            color_hex = "#E74C3C"  # Rojo

        self.patente_lbl.setText(f"Patente: {plate}")
        self.vehiculo_tipo_lbl.setText(f"Tipo Vehículo: {tipo_vehiculo}")
        self.tipo_lbl.setText(f"Tipo Usuario: {tipo_usuario or 'No Registrado'}")
        self.hora_lbl.setText(f"Hora: {hora}")
        self.estac_lbl.setText(f"Estac.: {estac_asignado}")
        self.estado_lbl.setText(f"Estado: {estado_msg}")
        self.estado_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color_hex};")
        
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(plate))
        self.table.setItem(0, 1, QTableWidgetItem(tipo_vehiculo))
        self.table.setItem(0, 2, QTableWidgetItem(tipo_usuario or 'No Registrado'))
        self.table.setItem(0, 3, QTableWidgetItem(hora))
        self.table.setItem(0, 4, QTableWidgetItem(estac_asignado))
        
        self.pause_detection()

    def asignar_espacio_libre(self, patente, hora):
        """Busca un espacio libre en la DB, lo ocupa y devuelve su ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_espacio FROM estacionamientos WHERE estado = 'Libre' ORDER BY id_espacio LIMIT 1")
        resultado = cursor.fetchone()
        
        if resultado:
            id_espacio = resultado[0]
            print(f"[INFO] [Acceso] Reservando espacio '{id_espacio}' para la patente '{patente}'.")
            # <<< CAMBIO 2: CAMBIAR EL ESTADO A 'Reservado' >>>
            cursor.execute("""
                UPDATE estacionamientos 
                SET estado = 'Reservado', patente_ocupante = ?, hora_ingreso = ? 
                WHERE id_espacio = ?
            """, (patente, hora, id_espacio))
            self.conn.commit()
            return id_espacio
        else:
            print("[WARN] [Acceso] No hay espacios de estacionamiento libres.")
            return None
    def simulate_entry(self):
        test_plate = "BCFG34"
        test_vehicle_type = "Auto"
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO usuarios (patente, tipo, activo) VALUES (?, 'Profesor', 1)", (test_plate,))
        self.conn.commit()
        self.process_confirmed_plate(test_plate, test_vehicle_type)
        QMessageBox.information(self, "Simulación", f"Se ha simulado la entrada del vehículo {test_vehicle_type} con patente {test_plate}.")

    # --- Métodos de ayuda y UI (sin cambios mayores) ---
    def update_display(self, frame):
        x, y, w, h = self.detection_zone
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
        cv2.putText(frame, "ZONA DE DETECCION", (x + 5, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

    def box_intersects_zone(self, box_coords):
        zx, zy, zw, zh = self.detection_zone; zx2, zy2 = zx + zw, zy + zh
        bx1, by1, bx2, by2 = box_coords
        return bx1 < zx2 and bx2 > zx and by1 < zy2 and by2 > zy

    def pause_detection(self):
        self.detection_paused = True
        self.pause_timer.start(PAUSE_AFTER_DETECTION_MS)

    def resume_detection(self):
        self.detection_paused = False
        self.reset_ui_labels()
        
    def reset_ui_labels(self):
        self.patente_lbl.setText("Patente: --"); self.vehiculo_tipo_lbl.setText("Tipo Vehículo: --")
        self.tipo_lbl.setText("Tipo de usuario: --"); self.hora_lbl.setText("Hora ingreso: --:--:--")
        self.estac_lbl.setText("Estacionamiento: --"); self.estado_lbl.setText("Estado: Esperando vehículo...")
        self.estado_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #888888;")

    def reset_detection_state(self):
        self.detection_paused = False; self.pause_timer.stop()
        self.detection_buffer.clear(); self.recent_plates.clear()
        self.reset_ui_labels()

    def ocr_on_plate(self, roi):
        if roi is None or roi.size == 0: return ""
        results = self.ocr_reader.predict(roi)
        detected_texts = []
        if not results or not results[0]: return ""
        result_data = results[0]
        if isinstance(result_data, dict):
            if 'rec_texts' in result_data and 'rec_scores' in result_data:
                for text, score in zip(result_data.get('rec_texts', []), result_data.get('rec_scores', [])):
                    if score > OCR_CONFIDENCE_THRESHOLD: detected_texts.append(text)
        elif isinstance(result_data, list):
            for line in result_data:
                try:
                    text, score = line[1]
                    if score > OCR_CONFIDENCE_THRESHOLD: detected_texts.append(text)
                except (IndexError, TypeError, ValueError): continue
        if not detected_texts: return ""
        valid_plates = self.filtrar_patentes(detected_texts)
        return valid_plates[0] if valid_plates else ""


    def filtrar_patentes(self, textos):
        posibles = []
        for t in textos:
            t_limpio = re.sub(r'[^A-Z0-9]', '', t.upper().strip())
            if len(t_limpio) == 6 and any(c.isdigit() for c in t_limpio) and any(c.isalpha() for c in t_limpio):
                posibles.append(t_limpio)
        return posibles

    def check_user_in_db(self, patente):
        cursor = self.conn.cursor()
        cursor.execute("SELECT tipo FROM usuarios WHERE patente = ? AND activo = 1", (patente,))
        row = cursor.fetchone()
        return row[0] if row else None

    def clean_cooldown_list(self):
        current_time = time.time()
        keys_to_delete = [p for p, ts in self.recent_plates.items() if current_time - ts > COOLDOWN_SECONDS]
        for key in keys_to_delete:
            if key in self.recent_plates: del self.recent_plates[key]

    def stop_video(self):
        self.timer_video.stop()
        if self.cap: self.cap.release(); self.cap = None

# --- Pestaña 2: Monitoreo de Estacionamiento ---
class ParkingStatusTab(QWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        print("[INFO] [Monitoreo] Cargando modelo...")
        self.model = self.load_model()
        self.current_image = None
        self.initUI()
        self.refresh_from_db() # Cargar estado inicial de la DB

    def load_model(self):
        try:
            return YOLO(MODELO_PARKING_SLOTS_PATH)
        except Exception as e:
            QMessageBox.critical(self, "Error de Modelo", f"No se pudo cargar el modelo de estacionamientos: {e}")
            return None

    def initUI(self):
        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()

        # Panel Izquierdo (Imagen)
        image_group = QGroupBox("📷 Imagen del Estacionamiento")
        image_layout = QVBoxLayout()
        self.image_label = QLabel("Cargue una imagen para analizar y actualizar el estado de los espacios.")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        image_layout.addWidget(self.image_label)
        image_group.setLayout(image_layout)
        
        choose_image_btn = QPushButton("📁 Analizar Imagen y Actualizar BD")
        choose_image_btn.clicked.connect(self.choose_and_process_image)
        
        left_panel.addWidget(image_group)
        left_panel.addWidget(choose_image_btn)

        # Panel Derecho (Datos)
        summary_group = QGroupBox("📊 Resumen de Ocupación (Desde BD)")
        summary_layout = QGridLayout()
        self.available_lbl = QLabel("Disponibles: 0")
        self.reserved_lbl = QLabel("Reservados: 0") # Nuevo Label
        self.occupied_lbl = QLabel("Ocupados: 0")
        self.total_lbl = QLabel("Total de espacios: 0")
        self.available_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
        self.reserved_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff9b00;") # Amarillo
        self.occupied_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
        self.total_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        summary_layout.addWidget(self.available_lbl, 0, 0)
        summary_layout.addWidget(self.reserved_lbl, 1, 0) # Añadido al layout
        summary_layout.addWidget(self.occupied_lbl, 2, 0)
        summary_layout.addWidget(self.total_lbl, 3, 0)
        summary_group.setLayout(summary_layout)

        table_group = QGroupBox("🗂️ Estado Actual de Espacios (Desde BD)")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID Espacio", "Estado", "Patente Ocupante", "Hora Ingreso"])
        self.table.setColumnWidth(0, 100); self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 120); self.table.setColumnWidth(3, 100)
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)
        
        refresh_btn = QPushButton("🔄 Refrescar Vista desde BD")
        refresh_btn.clicked.connect(self.refresh_from_db)

        right_panel.addWidget(summary_group)
        right_panel.addWidget(table_group)
        right_panel.addWidget(refresh_btn)

        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(right_panel, 1)
        self.setLayout(main_layout)

    def choose_and_process_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if file_path:
            self.current_image = cv2.imread(file_path)
            if self.current_image is not None:
                self.process_image_and_update_db()
            else:
                QMessageBox.warning(self, "Error", "No se pudo cargar la imagen.")

    def process_image_and_update_db(self):
        if self.model is None or self.current_image is None: return

        # Ejecutar la detección en la imagen
        results = self.model(self.current_image, verbose=False)
        
        # Guardar las detecciones ordenadas en caché para usarlas después al dibujar
        self.detections_cache = sorted(results[0].boxes, key=lambda box: (box.xyxy[0][1], box.xyxy[0][0]))
        
        cursor = self.conn.cursor()
        class_names = self.model.model.names
        
        # --- INICIO DE LA LÓGICA DE ACTUALIZACIÓN MEJORADA ---
        print("[INFO] [Monitoreo] Analizando imagen y actualizando base de datos...")
        
        slot_id_counter = 1
        processed_slots_count = 0

        for box in self.detections_cache:
            # Asignar un ID consistente al espacio de estacionamiento
            slot_id = f"E-{slot_id_counter:02d}"
            slot_id_counter += 1
            
            # Determinar el estado FÍSICO del espacio según la detección del modelo
            cls_id = int(box.cls[0].item())
            status_name = class_names[cls_id].lower()
            estado_fisico_detectado = 'Ocupado' if 'occupied' in status_name else 'Libre'

            # 1. Asegurarse de que el espacio exista en la base de datos.
            # Si es la primera vez que se detecta, se inserta como 'Libre'.
            cursor.execute("INSERT OR IGNORE INTO estacionamientos (id_espacio, estado) VALUES (?, 'Libre')", (slot_id,))
            
            # 2. Obtener el estado LÓGICO actual del espacio desde la base de datos.
            cursor.execute("SELECT estado FROM estacionamientos WHERE id_espacio = ?", (slot_id,))
            db_state_row = cursor.fetchone()
            if not db_state_row: continue # Si algo falló, saltar a la siguiente detección
            
            estado_logico_en_db = db_state_row[0]

            # 3. Aplicar la lógica de transición de estados
            if estado_fisico_detectado == 'Ocupado' and estado_logico_en_db != 'Ocupado':
                # CASO A: El modelo ve un coche donde lógicamente no debería haberlo (o estaba reservado).
                # Esto confirma la ocupación, ya sea de una reserva o de una nueva llegada.
                # Se actualiza el estado a 'Ocupado'.
                print(f"[Monitoreo] Espacio {slot_id} detectado como Ocupado (antes {estado_logico_en_db}). Actualizando a 'Ocupado'.")
                cursor.execute("UPDATE estacionamientos SET estado = 'Ocupado' WHERE id_espacio = ?", (slot_id,))
                processed_slots_count += 1

            elif estado_fisico_detectado == 'Libre' and estado_logico_en_db == 'Ocupado':
                # CASO B: El modelo ve un espacio libre donde lógicamente había un coche.
                # Esto significa que un vehículo se ha ido.
                # Se libera el espacio, limpiando la patente y la hora de ingreso.
                print(f"[Monitoreo] Espacio {slot_id} detectado como Libre (antes Ocupado). Actualizando a 'Libre'.")
                cursor.execute("UPDATE estacionamientos SET estado = 'Libre', patente_ocupante = NULL, hora_ingreso = NULL WHERE id_espacio = ?", (slot_id,))
                processed_slots_count += 1
            
            # CASO C (implícito): Si el estado físico detectado es 'Libre' y el estado lógico en la BD es 'Reservado',
            # NO HACEMOS NADA. Esto es crucial, ya que le da tiempo al conductor para llegar a su espacio asignado
            # sin que el sistema lo marque como 'Libre' por error.

            # CASO D (implícito): Si el estado físico coincide con el lógico (Ocupado-Ocupado, Libre-Libre),
            # tampoco se hace nada, ya que la base de datos ya está sincronizada.

        self.conn.commit()
        print(f"[INFO] [Monitoreo] Base de datos actualizada. Se modificaron {processed_slots_count} registros.")
        
        # Después de actualizar la BD, se refresca toda la UI para mostrar los cambios.
        # Esto incluye la tabla, los contadores y las anotaciones en la imagen.
        self.refresh_from_db()

        # Mostrar un mensaje al usuario
        QMessageBox.information(self, "Análisis Completado", 
                                f"Se ha analizado la imagen y actualizado la base de datos.\n"
                                f"Se modificó el estado de {processed_slots_count} espacios.")

    def refresh_from_db(self):
        """Carga los datos desde la BD y actualiza toda la UI (tabla, resumen e imagen)."""
        print("[INFO] [Monitoreo] Refrescando vista completa desde la base de datos.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_espacio, estado, patente_ocupante, hora_ingreso FROM estacionamientos ORDER BY id_espacio")
        rows = cursor.fetchall()
        
        self.table.setRowCount(0)
        occupied_count = 0
        reserved_count = 0
        
        # --- INICIO DE LA LÓGICA DE ACTUALIZACIÓN DE UI ---
        # Define los colores para cada estado
        colors = {
            'Libre': QColor("#2ECC71"),      # Verde
            'Ocupado': QColor("#E74C3C"),    # Rojo
            'Reservado': QColor("#ff9b00")   # Amarillo
        }

        # Itera sobre los datos de la BD para llenar la tabla
        for row_data in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            estado = row_data[1]  # El estado está en la segunda columna (índice 1)
            
            # Contar cada tipo de estado
            if estado == 'Ocupado':
                occupied_count += 1
            elif estado == 'Reservado':
                reserved_count += 1
            
            # Obtener el color correspondiente al estado
            color = colors.get(estado, QColor("white")) # Usa blanco si el estado es desconocido

            # Llenar cada celda de la fila y aplicarle el color de fondo
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data or "---"))
                item.setBackground(color)
                # Opcional: Hacer el texto blanco para mejor contraste en fondos oscuros
                if estado in ['Ocupado', 'Reservado']:
                    item.setForeground(QColor("white"))
                self.table.setItem(row_idx, col_idx, item)
        
        # Actualizar los contadores del resumen
        total_slots = len(rows)
        available_count = total_slots - occupied_count - reserved_count
        
        self.total_lbl.setText(f"Total de espacios: {total_slots}")
        self.occupied_lbl.setText(f"Ocupados: {occupied_count}")
        self.reserved_lbl.setText(f"Reservados: {reserved_count}") # Actualizar el nuevo label
        self.available_lbl.setText(f"Disponibles: {available_count}")

        # Si hay una imagen y detecciones en caché, redibujar las anotaciones
        # para que los colores coincidan con el nuevo estado de la BD.
        if self.current_image is not None and self.detections_cache is not None:
            self.draw_annotations_on_image()

    def draw_annotations_on_image(self):
        """Dibuja las detecciones en la imagen, coloreando según el estado actual de la BD."""
        if self.current_image is None or self.detections_cache is None:
            return
        
        annotated_image = self.current_image.copy()
        
        # --- INICIO DE LA LÓGICA DE DIBUJADO BASADO EN LA BD ---
        # 1. Obtener el estado actual de TODOS los espacios desde la base de datos
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_espacio, estado FROM estacionamientos")
        # Crear un diccionario para un acceso rápido: {'E-01': 'Libre', 'E-02': 'Reservado', ...}
        db_states = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 2. Definir los colores para OpenCV (formato BGR: Azul, Verde, Rojo)
        colors_cv = {
            'Libre': (0, 255, 0),      # Verde
            'Ocupado': (0, 0, 255),    # Rojo
            'Reservado': (0, 155, 255)  # Amarillo
        }

        # 3. Iterar sobre las detecciones cacheadas (las coordenadas de los cuadros)
        slot_id_counter = 1
        for box in self.detections_cache:
            slot_id = f"E-{slot_id_counter:02d}"
            slot_id_counter += 1
            
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            
            # 4. Usar el estado de la BD para elegir el color, no la detección física
            estado_logico_actual = db_states.get(slot_id, 'Libre') # Default a 'Libre' si no se encuentra
            color = colors_cv.get(estado_logico_actual, (255, 255, 255)) # Blanco por defecto

            # Dibujar el rectángulo con el color correspondiente
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 3) # Borde más grueso
            
            # Añadir una etiqueta con el ID del espacio para fácil identificación
            # Poner un fondo negro al texto para que sea legible sobre cualquier color
            (w, h), _ = cv2.getTextSize(slot_id, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_image, (x1, y1 - h - 5), (x1 + w, y1), (0,0,0), -1)
            cv2.putText(annotated_image, slot_id, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
            
        # 5. Mostrar la imagen final anotada en la interfaz
        self.display_image(annotated_image)

    def display_image(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

# --- Ventana Principal de la Aplicación ---
class SmartParkingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Integrado de Gestión de Estacionamiento")
        self.setGeometry(50, 50, 1300, 900)

        # Conexión a la base de datos compartida
        self.db_connection = sqlite3.connect(DATABASE_PATH)

        # Crear el widget de pestañas
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Crear e instanciar las pestañas
        self.access_tab = AccessControlTab(self.db_connection)
        self.status_tab = ParkingStatusTab(self.db_connection)

        # Añadir las pestañas al widget
        self.tabs.addTab(self.access_tab, "🛂 Control de Acceso")
        self.tabs.addTab(self.status_tab, "📊 Estado del Estacionamiento")

        # Conectar la señal de la pestaña de acceso al slot de la pestaña de estado
        self.access_tab.spot_state_changed.connect(self.status_tab.refresh_from_db)

    def closeEvent(self, event):
        """Asegurarse de cerrar todo correctamente."""
        print("[INFO] Cerrando aplicación...")
        self.access_tab.stop_video()
        self.db_connection.close()
        event.accept()

if __name__ == '__main__':
    # Inicializar la base de datos antes de iniciar la app
    inicializar_base_de_datos()
    
    app = QApplication(sys.argv)
    window = SmartParkingApp()
    window.show()
    sys.exit(app.exec_())