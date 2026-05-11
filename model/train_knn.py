import pandas as pd
import pickle
import sys
import os

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors

# Tambahkan folder induk (root proyek) ke sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.parser import (
    extract_ram,
    extract_processor,
    extract_gpu
)

# =========================
# LOAD DATASET
# =========================

df = pd.read_csv('dataset/final_dataset.csv')

# Rapikan nama kolom
df.columns = df.columns.str.lower()

print("Kolom dataset:")
print(df.columns)

# =========================
# PARSING SPESIFIKASI
# =========================

df['ram'] = df['product_name'].apply(extract_ram)
df['processor'] = df['product_name'].apply(extract_processor)
df['gpu'] = df['product_name'].apply(extract_gpu)

# =========================
# DEBUG: CEK HASIL PARSING GPU UNTUK PRODUK APPLE/MACBOOK
# =========================
print("\n🔍 DEBUG: Cek produk Apple/MacBook")
mask_apple = df['product_name'].str.contains('MacBook|Apple', case=False, na=False)
if mask_apple.any():
    print(df.loc[mask_apple, ['product_name', 'gpu']].head(5))
else:
    print("Tidak ada produk Apple/MacBook ditemukan dalam dataset.")

print("\n📊 Distribusi GPU (10 terbanyak):")
print(df['gpu'].value_counts().head(10))

# =========================
# CLEANING DATA
# =========================

# Bersihkan harga
df['price'] = (
    df['price']
    .astype(str)
    .str.replace('Rp', '')
    .str.replace('.', '')
    .str.replace(',', '')
)

df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['ram'] = pd.to_numeric(df['ram'], errors='coerce')

df = df.dropna(subset=['price', 'ram'])

df['price'] = df['price'].astype(int)
df['ram'] = df['ram'].astype(int)

# =========================
# ENCODE KATEGORI
# =========================

label_encoder = LabelEncoder()
df['kategori_encoded'] = label_encoder.fit_transform(df['kategori_kebutuhan'])

# =========================
# FEATURE & NORMALISASI
# =========================

X = df[['price', 'ram', 'kategori_encoded']]

# Normalisasi fitur (penting agar harga tidak mendominasi)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================
# TRAINING KNN
# =========================

knn = NearestNeighbors(n_neighbors=5, metric='euclidean')
knn.fit(X_scaled)

# =========================
# SAVE MODEL, ENCODER, SCALER
# =========================

with open('model/knn_model.pkl', 'wb') as file:
    pickle.dump(knn, file)

with open('model/label_encoder.pkl', 'wb') as file:
    pickle.dump(label_encoder, file)

with open('model/scaler.pkl', 'wb') as file:
    pickle.dump(scaler, file)

# =========================
# SAVE CLEAN DATASET
# =========================

output_path = 'dataset/cleaned_dataset.csv'

try:
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"File lama {output_path} berhasil dihapus.")
    df.to_csv(output_path, index=False)
    print(f'\n✅ Dataset cleaned berhasil disimpan di: {output_path}')
except PermissionError:
    print("\n❌ ERROR: File 'cleaned_dataset.csv' sedang digunakan (misal terbuka di Excel).")
    print("Tutup file tersebut, lalu jalankan ulang script.")
    sys.exit(1)

print('Jumlah data:', len(df))
print('\n✅ Model, encoder, dan scaler berhasil disimpan!')