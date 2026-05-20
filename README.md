# 🌱 Fidelik Sisleme Sulama Sistemi — Bulanık Mantık Kontrolcüsü

> **Bulanık Mantık Dersi Dönem Projesi**  
> Mamdani Çıkarım Motoru | Centroid Durulaştırma | Streamlit Arayüzü

---

## 📌 Proje Özeti

Bu proje, **fidelik sisleme sulama sistemleri** için bulanık mantık tabanlı akıllı bir karar destek sistemi sunar.
Sistem, gerçek zamanlı sensör verileri (toprak nemi, hava sıcaklığı, bağıl nem) alarak uygun sulama süresini (dakika) otomatik olarak belirler.

---

## 🎯 Giriş & Çıkış Değişkenleri

| Tür | Değişken | Aralık | Dilsel Tanımlar |
|-----|----------|--------|-----------------|
| Giriş | Toprak Nemi | 0 – 100 % | Kuru / Orta / Nemli |
| Giriş | Hava Sıcaklığı | 0 – 45 °C | Serin / Ilık / Sıcak / Çok Sıcak |
| Giriş | Bağıl Nem | 0 – 100 % | Düşük / Orta / Yüksek |
| Çıkış | Sulama Süresi | 0 – 30 dk | Yok / Az / Orta / Fazla / Çok Fazla |

---

## 🧠 Sistem Tasarımı

### Üyelik Fonksiyonları
- **Toprak Nemi:** Trapez (Kuru, Nemli) + Üçgen (Orta)
- **Hava Sıcaklığı:** Trapez (Serin, Çok Sıcak) + Üçgen (Ilık, Sıcak)
- **Bağıl Nem:** Trapez (Düşük, Yüksek) + Üçgen (Orta)
- **Sulama Süresi:** Trapez (Yok, Çok Fazla) + Üçgen (Az, Orta, Fazla)

### Çıkarım Motoru
- **Yöntem:** Mamdani
- **AND Operatörü:** Minimum (min)
- **Birleştirme:** Maksimum (max)
- **Kural Sayısı:** 36 IF-THEN kuralı

### Durulaştırma
- **Yöntem:** Ağırlık Merkezi (Centroid / COG)
- **Formül:** `crisp = Σ(x · μ(x)) / Σ(μ(x))`

---

## 🖥️ Kurulum ve Çalıştırma

```bash
# 1. Repo'yu klonla
git clone https://github.com/KULLANICI_ADINIZ/fuzzy-irrigation.git
cd fuzzy-irrigation

# 2. Sanal ortam oluştur (isteğe bağlı ama önerilir)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Uygulamayı başlat
streamlit run app.py
```

Tarayıcınızda `http://localhost:8501` adresine gidin.

---

## 🗂️ Dosya Yapısı

```
fuzzy-irrigation/
├── app.py              # Ana Streamlit uygulaması
├── requirements.txt    # Python bağımlılıkları
└── README.md           # Bu dosya
```

---

## 📊 Test Senaryoları

| Senaryo | Toprak Nemi | Sıcaklık | Bağıl Nem | Beklenen Sulama |
|---------|-------------|----------|-----------|-----------------|
| Kurak yaz günü | 15 % | 38 °C | 20 % | ~27–30 dk |
| Normal bahar günü | 50 % | 25 °C | 55 % | ~7–10 dk |
| Serin & nemli sabah | 75 % | 12 °C | 80 % | ~0 dk |
| İlkbahar sabahı | 35 % | 18 °C | 60 % | ~4–6 dk |
| Kritik nem açığı | 10 % | 42 °C | 15 % | ~29–30 dk |

---

## ⚡ Arayüz Özellikleri

- 🎚️ Slider + manuel sayısal giriş (her değişken için)
- 📈 Tüm üyelik fonksiyonlarının grafiksel gösterimi
- 🔬 Bulanıklaştırma görselleştirmesi (anlık ateşleme)
- 📋 Aktif/pasif kural listesi
- 📊 Kural ateşleme güçleri (yatay bar grafik)
- 🎯 Durulaştırma grafiği (toplamlaşmış çıkış + centroid)
- 🔢 Sayısal sonuç + dilsel yorum

---

## 🔬 Teknik Detaylar

Proje, `scikit-fuzzy` yerine **sıfırdan implementasyon** (pure NumPy) kullanır.
Bu sayede üyelik fonksiyonları, çıkarım motoru ve durulaştırma algoritması
tamamen şeffaf ve özelleştirilebilirdir.

### Üyelik Fonksiyon Formülleri

**Üçgen (trimf):**
```
μ(x) = max(0, min((x-a)/(b-a), (c-x)/(c-b)))
```

**Trapez (trapmf):**
```
μ(x) = max(0, min((x-a)/(b-a), 1, (d-x)/(d-c)))
```

**Centroid:**
```
x* = Σ(xᵢ · μ(xᵢ)) / Σ(μ(xᵢ))
```

---

## 📚 Kaynaklar

1. Zadeh, L.A. (1965). *Fuzzy Sets*. Information and Control, 8(3), 338–353.
2. Mamdani, E.H. (1974). *Application of fuzzy algorithms for control of simple dynamic plant*. Proc. IEE, 121(12), 1585–1588.
3. Ross, T.J. (2010). *Fuzzy Logic with Engineering Applications* (3rd ed.). Wiley.
4. Scikit-fuzzy Documentation: https://pythonhosted.org/scikit-fuzzy/
5. Streamlit Documentation: https://docs.streamlit.io

---

## 👤 Yazar

**[Adınız Soyadınız]**  
Bulanık Mantık Dersi — Dönem Projesi  
Deadline: 21.05.2026
