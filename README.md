# HantaMed Assist
Hantavirüs hastaları için ilaç/tedavi bilgilendirme, reçete/rapor analizi ve semptom destek sistemi.

⚠️ **YASAL UYARI:** Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın.

## Özellikler
- 🔒 KVKK/GDPR uyumlu, Privacy-by-Design
- 🤖 Florence-2 OCR+NES+QA pipeline (CPU optimized)
- 🛡️ Güvenilirlik kapısı: Confidence <0.7 otomatik reddedilir
- 📊 Sentetik veri ile eğitim ve metrik takibi
- 📱 Mobil öncelikli, erişilebilir UI
- ☁️ Render Free Tier uyumlu deployment

## Kurulum
```bash
bash scripts/setup.sh
bash scripts/run.sh