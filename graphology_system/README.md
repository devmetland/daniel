# Graphology Analysis System

## 📋 Overview

Sistem analisis grafologi untuk mendukung proses interview HR. Menggunakan **Computer Vision** dan **Machine Learning (XGBoost)** untuk mengekstrak fitur tulisan tangan dan memprediksi karakteristik psikologis.

### ⚠️ PENTING - ETIKA PENGGUNAAN

Sistem ini dirancang untuk:
- ✅ **Internal use only**
- ✅ **Supporting insight** (BUKAN decision maker)
- ✅ **Eksplorasi berbasis data nyata perusahaan**
- ✅ **Secara etis & defensible**

**JANGAN gunakan untuk:**
- ❌ Keputusan hiring/firing otomatis
- ❌ Satu-satunya kriteria seleksi
- ❌ Diskriminasi berdasarkan hasil

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────┐
│              Graphology Analysis System              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐    ┌──────────────┐               │
│  │   Upload     │───▶│   Computer   │               │
│  │   Image      │    │   Vision     │               │
│  └──────────────┘    └──────────────┘               │
│                          │                           │
│                          ▼                           │
│                    ┌──────────────┐                 │
│                    │   Features   │                 │
│                    │   (8 items)  │                 │
│                    └──────────────┘                 │
│                          │                           │
│                          ▼                           │
│                    ┌──────────────┐                 │
│                    │   XGBoost    │                 │
│                    │   Model      │                 │
│                    └──────────────┘                 │
│                          │                           │
│                          ▼                           │
│                    ┌──────────────┐                 │
│                    │  Predictions │                 │
│                    │  (4 scores)  │                 │
│                    └──────────────┘                 │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Fitur yang Diekstrak

### Computer Vision Features (8):
1. **stroke_width_mean** - Rata-rata ketebalan goresan
2. **stroke_width_std** - Variasi ketebalan goresan
3. **vertical_projection_variance** - Variansi profil vertikal
4. **center_of_mass_x** - Pusat massa koordinat X
5. **center_of_mass_y** - Pusat massa koordinat Y
6. **contour_area_mean** - Rata-rata area kontur
7. **contour_area_std** - Variasi area kontur
8. **convexity_defects_score** - Skor defect convexity

### ML Predictions (4):
1. **leadership_score** - Potensi kepemimpinan (0-100)
2. **emotional_stability_score** - Stabilitas emosional (0-100)
3. **confidence_score** - Tingkat kepercayaan diri (0-100)
4. **discipline_score** - Tingkat kedisiplinan (0-100)

---

## 🚀 Instalasi

### Prasyarat
- Python 3.13.7
- pip

### Langkah Instalasi

```bash
# 1. Masuk ke direktori project
cd graphology_system

# 2. Buat virtual environment (opsional tapi disarankan)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Dependencies Utama:
- `opencv-python` - Computer vision
- `xgboost` - Machine learning model
- `fastapi` - REST API
- `uvicorn` - ASGI server
- `scikit-learn` - Preprocessing
- `numpy`, `pandas` - Data processing
- `pillow` - Image handling

---

## 📖 Cara Penggunaan

### 1. Menjalankan FastAPI Server

```bash
# Dari root directory graphology_system
python main.py
```

Server akan berjalan di: `http://localhost:8000`

Dokumentasi API tersedia di:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. Upload Gambar untuk Analisis

**Via API (Basic - Scores Only):**
```bash
curl -X POST "http://localhost:8000/analyze/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_handwriting.jpg"
```

**Via API (With Detailed Interpretation - RECOMMENDED):**
```bash
curl -X POST "http://localhost:8000/analyze/upload-with-interpretation?candidate_id=CAND-2025-001" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_handwriting.jpg"
```

Endpoint ini memberikan:
- ✅ Skor numerik (0-100) untuk setiap trait
- ✅ Deskripsi detail dalam bahasa Indonesia untuk setiap trait
- ✅ Kategori level (LOW/MODERATE/HIGH)
- ✅ Kekuatan potensial
- ✅ Area pengembangan
- ✅ Saran pertanyaan interview
- ✅ Ringkasan profil lengkap
- ✅ Laporan teks terformat siap cetak
- ✅ Panduan penggunaan etis

**Via Directory:**
1. Copy gambar ke folder `uploads/`
2. Akses endpoint: `http://localhost:8000/analyze/directory`

### 3. Menjalankan Directory Watcher (Auto-processing)

```bash
python -m src.directory_watcher ./uploads 10
```

Script akan memonitor folder `uploads/` setiap 10 detik dan otomatis memproses gambar baru.

