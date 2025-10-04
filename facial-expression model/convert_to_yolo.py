import os
import glob
from PIL import Image

# Define class names based on folder names
class_names = ["angry", "happy", "sad", "neutral", "surprise", "disgust", "fear"]
class_map = {name: idx for idx, name in enumerate(class_names)}

# Paths
dataset_path = r"G:\Dataset" 
yolo_labels_path = os.path.join(dataset_path, "labels")
os.makedirs(yolo_labels_path, exist_ok=True)

def convert_to_yolo_format(image_path, label, save_path):
    img = Image.open(image_path)
    width, height = img.size

    # Create a full-image bounding box (since we are classifying, not detecting)
    x_center = 0.5
    y_center = 0.5
    bbox_width = 1.0
    bbox_height = 1.0

    # Save label file
    label_txt_path = os.path.join(save_path, os.path.basename(image_path).replace(".jpg", ".txt"))
    with open(label_txt_path, "w") as f:
        f.write(f"{label} {x_center} {y_center} {bbox_width} {bbox_height}\n")

# Process each image in train and test folders
for split in ["train", "test"]:
    split_path = os.path.join(dataset_path, split)
    save_path = os.path.join(yolo_labels_path, split)
    os.makedirs(save_path, exist_ok=True)

    for class_name in class_names:
        image_folder = os.path.join(split_path, class_name)
        for image_file in glob.glob(os.path.join(image_folder, "*.jpg")):
            convert_to_yolo_format(image_file, class_map[class_name], save_path)

print("✅ Dataset converted to YOLO format!")
