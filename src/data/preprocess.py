import os
from PIL import Image

def preprocess_images(input_dir="data/raw/synth_imgs", output_dir="data/processed", size=(224,224)):
    os.makedirs(output_dir, exist_ok=True)
    for fname in os.listdir(input_dir):
        if fname.endswith(('.png', '.jpg')):
            img = Image.open(os.path.join(input_dir, fname)).convert('RGB')
            img = img.resize(size)
            img.save(os.path.join(output_dir, fname))