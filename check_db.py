# check_db.py
from sqlalchemy import create_engine, text
import os

# Render'daki DATABASE_URL'inizi buraya yapıştırın (örnek format)
# DATABASE_URL = "postgresql://neondb_owner:password@ep-xxx.aws.neon.tech/neondb?sslmode=require"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_EbZwCKXtS06W@ep-aged-tooth-al68e9hl-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Toplam kayıt sayısı
    result = conn.execute(text("SELECT COUNT(*) FROM analyses"))
    count = result.scalar()
    print(f"📊 Veritabanındaki toplam analiz sayısı: {count}")
    
    # Son 3 kaydı getir
    print("\n📋 Son 3 Kayıt:")
    rows = conn.execute(text("SELECT filename, status, avg_confidence FROM analyses ORDER BY id DESC LIMIT 3"))
    for row in rows:
        print(f" - Dosya: {row[0]}, Durum: {row[1]}, Güven: {row[2]}")