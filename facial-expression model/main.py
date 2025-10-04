from ultralytics import YOLO

# Load an untrained YOLO model
model = YOLO("yolov8n.yaml")  

# Train the model
model.train(
    data="G:/Dataset/data.yaml",  # Path to dataset config
    epochs=50,  # Training for 50 epochs
    batch=8,  # Adjust based on your GPU memory
    imgsz=640  # Image size for training
)

print("✅ Training complete!")
