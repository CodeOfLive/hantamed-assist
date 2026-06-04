"""
Add sample drug data to drugs table
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_EbZwCKXtS06W@ep-aged-tooth-al68e9hl-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

engine = create_engine(DATABASE_URL)

# drugs tablosunun yapısını kontrol et
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='drugs'
    """))
    columns = [row[0] for row in result]
    print('📊 drugs table columns:', columns)
    
    # Mevcut satır sayısı
    result = conn.execute(text('SELECT COUNT(*) FROM drugs'))
    count = result.scalar()
    print(f'📊 Current row count: {count}')

# Eğer tablo boşsa örnek veri ekle
if count == 0:
    # ✅ Doğru kolonlar: name, active_ingredient, indication, side_effects, source
    drugs = [
        ('Paracetamol', 'Paracetamol 500mg', 'Ağrı, ateş', 'Nadir: alerjik reaksiyon', 'WHO Essential Medicines'),
        ('Ibuprofen', 'Ibuprofen 400mg', 'Ağrı, enflamasyon', 'Mide rahatsızlığı, baş dönmesi', 'FDA Approved'),
        ('Amoxicillin', 'Amoxicillin 500mg', 'Bakteriyel enfeksiyonlar', 'İshal, bulantı, döküntü', 'WHO Essential Medicines'),
        ('Omeprazole', 'Omeprazole 20mg', 'Mide asidi, reflü', 'Baş ağrısı, karın ağrısı', 'FDA Approved'),
        ('Metformin', 'Metformin 500mg', 'Tip 2 diyabet', 'Mide bulantısı, ishal', 'FDA Approved'),
        ('Aspirin', 'Asetilsalisilik asit 100mg', 'Ağrı, kan sulandırıcı', 'Mide kanaması, alerji', 'WHO Essential Medicines'),
        ('Atorvastatin', 'Atorvastatin 20mg', 'Yüksek kolesterol', 'Kas ağrısı, baş ağrısı', 'FDA Approved'),
        ('Lisinopril', 'Lisinopril 10mg', 'Yüksek tansiyon', 'Öksürük, baş dönmesi', 'FDA Approved'),
        ('Metoprolol', 'Metoprolol 50mg', 'Hipertansiyon, anjina', 'Yorgunluk, bradikardi', 'FDA Approved'),
        ('Salbutamol', 'Salbutamol 100mcg', 'Astım, KOAH', 'Tremor, çarpıntı', 'WHO Essential Medicines'),
    ]
    
    with engine.connect() as conn:
        for name, active_ingredient, indication, side_effects, source in drugs:
            try:
                conn.execute(text("""
                    INSERT INTO drugs (name, active_ingredient, indication, side_effects, source)
                    VALUES (:name, :active_ingredient, :indication, :side_effects, :source)
                    ON CONFLICT DO NOTHING
                """), {
                    'name': name, 
                    'active_ingredient': active_ingredient, 
                    'indication': indication, 
                    'side_effects': side_effects,
                    'source': source
                })
            except Exception as e:
                print(f'⚠️ Error inserting {name}: {e}')
                conn.rollback()
        conn.commit()
        print('✅ Sample drugs added')
        
        # Kontrol et
        result = conn.execute(text('SELECT COUNT(*) FROM drugs'))
        print(f'📊 New row count: {result.scalar()}')
else:
    print('ℹ️ drugs table already has data, skipping insert')