import os
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

def generate_test_prescriptions(num_images=10, output_dir="test_prescriptions"):
    """
    OCR testi için sahte ama gerçekçi reçete görselleri oluşturur.
    """
    # Çıktı klasörünü oluştur
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ Klasör oluşturuldu: {output_dir}")

    # Rastgele veri havuzları
    doctors = [
        "Dr. Ahmet Yılmaz (Dahiliye Uzmanı)",
        "Dr. Ayşe Demir (Kardiyoloji Uzmanı)",
        "Dr. Mehmet Kaya (Aile Hekimi)",
        "Dr. Zeynep Çelik (Göz Hastalıkları Uzmanı)",
        "Dr. Can Özdemir (Kulak Burun Boğaz)"
    ]
    
    patients = [
        "Ali Veli", "Fatma Şahin", "Hasan Öztürk", 
        "Elif Yıldız", "Mustafa Demir", "Aylin Korkmaz",
        "Burak Arslan", "Selin Aydın"
    ]
    
    medications = [
        ("Paracetamol 500 mg", "20 Tablet - Günde 3 kez 1 tablet"),
        ("Amoxicillin 500 mg", "14 Kapsül - Günde 2 kez 1 kapsül"),
        ("Omeprazole 20 mg", "28 Kapsül - Sabah aç karnına 1 kapsül"),
        ("Metformin 500 mg", "60 Tablet - Günde 2 kez 1 tablet"),
        ("Atorvastatin 20 mg", "30 Tablet - Akşamları 1 tablet"),
        ("Lisinopril 10 mg", "30 Tablet - Günde 1 kez 1 tablet"),
        ("Salbutamol 100 mcg", "1 İnhaler - Gerektiğinde 2 puf"),
        ("Ibuprofen 400 mg", "20 Tablet - Ağrı durumunda 1 tablet"),
        ("Cetirizine 10 mg", "14 Tablet - Günde 1 kez 1 tablet"),
        ("Pantoprazol 40 mg", "14 Tablet - Sabahları 1 tablet")
    ]
    
    pharmacies = [
        "Şifa Eczanesi", "Can Eczanesi", "Güneş Eczanesi", 
        "Merkez Eczanesi", "Yaşam Eczanesi"
    ]

    # Font ayarları (Sistem fontu yoksa varsayılanı kullan)
    try:
        # Windows için yaygın fontlar
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_medium = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 18)
        font_tiny = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        # Fallback
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()

    print(f"🚀 {num_images} adet sahte reçete oluşturuluyor...\n")

    for i in range(1, num_images + 1):
        # A4'e yakın oranlar (800x1100) - OCR için ideal
        img = Image.new('RGB', (800, 1100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Rastgele veriler seç
        doctor = random.choice(doctors)
        patient = random.choice(patients)
        pharmacy = random.choice(pharmacies)
        
        # Rastgele tarih (son 30 gün içinde)
        random_date = datetime.now() - timedelta(days=random.randint(1, 30))
        date_str = random_date.strftime("%d.%m.%Y")
        
        # Rastgele 2-4 ilaç seç
        num_meds = random.randint(2, 4)
        selected_meds = random.sample(medications, num_meds)
        
        # --- ÇİZİM BAŞLANGICI ---
        
        # 1. Başlık ve Çizgiler
        draw.line([(50, 80), (750, 80)], fill='black', width=2)
        draw.text((50, 30), "REÇETE", fill='black', font=font_large)
        draw.text((50, 95), doctor, fill='black', font=font_medium)
        draw.text((50, 125), "Diploma No: " + str(random.randint(10000, 99999)), fill='black', font=font_small)
        
        # 2. Hasta Bilgileri
        draw.line([(50, 180), (750, 180)], fill='black', width=1)
        draw.text((50, 195), f"Hasta Adı Soyadı: {patient}", fill='black', font=font_medium)
        draw.text((50, 230), f"Tarih: {date_str}", fill='black', font=font_small)
        draw.text((400, 230), f"TC Kimlik No: {random.randint(10000000000, 99999999999)}", fill='black', font=font_small)
        
        # 3. İlaç Listesi (Rp)
        draw.line([(50, 290), (750, 290)], fill='black', width=1)
        draw.text((50, 305), "Rp (Reçete):", fill='black', font=font_medium)
        
        y_pos = 350
        for med_name, dosage in selected_meds:
            draw.text((70, y_pos), f"• {med_name}", fill='black', font=font_medium)
            draw.text((90, y_pos + 30), dosage, fill='black', font=font_small)
            y_pos += 90
            
        # 4. Alt Bilgi ve İmza
        draw.line([(50, y_pos + 40), (750, y_pos + 40)], fill='black', width=1)
        draw.text((50, y_pos + 60), "Not: İlaçları belirtilen dozda ve sürede kullanınız.", fill='black', font=font_small)
        draw.text((50, y_pos + 100), "Hekim İmzası:", fill='black', font=font_small)
        draw.line([(180, y_pos + 120), (400, y_pos + 120)], fill='black', width=2)
        
        # 5. Eczane Kaşesi (Sağ alt köşe)
        draw.rectangle([(500, y_pos + 60), (750, y_pos + 150)], outline='black', width=2)
        draw.text((520, y_pos + 80), pharmacy, fill='black', font=font_medium)
        draw.text((520, y_pos + 110), "Eczacı: [İsim]", fill='black', font=font_small)
        
        # 6. Kenarlık
        draw.rectangle([(10, 10), (790, 1090)], outline='black', width=3)
        
        # Kaydet
        filename = f"prescription_{i:02d}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, dpi=(300, 300))
        print(f"✅ Oluşturuldu: {filename} ({len(selected_meds)} ilaç içeriyor)")

    print(f"\n🎉 Tamamlandı! Tüm görseller '{output_dir}' klasöründe.")
    print("💡 İpucu: Bu görselleri HantaMed Assist ana sayfasından yükleyerek test edin.")

if __name__ == "__main__":
    generate_test_prescriptions(num_images=10)