### 4. Training Model dengan Data Sendiri

```python
from src.ml_predictor import GraphologyPredictor
import pandas as pd

# Load data perusahaan Anda (harus dikumpulkan secara etis!)
training_data = pd.read_csv('company_handwriting_data.csv')

# Inisialisasi predictor
predictor = GraphologyPredictor('./models')

# Train dengan data Anda
predictor.train(training_data=training_data, verbose=True)
```

---

## 📁 Struktur Folder

```
graphology_system/
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── README.md               # Dokumentasi
├── src/
│   ├── __init__.py
│   ├── feature_extractor.py    # Computer vision module
│   ├── ml_predictor.py         # XGBoost model
│   └── directory_watcher.py    # Auto-processing
├── uploads/                # Folder upload gambar
├── predictions/            # Hasil analisis (JSON)
└── models/                 # Model ML tersimpan
```

---

## 🔬 Workflow Detail

### 1. Image Preprocessing
```
Input Image → Grayscale → Gaussian Blur → 
Adaptive Threshold → Morphological Operations → Binary Image
```

### 2. Feature Extraction
```
Binary Image → Contour Detection → 
Calculate 8 Features → Feature Vector
```

### 3. Prediction
```
Feature Vector → StandardScaler → 
XGBoost Models (4x) → Psychological Scores
```

---

## 🛡️ Pertimbangan Etis

### Do's ✅
- Gunakan sebagai insight pendukung saja
- Kombinasikan dengan structured interview
- Pastikan informed consent dari kandidat
- Libatkan profesional terlatih untuk interpretasi
- Patuhi regulasi ketenagakerjaan lokal
- Jaga privasi dan keamanan data
- Dokumentasikan penggunaan dan keputusan

### Don'ts ❌
- Jangan gunakan sebagai satu-satunya kriteria
- Jangan buat keputusan hiring/firing otomatis
- Jangan diskriminasi berdasarkan hasil
- Jangan bagikan hasil tanpa consent
- Jangan gunakan di luar tujuan yang ditentukan
- Jangan abaikan faktor budaya dan kontekstual

---

## 📊 Contoh Response API

```json
{
  "filename": "20240115_103045_sample.jpg",
  "features": {
    "stroke_width_mean": 3.82,
    "stroke_width_std": 0.65,
    "vertical_projection_variance": 0.15,
    "center_of_mass_x": 0.52,
    "center_of_mass_y": 0.48,
    "contour_area_mean": 85.3,
    "contour_area_std": 42.1,
    "convexity_defects_score": 0.35
  },
  "predictions": {
    "leadership_score": 72.5,
    "emotional_stability_score": 68.3,
    "confidence_score": 75.1,
    "discipline_score": 71.8
  },
  "timestamp": "2024-01-15T10:30:45.123456",
  "disclaimer": "⚠️ FOR INSIGHT ONLY - Not for automated decision making"
}
```

---

## 🔧 Customization

### Mengubah Parameter Model

Edit file `src/ml_predictor.py`:

```python
model = xgb.XGBRegressor(
    n_estimators=100,      # Jumlah trees
    max_depth=4,           # Kedalaman tree
    learning_rate=0.1,     # Learning rate
    subsample=0.8,         # Subsample ratio
    colsample_bytree=0.8,  # Feature sampling
    random_state=42
)
```

### Menambah Fitur Baru

Edit file `src/feature_extractor.py`:

```python
def extract_new_feature(self) -> float:
    """Extract your custom feature"""
    # Your implementation here
    return feature_value
```

---

## 🧪 Testing

### Test Feature Extraction
```bash
python -m src.feature_extractor ./uploads
```

### Test ML Predictor
```bash
python -m src.ml_predictor
```

---

## 📝 License & Compliance

Sistem ini harus digunakan sesuai dengan:
- GDPR (General Data Protection Regulation)
- EEOC (Equal Employment Opportunity Commission)
- Regulasi ketenagakerjaan lokal
- Kebijakan privasi perusahaan

---

## 👥 Support

Untuk pertanyaan atau masalah:
1. Cek dokumentasi API di `/docs`
2. Review ethical guidelines di `/ethical-guidelines`
3. Pastikan compliance dengan tim legal

---

## ⚠️ DISCLAIMER

**Sistem ini adalah tool pendukung insight untuk HR interview.**
**BUKAN alat pengambilan keputusan otomatis.**

Selalu kombinasikan dengan:
- Structured interviews
- Professional judgment
- Assessment lainnya
- Pertimbangan kontekstual

Pastikan penggunaan yang etis dan bertanggung jawab.
