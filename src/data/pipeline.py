from src.data.synthetic_generator import generate_synthetic_data
from src.data.preprocess import preprocess_images

if __name__ == "__main__":
    generate_synthetic_data()
    preprocess_images()
    print("Veri seti ve ön işleme tamamlandı.")