from ultralytics import YOLO
import torch

def entrenar_yolo():

    # Cargar el modelo base (puede ser 'yolov8n', 'yolov8s', 'yolov8m', etc.)
    model = YOLO('yolo11m.pt')  # puedes usar también yolov8s.pt

    if not torch.cuda.is_available():
        print("⚠️ GPU no disponible. Se usará CPU.")
    else:
        print(f"✅ Entrenando en GPU: {torch.cuda.get_device_name(0)}")

    torch.cuda.empty_cache()


    # Entrenar con tu dataset
    model.train(
        data='C:/Users/aceve/Desktop/Carpetas/Universidad/2025-1/Visión por computador/Proyecto/models/carpat-1/data.yaml',
        epochs=50,
        imgsz=640,
        batch=16,
        device=0, 
        name='placas_v11',
        project='runs/detect'
    )


if __name__ == '__main__':
    entrenar_yolo()